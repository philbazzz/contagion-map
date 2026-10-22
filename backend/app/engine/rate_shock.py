"""Interest-rate shock engine (ecosystem exposure map).

Primary question: if a chosen market rate moves by N basis points, which companies
in the network have measurable direct exposure, which have only a qualitative
transmission pathway, and which lack enough data to estimate an impact?

Rules (no invented coefficients):
  * SOFR shock → only floating instruments whose base_rate is SOFR, with disclosed
    principal: Δ annual interest (USD M) = principal_usd_m × shock_bp / 10_000
  * Floors: when SOFR + shock would sit below a disclosed floor, sensitivity is clipped
  * UST 2Y / 10Y shocks do NOT auto-apply to SOFR floating debt
  * Fixed-rate debt does not incur higher interest before refinancing; maturity
    refinancing is shown as a qualitative channel only
  * Connected companies are never counted as financially affected solely because an
    edge exists — they appear as potential_indirect or transmission channels
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .relations import relationship_summary
from .secondary_contagion import compute_secondary_stress, secondary_node_status
from .stress_model import compute_origin_stress, stress_status

ORIGIN = "coreweave"

BENCHMARKS = {
    "sofr": {
        "id": "sofr",
        "label": "SOFR (단기 기준금리)",
        "label_en": "SOFR",
        "plain": "변동금리 차입금이 대부분 따르는 단기 기준금리",
        "applies_to": "sofr_floating",
    },
    "ust_2y": {
        "id": "ust_2y",
        "label": "미국 2년물 국채 금리",
        "label_en": "US 2Y Treasury",
        "plain": "단기·중기 시장금리의 벤치마크. SOFR 연동 차입과 자동으로 같지 않음",
        "applies_to": "treasury",
    },
    "ust_10y": {
        "id": "ust_10y",
        "label": "미국 10년물 국채 금리",
        "label_en": "US 10Y Treasury",
        "plain": "장기 시장금리의 벤치마크. 고정금리 채권 재발행 환경에 참고",
        "applies_to": "treasury",
    },
}

STAGES = ["Direct Rate Stress", "Transmission Channels", "Secondary Contagion", "Ecosystem Summary"]
STAGES_KO = ["직접 금리 스트레스", "전달 채널", "2차 전염", "생태계 종합"]


class ShockError(ValueError):
    pass


def _r(x: Optional[float], nd: int = 4) -> Optional[float]:
    if x is None:
        return None
    k = 10 ** nd
    return math.floor(float(x) * k + 0.5) / k


def _g(x: float) -> str:
    s = f"{_r(x, 6):.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _m(x: float) -> str:
    a = abs(x)
    sign = "−" if x < 0 else ("+" if x > 0 else "")
    if a >= 1000:
        body = f"${a / 1000:.2f}B"
    elif a >= 10:
        body = f"${a:,.0f}M"
    else:
        body = f"${a:.1f}M"
    return sign + body


def _u(x: float) -> str:
    return _m(abs(x)).lstrip("+−")


def _edge_to(net: dict, a: str, b: str, prefer: Optional[str] = None) -> Optional[str]:
    c = [e for e in net["edges"] if e["source"] == a and e["target"] == b]
    if prefer:
        for e in c:
            if e["impact_channel"] == prefer:
                return e["id"]
    return c[0]["id"] if c else None


def _floating_sensitivity_usd_m(principal: float, shock_bp: float, sofr: float, floor: Optional[float]) -> Dict[str, Any]:
    """Annual interest change on SOFR-linked principal, respecting an optional floor."""
    if floor is None:
        eff_bp = shock_bp
        note = f"원금 {_u(principal)} × {shock_bp:+.0f}bp / 10,000"
        formula = "principal_usd_m × shock_bp / 10_000"
    else:
        base = max(sofr, floor)
        shocked = max(sofr + shock_bp / 100.0, floor)
        eff_pct = shocked - base
        eff_bp = eff_pct * 100.0
        note = (
            f"SOFR {_g(sofr)}% (하한 {_g(floor)}%) → 충격 후 {_g(shocked)}% · "
            f"유효 {_g(eff_bp)}bp × 원금 {_u(principal)}"
        )
        formula = "max(SOFR+shock, floor) − max(SOFR, floor), then × principal"
    delta = _r(principal * eff_bp / 10_000.0)
    return {
        "annual_interest_delta_usd_m": delta,
        "effective_shock_bp": _r(eff_bp, 2),
        "formula": formula,
        "note": note,
        "status": "computed",
    }


def simulate_rate_shock(
    net: dict,
    shock_bp: float,
    benchmark: str = "sofr",
    sofr_pct: Optional[float] = None,
) -> dict:
    if benchmark not in BENCHMARKS:
        raise ShockError(f"알 수 없는 벤치마크: {benchmark}")
    if not (-700 <= shock_bp <= 700):
        raise ShockError("금리 충격은 −700bp ~ +700bp 범위")

    fin = net["financials"]
    sofr = fin["market_inputs"]["sofr_pct"] if sofr_pct is None else sofr_pct
    if not (0 <= sofr <= 20):
        raise ShockError("SOFR는 0~20%")

    bm = BENCHMARKS[benchmark]
    applies = bm["applies_to"]
    warnings: List[str] = []
    instrument_rows: List[dict] = []

    floating_total = 0.0
    floating_known = 0.0
    floating_unknown = 0
    fixed_known = 0.0
    computed_delta = 0.0
    has_computed = False

    for inst in fin["instruments"]:
        principal = inst.get("principal_usd_m")
        row: Dict[str, Any] = {
            "id": inst["id"],
            "name": inst["name"],
            "kind": inst["kind"],
            "rate_type": inst["rate_type"],
            "base_rate": inst.get("base_rate"),
            "principal_usd_m": principal,
            "maturity": inst.get("maturity"),
            "channel": None,
            "exposure_class": "not_applicable",
            "annual_interest_delta_usd_m": None,
            "reason": "",
            "formula": None,
            "evidence_status": inst.get("rate_status") or "UNKNOWN",
        }

        if inst["rate_type"] == "floating" and (inst.get("base_rate") or "").upper() == "SOFR":
            if principal and principal > 0:
                floating_known += principal
            elif principal is None:
                floating_unknown += 1
            else:
                pass  # zero drawn (e.g. undrawn revolver)

            if applies == "sofr_floating":
                if principal is None:
                    row.update({
                        "channel": "floating_rate_interest",
                        "exposure_class": "insufficient_data",
                        "reason": "SOFR 연동 변동금리이나 잔액이 공시되지 않아 이자 민감도를 계산할 수 없음",
                    })
                elif principal <= 0:
                    row.update({
                        "channel": "floating_rate_interest",
                        "exposure_class": "not_applicable",
                        "reason": "약정은 있으나 인출 잔액 0 — 이자 민감도 없음",
                    })
                else:
                    sens = _floating_sensitivity_usd_m(principal, shock_bp, sofr, inst.get("floor_pct"))
                    row.update({
                        "channel": "floating_rate_interest",
                        "exposure_class": "direct_computed",
                        "annual_interest_delta_usd_m": sens["annual_interest_delta_usd_m"],
                        "reason": sens["note"],
                        "formula": sens["formula"],
                        "effective_shock_bp": sens["effective_shock_bp"],
                    })
                    computed_delta += sens["annual_interest_delta_usd_m"] or 0.0
                    has_computed = True
            else:
                row.update({
                    "channel": "floating_rate_interest",
                    "exposure_class": "benchmark_mismatch",
                    "reason": (
                        f"이 차입금은 SOFR에 연동됩니다. 선택한 벤치마크({bm['label']})와 자동으로 같지 않아 "
                        "이자비용을 계산하지 않습니다."
                    ),
                })
                warnings.append(
                    f"{inst['name']}: SOFR 연동 — {bm['label']} 충격은 자동 적용하지 않음"
                )

        elif inst["rate_type"] == "fixed":
            if principal and principal > 0:
                fixed_known += principal
            if applies == "treasury":
                row.update({
                    "channel": "fixed_rate_refinancing",
                    "exposure_class": "qualitative_refi",
                    "reason": (
                        f"고정금리 {inst.get('coupon_pct')}% · 만기 {inst.get('maturity') or '미공시'}. "
                        "만기 전 이자비용은 변하지 않음. 만기 재발행 시 시장금리가 반영될 수 있으나 "
                        "재발행 금리·잔액 가정이 없어 금액을 만들지 않음."
                    ),
                })
            else:
                row.update({
                    "channel": "fixed_rate_refinancing",
                    "exposure_class": "not_applicable",
                    "reason": "고정금리 — SOFR 충격이 만기 전 이자비용에 직접 적용되지 않음",
                })

        elif inst["rate_type"] == "unknown":
            row.update({
                "channel": "unknown_rate",
                "exposure_class": "insufficient_data",
                "reason": "금리 유형(고정/변동)이 공시되지 않아 민감도를 계산할 수 없음",
            })
        else:
            row["reason"] = "이 시나리오와 직접 관련 없음"

        if inst["rate_type"] == "floating":
            floating_total += principal or 0.0
        instrument_rows.append(row)

    # ---- entity assessments ----
    assessments: Dict[str, dict] = {}
    lender_ids = set()
    for inst in fin["instruments"]:
        for p in inst.get("participants") or []:
            lender_ids.add(p["entity"])

    supply_indirect = {"nvidia", "dell", "sk_hynix", "tsmc", "samsung"}
    customer_ids = {e["target"] for e in net["edges"] if e["impact_channel"] == "customer" and e["source"] == ORIGIN}
    facility_ids = {e["target"] for e in net["edges"] if e["impact_channel"] == "facility"}

    origin_values = []
    if has_computed and applies == "sofr_floating":
        origin_values.append({
            "label": "추가 연간 이자비용 (SOFR 연동·잔액 공시분)",
            "usd_m": _r(computed_delta),
            "status": "computed",
            "round": 0,
        })

    for n in net["nodes"]:
        nid = n["id"]
        rel = relationship_summary(net, ORIGIN, nid)

        if nid == ORIGIN:
            if applies == "sofr_floating" and has_computed:
                assessments[nid] = {
                    "category": "computed",
                    "exposure_class": "direct_computed",
                    "relation": rel,
                    "values": origin_values,
                    "reason": (
                        f"SOFR 연동 변동금리 잔액(공시분) {_u(floating_known)}에 "
                        f"{shock_bp:+.0f}bp를 적용. 공식: 원금 × bp / 10,000. "
                        f"고정금리·미공시 잔액은 제외."
                    ),
                    "needed": None if floating_unknown == 0 else "잔액 미공시 변동금리 차입금의 인출 잔액",
                    "channels": ["floating_rate_interest"],
                }
            elif applies == "sofr_floating":
                assessments[nid] = {
                    "category": "relationship_only",
                    "exposure_class": "insufficient_data",
                    "relation": rel,
                    "values": [],
                    "reason": "SOFR 연동 차입금이 있으나 계산 가능한 잔액이 없음",
                    "needed": "변동금리 차입금 잔액",
                    "channels": ["floating_rate_interest"],
                }
            else:
                assessments[nid] = {
                    "category": "relationship_only",
                    "exposure_class": "qualitative_refi",
                    "relation": rel,
                    "values": [],
                    "reason": (
                        f"{bm['label']} 충격은 CoreWeave의 SOFR 연동 이자에 자동 적용하지 않습니다. "
                        f"고정금리 공시 잔액 {_u(fixed_known)}은 만기 재발행 시에만 시장금리가 반영될 수 있으며, "
                        "재발행 가정을 넣지 않아 금액을 만들지 않습니다."
                    ),
                    "needed": "만기별 재발행 금리·금액 가정 (사용자 입력 시 별도 차환 도구 사용)",
                    "channels": ["fixed_rate_refinancing"],
                }
            continue

        if rel["kind"] == "unconfirmed":
            assessments[nid] = {
                "category": "unconfirmed",
                "exposure_class": "no_identified_exposure",
                "relation": rel,
                "values": [],
                "reason": "공개자료에서 확인된 관계 경로 없음",
                "needed": "관계를 입증할 공시·계약 자료",
                "channels": [],
            }
            continue

        if nid in lender_ids:
            assessments[nid] = {
                "category": "relationship_only",
                "exposure_class": "transmission_channel",
                "relation": rel,
                "values": [],
                "reason": (
                    "대주·주선 기관. 금리 상승은 대주에게 자동 손실이 아니라 이자수익·자산가치 변화일 수 있음. "
                    "기관별 보유액 미공시로 손익을 계산하지 않음."
                ),
                "needed": "기관별 대출 보유액·헤지·재매각 여부",
                "channels": ["lender_borrower"],
            }
            continue

        if nid in supply_indirect and applies == "sofr_floating" and has_computed and computed_delta > 0:
            assessments[nid] = {
                "category": "relationship_only",
                "exposure_class": "potential_indirect",
                "relation": rel,
                "values": [],
                "reason": (
                    "공급망 관계는 확인되나, 이자비용 증가 → CAPEX/구매 축소 규모는 "
                    "가정 없이는 계산하지 않음 (잠재 전달 경로)."
                ),
                "needed": {
                    "nvidia": "CoreWeave 연간 GPU 구매액",
                    "dell": "Dell 서버 구매액",
                    "sk_hynix": "NVIDIA HBM 매입 중 SK hynix 비중",
                    "tsmc": "NVIDIA 위탁생산 중 CoreWeave 관련 비중",
                    "samsung": "NVIDIA HBM 매입 중 Samsung 비중",
                }.get(nid),
                "channels": ["supplier_customer"],
            }
            continue

        if nid in customer_ids or nid in facility_ids:
            assessments[nid] = {
                "category": "relationship_only",
                "exposure_class": "potential_indirect",
                "relation": rel,
                "values": [],
                "reason": (
                    "고객·데이터센터 관계는 확인되나, 금리 충격이 계약 대금·임차료로 "
                    "전달된다는 공시가 없어 정량 영향을 만들지 않음."
                ),
                "needed": None,
                "channels": ["supplier_customer" if nid in customer_ids else "facility"],
            }
            continue

        # equity / other confirmed links
        assessments[nid] = {
            "category": "relationship_only",
            "exposure_class": "potential_indirect",
            "relation": rel,
            "values": [],
            "reason": "관계는 확인되나 이번 금리 충격과 정량 전달 경로·데이터가 없음",
            "needed": None,
            "channels": [],
        }

    origin_stress = None
    if applies == "sofr_floating":
        origin_stress = compute_origin_stress(
            fin, shock_bp, computed_delta if has_computed else None, floating_known, sofr, has_computed,
        )

    present_ids = {n["id"] for n in net["nodes"]}
    secondary_list = compute_secondary_stress(
        origin_stress["level"] if origin_stress else None, shock_bp, present_ids,
    )
    for sec in secondary_list:
        assessments[sec["entity_id"]] = {
            "category": "relationship_only",
            "exposure_class": "secondary_contagion",
            "relation": relationship_summary(net, ORIGIN, sec["entity_id"]),
            "values": [],
            "reason": sec["reason"],
            "needed": None,
            "channels": ["facility", "secondary_contagion"],
            "mechanism": "secondary_contagion",
        }

    # ---- summary (no double-counting) ----
    classes = {nid: a["exposure_class"] for nid, a in assessments.items()}
    direct_ids = {i for i, c in classes.items() if c == "direct_computed"}
    insuff_ids = {i for i, c in classes.items() if c in ("insufficient_data", "qualitative_refi", "benchmark_mismatch")}
    pot_ids = {i for i, c in classes.items() if c == "potential_indirect"}
    tx_ids = {i for i, c in classes.items() if c == "transmission_channel"}
    none_ids = {i for i, c in classes.items() if c == "no_identified_exposure"}

    high_n = (1 if origin_stress and origin_stress["level"] in ("high", "critical") else 0) + sum(
        1 for s in secondary_list if s["level"] in ("high", "critical")
    )
    crit_n = (1 if origin_stress and origin_stress["level"] == "critical" else 0) + sum(
        1 for s in secondary_list if s["level"] == "critical"
    )

    summary = {
        "network_companies": len(net["nodes"]),
        "direct_measurable": len(direct_ids),
        "potential_indirect": len(pot_ids),
        "transmission_channels": len(tx_ids),
        "insufficient_data": len(insuff_ids),
        "no_identified_exposure": len(none_ids),
        "total_incremental_interest_usd_m": _r(computed_delta) if has_computed else None,
        "floating_sofr_principal_usd_m": _r(floating_known),
        "fixed_principal_usd_m": _r(fixed_known),
        "shock_bp": shock_bp,
        "benchmark": benchmark,
        "stress_level": origin_stress["level"] if origin_stress else None,
        "companies_at_or_above_high": high_n,
        "companies_critical": crit_n,
        "secondary_stressed": len(secondary_list),
        "secondary_critical": sum(1 for s in secondary_list if s["level"] == "critical"),
        "baseline_sofr_pct": sofr,
        "stressed_sofr_pct": _r(sofr + shock_bp / 100.0, 4),
    }

    rounds = _build_rounds(
        net, bm, shock_bp, applies, has_computed, computed_delta, floating_known,
        assessments, instrument_rows, lender_ids, supply_indirect, origin_stress, secondary_list,
    )

    return {
        "mode": "RATE_SHOCK",
        "origin": ORIGIN,
        "benchmark": bm,
        "params": {
            "shock_bp": shock_bp,
            "benchmark": benchmark,
            "sofr_pct": sofr,
        },
        "summary": summary,
        "origin_stress": origin_stress,
        "secondary_stress": secondary_list,
        "instruments": instrument_rows,
        "rounds": rounds,
        "assessments": assessments,
        "formulas": [
            "SOFR 연동 변동금리 (잔액 공시): 연간 이자 변화(USD M) = principal_usd_m × shock_bp / 10_000",
            "하한(floor) 있는 경우: 유효 금리변화 = max(SOFR+shock, floor) − max(SOFR, floor)",
            "고정금리: 만기 전 이자비용 불변 — 금액 미산정",
            "국채 충격은 SOFR 연동 이자에 자동 가산하지 않음",
            "직접 스트레스 점수 = Δ연간이자 / 연환산 OCF (분석용 밴드; 약정·부도 예측 아님)",
            "2차 전염: CoreWeave 스트레스 밴드 × 공시된 임차·매출 집중도(sole / material / campus) — 확정 부도 아님",
        ],
        "warnings": warnings[:12],
        "notes": [
            "결과는 스트레스 시나리오이며 주가·부도·투자 예측이 아닙니다.",
            "직접 금리 민감도(A)와 CoreWeave 부실 시 임차·가동 2차 전염(B)을 분리해 모델링합니다.",
            "관계가 있다고 해서 재무 손실이 있다고 보지 않습니다.",
            "시장 관측값(국채·SOFR)과 시나리오 가정(충격 bp)을 구분합니다. 행성 균열은 분석용 스트레스 경고이며 부도 예측이 아닙니다.",
            f"SOFR 관측값 {_g(sofr)}% ({fin['market_inputs'].get('sofr_date', '')}) — 하한 계산에만 사용.",
        ],
        # shape compatibility with refinancing result consumers that expect .result / rounds
        "result": {
            "annual_interest_delta_usd_m": _r(computed_delta) if has_computed else 0.0,
            "shock_bp": shock_bp,
            "rate_change_bp": shock_bp,
            "new_rate_pct": None,
            "existing_rate_pct": None,
            "amount_usd_m": _r(floating_known),
            "refinanced_usd_m": None,
            "not_refinanced_usd_m": None,
            "annual_interest_existing_usd_m": None,
            "annual_interest_new_usd_m": None,
            "one_off_fee_usd_m": 0.0,
            "funding_need_usd_m": 0.0,
            "delta_6m_usd_m": _r(computed_delta / 2) if has_computed else None,
            "delta_6m_vs_ocf_6m_pct": None,
            "delta_6m_vs_interest_6m_pct": None,
        },
        "instrument": {
            "id": "ecosystem",
            "name": f"{bm['label_en']} {shock_bp:+.0f}bp",
            "kind": "term_loan",
            "principal_usd_m": _r(floating_known),
            "principal_as_of": fin.get("as_of"),
            "maturity": None,
            "rate_type": "floating" if applies == "sofr_floating" else "unknown",
            "coupon_pct": None,
            "spread_pct": None,
            "effective_rate_pct": None,
            "rate_status": "ASSUMED",
            "rate_note": "생태계 금리 충격 시나리오",
            "borrower": ORIGIN,
            "recourse": None,
            "source_ids": [fin.get("filing")] if fin.get("filing") else [],
        },
        "existing_rate": {
            "rate_pct": sofr if applies == "sofr_floating" else None,
            "basis": "market",
            "status": "VERIFIED" if applies == "sofr_floating" else "ASSUMED",
            "formula": f"충격 {shock_bp:+.0f}bp · {bm['label']}",
            "fallback": False,
        },
        "comparison": [],
        "schedule": [],
        "reference": {
            "ocf_6m_usd_m": next((m["value_usd_m"] for m in fin["metrics"] if m["id"] == "ocf_6m"), None),
            "contractual_interest_6m_usd_m": next((m["value_usd_m"] for m in fin["metrics"] if m["id"] == "contractual_interest_6m"), None),
            "cash_usd_m": next((m["value_usd_m"] for m in fin["metrics"] if m["id"] == "cash"), None),
            "capex_6m_usd_m": next((m["value_usd_m"] for m in fin["metrics"] if m["id"] == "capex_6m"), None),
            "as_of": fin.get("as_of"),
            "source_ids": [fin.get("filing")] if fin.get("filing") else [],
            "nvidia_revenue_fy2026_usd_m": fin.get("reference", {}).get("nvidia_revenue_fy2026_usd_m"),
            "nvidia_source_id": fin.get("reference", {}).get("nvidia_source_id"),
        },
        "assumption_chain": {
            "capex_absorption_pct": None,
            "capex_cut_usd_m": None,
            "gpu_share_pct": None,
            "gpu_purchase_cut_usd_m": None,
            "gpu_cut_vs_nvidia_revenue_pct": None,
        },
    }


def _build_rounds(
    net, bm, shock_bp, applies, has_computed, computed_delta, floating_known,
    assessments, instrument_rows, lender_ids, supply_indirect, origin_stress=None,
    secondary_list=None,
) -> List[dict]:
    states: Dict[str, dict] = {}
    rounds: List[dict] = []
    secondary_list = secondary_list or []
    level_ko = {
        "normal": "정상", "moderate": "중간 스트레스", "high": "높은 스트레스",
        "critical": "심각 재무 압박 — 시나리오 추정", "insufficient": "데이터 부족",
        "not_applicable": "해당 없음",
    }

    def snap(i: int, lines: List[str], active: List[str]) -> None:
        rounds.append({
            "round": i,
            "stage": i + 1,
            "title": f"STAGE {i + 1} · {STAGES[i]}",
            "title_ko": STAGES_KO[i],
            "lines": lines,
            "active_edges": active,
            "node_states": {k: dict(v) for k, v in states.items()},
        })

    # Stage 0 — direct
    if has_computed and applies == "sofr_floating" and origin_stress:
        lvl = origin_stress["level"]
        states[ORIGIN] = {
            "status": stress_status(lvl, True),
            "label": f"이자 {_m(computed_delta)}/년 · {level_ko.get(lvl, lvl)}",
            "category": "computed",
            "intensity": origin_stress.get("intensity"),
            "stress": lvl,
        }
        lines = [
            f"SOFR {_g(origin_stress['baseline_sofr_pct'])}% → {_g(origin_stress['stressed_sofr_pct'])}% ({shock_bp:+.0f}bp)",
            f"CoreWeave SOFR 연동 {_u(floating_known)} → 연간 이자 {_m(computed_delta)}",
            (
                f"커버리지 {_g(origin_stress.get('baseline_coverage') or 0)}x → {_g(origin_stress.get('stressed_coverage') or 0)}x"
                if origin_stress.get("stressed_coverage") is not None
                else "커버리지 산정 불가"
            ),
            (
                f"분석용 임계 SOFR ≈ {_g(origin_stress['critical_sofr_pct'])}% (+{_g(origin_stress.get('critical_shock_bp') or 0)}bp)"
                if origin_stress.get("critical_sofr_pct") is not None
                else "임계 금리: 공시만으로 산정 불가"
            ),
        ]
    elif applies == "sofr_floating":
        states[ORIGIN] = {
            "status": "insufficient", "label": "데이터 부족", "category": "relationship_only",
            "intensity": 0.35, "stress": "insufficient",
        }
        lines = [f"{bm['label']} {shock_bp:+.0f}bp · 계산 가능한 SOFR 잔액 없음"]
    else:
        states[ORIGIN] = {
            "status": "potential", "label": "정성 경로", "category": "relationship_only",
            "intensity": 0.4, "stress": "not_applicable",
        }
        lines = [
            f"{bm['label']} {shock_bp:+.0f}bp",
            assessments[ORIGIN]["reason"][:120],
        ]
    insuff_inst = [r["name"] for r in instrument_rows if r["exposure_class"] == "insufficient_data"]
    if insuff_inst:
        lines.append(f"잔액·금리 미공시 차입금 {len(insuff_inst)}건 — 금액 미산정")
    snap(0, lines, [])

    # Stage 1 — lenders / transmission
    fin_edges = []
    for lid in sorted(lender_ids):
        states[lid] = {"status": "contract_party", "label": "전달 채널 · 미산정", "category": "relationship_only"}
        e = _edge_to(net, ORIGIN, lid, "financial")
        if e:
            fin_edges.append(e)
    lines = [
        f"대주·주선 기관 {len(lender_ids)}곳 — 계약 관계는 확인, 보유액 미공시로 손익 미산정",
        "금리 상승 ≠ 대주 손실. 이자수익·자산가치 변화일 수 있음",
    ]
    snap(1, lines, fin_edges)

    # Stage 2 — secondary contagion (+ supply watch)
    sec_edges: List[str] = []
    for sec in secondary_list:
        states[sec["entity_id"]] = {
            "status": secondary_node_status(sec["level"]),
            "label": sec["label_ko"],
            "category": "relationship_only",
            "intensity": sec["intensity"],
            "stress": sec["level"],
        }
        e = _edge_to(net, ORIGIN, sec["entity_id"], "facility")
        if e:
            sec_edges.append(e)

    show_supply = applies == "sofr_floating" and has_computed and computed_delta > 0
    node_ids = {n["id"] for n in net["nodes"]}
    if show_supply:
        for sid in ("nvidia", "dell"):
            if sid in node_ids and sid not in states:
                states[sid] = {"status": "potential", "label": "잠재 경로 · 미산정", "category": "relationship_only"}
                e = _edge_to(net, ORIGIN, sid, "supply_chain")
                if e:
                    sec_edges.append(e)
        for sid in ("sk_hynix", "tsmc"):
            if sid in node_ids and sid not in states:
                states[sid] = {"status": "potential", "label": "잠재 경로 · 미산정", "category": "relationship_only"}
        for e in net["edges"]:
            if e["source"] == "nvidia" and e["target"] in ("sk_hynix", "tsmc"):
                sec_edges.append(e["id"])

    if secondary_list:
        names = []
        for s in secondary_list:
            nm = next((n["name"] for n in net["nodes"] if n["id"] == s["entity_id"]), s["entity_id"])
            names.append(f"{nm}→{s['label_en']}")
        lines = [
            f"CoreWeave {(origin_stress or {}).get('level', '—')} → 공시 집중도 기반 2차 전염 {len(secondary_list)}곳 (확정 부도 아님)",
            *names[:4],
            "메커니즘 B: 임차료·가동·계약현금흐름 — 직접 SOFR 이자(A)와 별도",
        ]
        if show_supply:
            lines.append("공급망(NVDA 등)은 구매 비중 가정 없이 잠재 경로만 표시")
        snap(2, lines, sec_edges)
    elif show_supply:
        snap(2, [
            "CoreWeave 스트레스가 2차 임계에 미달 — 임차 상대방 행성 스트레스 미적용",
            "공급망으로의 전달은 가능하나 CAPEX·구매 비중 가정 없이 금액을 만들지 않음",
        ], sec_edges)
    else:
        snap(2, ["이번 벤치마크·충격에서는 정량 직접 노출이 없어 2차 전염을 산정하지 않음"], [])

    # Stage 3 — summary
    cats: Dict[str, int] = {}
    for a in assessments.values():
        cats[a["exposure_class"]] = cats.get(a["exposure_class"], 0) + 1
    sec_crit = sum(1 for s in secondary_list if s["level"] == "critical")
    lines = [
        f"네트워크 {len(net['nodes'])}개사",
        (
            f"직접 측정 {cats.get('direct_computed', 0)} · 2차 전염 {cats.get('secondary_contagion', 0)} (심각 {sec_crit}) · "
            f"잠재 간접 {cats.get('potential_indirect', 0)} · 전달 채널 {cats.get('transmission_channel', 0)} · "
            f"데이터 부족/정성 {sum(cats.get(k, 0) for k in ('insufficient_data', 'qualitative_refi', 'benchmark_mismatch'))}"
        ),
        (
            f"합산 추가 연간 이자(계산분) {_m(computed_delta)}"
            if has_computed else "합산 추가 이자: 계산 가능한 항목 없음"
        ),
    ]
    if not secondary_list and origin_stress:
        lines.append("추가 모델 전파 없음 — 선택 시나리오에서 2차 임계 미충족")
    snap(3, lines, sorted(set(fin_edges + sec_edges)))
    return rounds
