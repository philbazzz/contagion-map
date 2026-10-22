"""Refinancing shock engine.

Only ONE number in this engine is derived purely from disclosed data plus the user's rate
input: the change in CoreWeave's interest cost on the instrument being refinanced.

    추가 연간 이자비용 = 차환 금액 × 차환 성공 비율 × (신규 금리 − 기존 비교금리)

Everything downstream is either
  * computed from the user's explicit assumptions (CAPEX 흡수율, GPU 비중) — type C, or
  * shown as a relationship-only path with no number — type D.
No coefficient is multiplied along a chain unless the user typed it in, and no entity is ever
marked as defaulted.

Stage plan (rounds 0..5 shown as STAGE 1..6):
  1 Refinancing Event   2 Funding Cost   3 Investment Capacity
  4 GPU Supply Chain    5 HBM Supply Chain   6 Network Impact
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

from .relations import relationship_summary

STAGES = ["Refinancing Event", "Funding Cost", "Investment Capacity", "GPU Supply Chain", "HBM Supply Chain", "Network Impact"]
STAGES_KO = ["차환 발생", "자금조달 비용", "투자여력", "GPU 공급망", "HBM 공급망", "네트워크 종합"]
COMPARE_RATES = [9.0, 12.0, 15.0]
ORIGIN = "coreweave"


class RefiError(ValueError):
    pass


# Rounding/formatting helpers are written so the TypeScript port (frontend/src/engine/refinancing.ts)
# produces byte-identical output: half-up rounding on the same IEEE operations, no locale formatting.
def _r(x: Optional[float], nd: int = 4) -> Optional[float]:
    if x is None:
        return None
    k = 10 ** nd
    return math.floor(float(x) * k + 0.5) / k


def _fix(x: float, nd: int) -> str:
    """Half-up fixed decimals of |x| (sign handled by caller)."""
    v = _r(abs(x), nd)
    return f"{v:.{nd}f}"


def _g(x: float) -> str:
    """Shortest plain form of a user/disclosed rate: 9.25 -> '9.25', 12.0 -> '12'."""
    v = _r(x, 6)
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _sign(x: float) -> str:
    return "−" if x < 0 else "+" if x > 0 else ""


def _group(s: str) -> str:
    whole, _, frac = s.partition(".")
    out = ""
    while len(whole) > 3:
        out = "," + whole[-3:] + out
        whole = whole[:-3]
    return whole + out + ("." + frac if frac else "")


def _m(x: float) -> str:
    """USD million -> compact label used in stage text ($840M / $1.90B)."""
    a = abs(x)
    s = f"${_fix(a / 1000, 2)}B" if a >= 1000 else f"${_group(_fix(a, 0))}M" if a >= 10 else f"${_fix(a, 1)}M"
    return _sign(x) + s


def _u(x: float) -> str:
    """Unsigned amount label."""
    return _m(abs(x)).lstrip("+−")


def _parse_ym(s: str) -> tuple:
    parts = s.split("-")
    y, mth = int(parts[0]), int(parts[1]) if len(parts) > 1 else 12
    if not (1 <= mth <= 12):
        raise RefiError(f"잘못된 날짜: {s}")
    return y, mth


def instrument_map(net: dict) -> Dict[str, dict]:
    return {x["id"]: x for x in net["financials"]["instruments"]}


def next_maturity_id(net: dict, today: Optional[str] = None) -> Optional[str]:
    """Earliest future final maturity among drawn instruments (the default refinancing target)."""
    t = today or net["meta"]["as_of"]
    cands = [x for x in net["financials"]["instruments"]
             if x.get("maturity") and (x.get("principal_usd_m") or 0) > 0 and x["maturity"] >= t[:7]]
    cands.sort(key=lambda x: x["maturity"])
    return cands[0]["id"] if cands else None


def existing_rate(inst: dict, basis: str, sofr_pct: float) -> dict:
    """The comparison rate for the existing debt, with how it was obtained."""
    if basis not in ("stated", "effective"):
        raise RefiError("basis는 stated 또는 effective")
    if basis == "stated":
        if inst["rate_type"] == "fixed" and inst.get("coupon_pct") is not None:
            return {"rate_pct": inst["coupon_pct"], "basis": "stated", "status": inst["rate_status"],
                    "formula": f"표면금리 {_g(inst['coupon_pct'])}% (고정)", "fallback": False}
        if inst["rate_type"] == "floating" and inst.get("spread_pct") is not None:
            base = sofr_pct if inst.get("floor_pct") is None else max(sofr_pct, inst["floor_pct"])
            st = "INFERRED" if inst["rate_status"] != "VERIFIED" else "VERIFIED"
            return {"rate_pct": _r(base + inst["spread_pct"]), "basis": "stated", "status": st,
                    "formula": f"SOFR {_g(base)}% + 가산금리 {_g(inst['spread_pct'])}%", "fallback": False}
    if inst.get("effective_rate_pct") is not None:
        return {"rate_pct": inst["effective_rate_pct"], "basis": "effective", "status": "VERIFIED",
                "formula": f"10-Q 유효이자율 {_g(inst['effective_rate_pct'])}% (반올림 공시값)",
                "fallback": basis == "stated"}
    raise RefiError(f"{inst['name']}: 기존 금리를 확인할 수 없어 계산할 수 없습니다 (표면금리·유효이자율 모두 미공시).")


def core(amount: float, success: float, ex_pct: float, new_pct: float, fee_pct: float, ref: dict) -> dict:
    refinanced = amount * success
    delta = refinanced * (new_pct - ex_pct) / 100.0
    out = {
        "new_rate_pct": new_pct,
        "existing_rate_pct": ex_pct,
        "rate_change_bp": _r((new_pct - ex_pct) * 100, 1),
        "amount_usd_m": _r(amount),
        "refinanced_usd_m": _r(refinanced),
        "not_refinanced_usd_m": _r(amount - refinanced),
        "annual_interest_existing_usd_m": _r(refinanced * ex_pct / 100.0),
        "annual_interest_new_usd_m": _r(refinanced * new_pct / 100.0),
        "annual_interest_delta_usd_m": _r(delta),
        "one_off_fee_usd_m": _r(refinanced * fee_pct / 100.0),
        "funding_need_usd_m": _r(amount - refinanced),
        "delta_6m_usd_m": _r(delta / 2.0),
        "delta_6m_vs_ocf_6m_pct": _r(delta / 2.0 / ref["ocf_6m"] * 100.0) if ref.get("ocf_6m") else None,
        "delta_6m_vs_interest_6m_pct": _r(delta / 2.0 / ref["contractual_interest_6m"] * 100.0) if ref.get("contractual_interest_6m") else None,
    }
    return out


def schedule(refinanced: float, ex_pct: float, new_pct: float, fee_pct: float, start: tuple, tenor: int) -> List[dict]:
    """Yearly interest/principal for the refinanced amount. New loan assumed bullet (user tenor);
    the base line keeps the existing rate for the same months so the two rows are comparable."""
    sy, sm = start
    end_index = sy * 12 + (sm - 1) + tenor * 12  # month index of new maturity (exclusive)
    rows = []
    for y in range(sy, sy + tenor + 1):
        first = max(y * 12, sy * 12 + sm - 1)
        last = min(y * 12 + 12, end_index)
        months = max(0, last - first)
        if months == 0 and y != sy + tenor:
            continue
        base = refinanced * ex_pct / 100.0 * months / 12.0
        new = refinanced * new_pct / 100.0 * months / 12.0
        principal = refinanced if (end_index - 1) // 12 == y else 0.0
        fee = refinanced * fee_pct / 100.0 if y == sy else 0.0
        if months == 0 and principal == 0:
            continue
        rows.append({"year": y, "months": months, "interest_existing_usd_m": _r(base), "interest_new_usd_m": _r(new),
                     "interest_delta_usd_m": _r(new - base), "fee_usd_m": _r(fee), "principal_usd_m": _r(principal),
                     "debt_service_new_usd_m": _r(new + fee + principal)})
    return rows


def _metric(net: dict, mid: str) -> Optional[float]:
    for m in net["financials"]["metrics"]:
        if m["id"] == mid:
            return m["value_usd_m"]
    return None


def simulate_refinancing(net: dict, instrument_id: str, new_rate_pct: float, amount_usd_m: Optional[float] = None,
                         basis: str = "stated", refi_date: Optional[str] = None, success_ratio: float = 1.0,
                         fee_pct: float = 0.0, new_tenor_years: int = 5, sofr_pct: Optional[float] = None,
                         capex_absorption_pct: Optional[float] = None, gpu_share_pct: Optional[float] = None,
                         compare_rates: Optional[List[float]] = None) -> dict:
    fin = net["financials"]
    insts = instrument_map(net)
    if instrument_id not in insts:
        raise RefiError(f"알 수 없는 차입금: {instrument_id}")
    inst = insts[instrument_id]
    if not (0 <= new_rate_pct <= 40):
        raise RefiError("신규 금리는 0~40% 범위")
    if not (0 <= success_ratio <= 1):
        raise RefiError("차환 성공 비율은 0~1")
    if not (0 <= fee_pct <= 10):
        raise RefiError("추가 조달비용은 0~10%")
    if not (1 <= int(new_tenor_years) <= 15):
        raise RefiError("신규 만기는 1~15년")
    for v, nm in ((capex_absorption_pct, "CAPEX 흡수율"), (gpu_share_pct, "GPU 비중")):
        if v is not None and not (0 <= v <= 100):
            raise RefiError(f"{nm}은 0~100%")
    sofr = fin["market_inputs"]["sofr_pct"] if sofr_pct is None else float(sofr_pct)
    if not (0 <= sofr <= 20):
        raise RefiError("SOFR는 0~20%")

    warnings: List[str] = []
    amount = amount_usd_m if amount_usd_m is not None else inst.get("principal_usd_m")
    if amount is None or amount <= 0:
        raise RefiError(f"{inst['name']}: 2026.6.30 기준 잔액이 공시되지 않았습니다. 차환 대상 금액을 직접 입력하세요.")
    if amount_usd_m is None and "분할상환" in (inst.get("amortization") or ""):
        warnings.append("분할상환 차입금이라 만기 시점 잔액은 2026.6.30 잔액보다 작습니다. 개별 상환 스케줄이 공시되지 않아 6.30 잔액을 기본값으로 썼습니다.")
    if amount_usd_m is not None and inst.get("principal_usd_m") and amount_usd_m > inst["principal_usd_m"]:
        warnings.append("입력 금액이 공시 잔액보다 큽니다.")

    ex = existing_rate(inst, basis, sofr)
    if ex["fallback"]:
        warnings.append(f"{inst['name']}의 표면금리가 공시되지 않아 10-Q 유효이자율로 비교했습니다.")
    if ex["status"] == "INFERRED" and inst.get("effective_rate_pct") is not None:
        warnings.append(f"기존 금리의 가산금리는 2차 출처 값(INFERRED)입니다. 공시 유효이자율 {_g(inst['effective_rate_pct'])}% 기준으로도 비교해 보세요.")
    if inst["kind"] == "convertible":
        warnings.append("전환사채는 낮은 표면금리 대신 전환권을 준 구조라 일반 차입금리와 단순 비교 시 차이가 크게 보입니다.")

    if refi_date is None:
        m = inst.get("maturity")
        refi_date = m[:7] if m and len(m) >= 7 else (f"{m}-01" if m else net["meta"]["as_of"][:7])
    start = _parse_ym(refi_date)

    ref = {"ocf_6m": _metric(net, "ocf_6m"), "contractual_interest_6m": _metric(net, "contractual_interest_6m"),
           "cash": _metric(net, "cash"), "capex_6m": _metric(net, "capex_6m")}
    main = core(amount, success_ratio, ex["rate_pct"], new_rate_pct, fee_pct, ref)
    sched = schedule(amount * success_ratio, ex["rate_pct"], new_rate_pct, fee_pct, start, int(new_tenor_years))
    rates = compare_rates if compare_rates is not None else COMPARE_RATES
    comparison = [dict(core(amount, success_ratio, ex["rate_pct"], r, fee_pct, ref), label=f"Scenario {chr(65 + i)}")
                  for i, r in enumerate(rates)]

    delta = main["annual_interest_delta_usd_m"]
    capex_cut = gpu_cut = None
    if capex_absorption_pct is not None and delta is not None and delta > 0:
        capex_cut = _r(delta * capex_absorption_pct / 100.0)
        if gpu_share_pct is not None:
            gpu_cut = _r(capex_cut * gpu_share_pct / 100.0)
    nv_rev = fin["reference"]["nvidia_revenue_fy2026_usd_m"]
    gpu_vs_nv = _r(gpu_cut / nv_rev * 100.0, 6) if gpu_cut is not None else None

    rounds = _rounds(net, inst, ex, main, new_rate_pct, capex_absorption_pct, gpu_share_pct, capex_cut, gpu_cut, gpu_vs_nv)
    assess = _assessments(net, inst, main, capex_cut, gpu_cut, gpu_vs_nv)

    return {
        "mode": "REFINANCING",
        "origin": ORIGIN,
        "instrument": {k: inst.get(k) for k in ("id", "name", "kind", "principal_usd_m", "principal_as_of", "maturity",
                                                  "rate_type", "coupon_pct", "spread_pct", "effective_rate_pct",
                                                  "rate_status", "rate_note", "borrower", "recourse", "source_ids")},
        "params": {"instrument_id": instrument_id, "new_rate_pct": new_rate_pct, "amount_usd_m": amount,
                   "basis": basis, "refi_date": refi_date, "success_ratio": success_ratio, "fee_pct": fee_pct,
                   "new_tenor_years": int(new_tenor_years), "sofr_pct": sofr,
                   "capex_absorption_pct": capex_absorption_pct, "gpu_share_pct": gpu_share_pct},
        "existing_rate": ex,
        "result": main,
        "schedule": sched,
        "comparison": comparison,
        "reference": {"ocf_6m_usd_m": ref["ocf_6m"], "contractual_interest_6m_usd_m": ref["contractual_interest_6m"],
                      "cash_usd_m": ref["cash"], "capex_6m_usd_m": ref["capex_6m"], "as_of": fin["as_of"],
                      "source_ids": [fin["filing"]], "nvidia_revenue_fy2026_usd_m": nv_rev,
                      "nvidia_source_id": fin["reference"]["nvidia_source_id"]},
        "assumption_chain": {"capex_absorption_pct": capex_absorption_pct, "capex_cut_usd_m": capex_cut,
                             "gpu_share_pct": gpu_share_pct, "gpu_purchase_cut_usd_m": gpu_cut,
                             "gpu_cut_vs_nvidia_revenue_pct": gpu_vs_nv},
        "rounds": rounds,
        "assessments": assess,
        "warnings": warnings,
        "notes": [
            "추가 이자비용은 차환 대상 차입금 하나에만 적용했습니다. 다른 차입금의 금리는 바뀌지 않습니다.",
            "비교 기준선은 '같은 기간 기존 금리 유지'입니다. 실제 기존 차입금은 만기에 상환되므로, 기준선은 비교용입니다.",
            "상반기 비교는 연간 추가 이자의 1/2을 같은 6개월 실적과 비교한 값입니다(기간 기준 일치).",
            "금리 상승이 곧 부도나 투자 축소를 뜻하지 않습니다. 투자 축소 이후 단계는 사용자 가정이 있을 때만 숫자로 표시합니다.",
        ],
    }


def _participants(inst: dict) -> List[dict]:
    return inst.get("participants") or []


def _edge_to(net: dict, a: str, b: str, prefer: Optional[str] = None) -> Optional[str]:
    cands = [e for e in net["edges"] if e["source"] == a and e["target"] == b]
    if prefer:
        for e in cands:
            if e["impact_channel"] == prefer:
                return e["id"]
    return cands[0]["id"] if cands else None


def _rounds(net, inst, ex, main, new_pct, absorb, gpu_share, capex_cut, gpu_cut, gpu_vs_nv) -> List[dict]:
    delta = main["annual_interest_delta_usd_m"]
    parts = _participants(inst)
    part_ids = [p["entity"] for p in parts]
    fin_edges = [eid for eid in (_edge_to(net, ORIGIN, pid, "financial") for pid in part_ids) if eid]
    states: Dict[str, dict] = {}
    rounds = []

    def snap(i, lines, active):
        rounds.append({"round": i, "stage": i + 1, "title": f"STAGE {i + 1} · {STAGES[i]}", "title_ko": STAGES_KO[i],
                       "lines": lines, "active_edges": active, "node_states": {k: dict(v) for k, v in states.items()}})

    # 1 Refinancing event
    states[ORIGIN] = {"status": "shock_origin", "label": f"{inst['name']} → {_g(new_pct)}%", "category": "computed"}
    for pid in part_ids:
        states[pid] = {"status": "contract_party", "label": "계약 참여 · 영향 미산정", "category": "relationship_only"}
    lines = [f"CoreWeave가 {inst['name']} {_u(main['amount_usd_m'])}을(를) {_g(new_pct)}%로 차환한다고 가정 (기존 비교금리 {_g(ex['rate_pct'])}%, {ex['formula']})"]
    if parts:
        lines.append(f"계약 참여 기관 {len(parts)}곳 표시 — 기관별 보유액 미공시로 영향 미산정")
    else:
        lines.append("공시된 계약 참여 기관 없음")
    snap(0, lines, fin_edges)

    # 2 Funding cost (computed)
    states[ORIGIN] = {"status": "shock_origin", "label": f"이자 {_m(delta)}/년", "category": "computed"}
    lines = [f"연간 이자비용 {_u(main['annual_interest_existing_usd_m'])} → {_u(main['annual_interest_new_usd_m'])} (차이 {_m(delta)}/년, {_sign(main['rate_change_bp'])}{_g(abs(main['rate_change_bp']))}bp)"]
    if main["delta_6m_vs_ocf_6m_pct"] is not None:
        lines.append(f"6개월 환산 {_m(main['delta_6m_usd_m'])} = 2026 상반기 영업현금흐름의 {_sign(main['delta_6m_vs_ocf_6m_pct'])}{_fix(main['delta_6m_vs_ocf_6m_pct'], 2)}%")
    if main["funding_need_usd_m"]:
        lines.append(f"차환되지 않은 {_u(main['funding_need_usd_m'])}은 자체 자금으로 상환 필요 (자금조달 필요액)")
    snap(1, lines, [])

    # 3 Investment capacity
    if delta is not None and delta <= 0:
        lines = ["이자 부담이 늘지 않아 투자여력 감소 경로가 생기지 않습니다."]
    elif capex_cut is not None:
        states[ORIGIN] = {"status": "shock_origin", "label": f"CAPEX {_m(-capex_cut)}/년 (가정)", "category": "assumed"}
        lines = [f"사용자 가정: 추가 이자의 {_g(absorb)}%를 CAPEX 축소로 흡수 → CAPEX {_m(-capex_cut)}/년"]
    else:
        lines = ["투자여력이 줄어들 수 있으나, 축소 규모는 가정 없이는 계산하지 않습니다 (CAPEX 흡수율 미입력)."]
    snap(2, lines, [])

    # 4 GPU supply chain
    propagate = delta is not None and delta > 0
    gpu_edges = [x for x in (_edge_to(net, ORIGIN, "nvidia", "supply_chain"), _edge_to(net, ORIGIN, "dell", "supply_chain")) if x] if propagate else []
    if propagate:
        if gpu_cut is not None:
            states["nvidia"] = {"status": "assumed", "label": f"GPU 구매 {_m(-gpu_cut)} (가정)", "category": "assumed"}
            lines = [f"사용자 가정: CAPEX 축소분의 {_g(gpu_share)}%가 GPU 구매 → GPU 구매 {_m(-gpu_cut)}/년",
                     f"NVIDIA FY2026 매출 대비 {_fix(gpu_vs_nv, 4)}% (가정 기반 비율, 매출 감소 예측 아님)"]
        else:
            states["nvidia"] = {"status": "potential", "label": "잠재 경로 · 미산정", "category": "relationship_only"}
            lines = ["NVIDIA로 GPU 구매 변화가 전달될 수 있으나, CAPEX·GPU 비중 가정이 없어 금액을 계산하지 않습니다."]
        states["dell"] = {"status": "potential", "label": "잠재 경로 · 미산정", "category": "relationship_only"}
        lines.append("Dell: CoreWeave의 Dell 서버 구매 비중이 공시되지 않아 미산정")
    else:
        lines = ["추가 이자 부담이 없으므로 공급망 전달 경로를 표시하지 않습니다."]
    snap(3, lines, gpu_edges)

    # 5 HBM supply chain
    hbm_edges = [x for x in (_edge_to(net, "nvidia", "sk_hynix"), _edge_to(net, "nvidia", "tsmc"), _edge_to(net, "dell", "nvidia")) if x] if propagate else []
    if propagate:
        states["sk_hynix"] = {"status": "potential", "label": "잠재 경로 · 미산정", "category": "relationship_only"}
        states["tsmc"] = {"status": "potential", "label": "잠재 경로 · 미산정", "category": "relationship_only"}
        lines = ["SK hynix: NVIDIA의 HBM 매입 중 SK hynix 비중이 공시되지 않아 금액 미산정 (관계는 확인)",
                 "TSMC: NVIDIA 위탁생산 관계는 산업 구조 추론(INFERRED), 금액 미산정"]
    else:
        lines = ["전달 경로 없음"]
    snap(4, lines, hbm_edges)

    # 6 Network impact
    cats = {}
    for k, v in states.items():
        cats[v["category"]] = cats.get(v["category"], 0) + 1
    lines = [f"계산값: CoreWeave 이자비용 {_m(delta)}/년",
             f"가정 기반 계산 {sum(1 for k, v in states.items() if v['category'] == 'assumed' and k != ORIGIN)}곳 · 관계만 확인(미산정) {cats.get('relationship_only', 0)}곳",
             "고객사·데이터센터 임대인은 이번 차환 충격과 정량 전달 경로가 없어 표시하지 않습니다."]
    snap(5, lines, sorted(set(fin_edges + gpu_edges + hbm_edges)))
    return rounds


NEEDED = {
    "nvidia": "CoreWeave의 연간 NVIDIA GPU 구매액, NVIDIA 매출 중 CoreWeave 비중",
    "dell": "CoreWeave의 Dell 서버 구매액과 Dell AI 서버 매출 중 비중",
    "sk_hynix": "NVIDIA HBM 매입액 중 SK hynix 비중, CoreWeave발 GPU 수요의 HBM 환산액",
    "tsmc": "NVIDIA 위탁생산 금액 중 CoreWeave 관련 비중",
}


def _assessments(net: dict, inst: dict, main: dict, capex_cut, gpu_cut, gpu_vs_nv) -> Dict[str, dict]:
    """Per-entity calculation status (B/C/D/E) next to its relationship path (A)."""
    parts = {p["entity"]: p for p in _participants(inst)}
    delta = main["annual_interest_delta_usd_m"]
    out: Dict[str, dict] = {}
    for n in net["nodes"]:
        nid = n["id"]
        rel = relationship_summary(net, ORIGIN, nid)
        if nid == ORIGIN:
            out[nid] = {"category": "computed", "relation": rel, "values": [
                {"label": "추가 연간 이자비용", "usd_m": delta, "status": "computed", "round": 1},
                *([{"label": "CAPEX 축소 (가정)", "usd_m": -capex_cut, "status": "assumed", "round": 2}] if capex_cut is not None else [])],
                "reason": "공시 차입금 잔액·금리와 사용자 신규 금리로 직접 계산", "needed": None}
            continue
        if rel["kind"] == "unconfirmed":
            out[nid] = {"category": "unconfirmed", "relation": rel, "values": [],
                        "reason": "공개자료에서 CoreWeave와의 관계 경로가 확인되지 않음", "needed": "관계를 입증할 공시·계약 자료"}
            continue
        if nid == "nvidia" and gpu_cut is not None:
            out[nid] = {"category": "assumed", "relation": rel, "values": [
                {"label": "GPU 구매 감소 (가정)", "usd_m": -gpu_cut, "status": "assumed", "round": 3},
                {"label": "NVIDIA FY2026 매출 대비", "pct": gpu_vs_nv, "status": "assumed", "round": 3}],
                "reason": "CAPEX 흡수율·GPU 비중 사용자 가정으로 계산", "needed": NEEDED["nvidia"]}
            continue
        if nid in parts:
            roles = ", ".join(parts[nid]["roles"])
            out[nid] = {"category": "relationship_only", "relation": rel, "values": [],
                        "reason": f"{inst['name']} 참여({roles}). 기관별 보유액이 공시되지 않아 영향 미산정. 금리 상승은 대주에게 손실이 아니라 이자수익 변화입니다.",
                        "needed": "기관별 대출 보유액·재매각 여부"}
            continue
        if nid in NEEDED and (delta or 0) > 0:
            out[nid] = {"category": "relationship_only", "relation": rel, "values": [],
                        "reason": "공급망 관계는 확인되나 전달 규모를 계산할 공개 데이터가 없음", "needed": NEEDED[nid]}
            continue
        out[nid] = {"category": "relationship_only", "relation": rel, "values": [],
                    "reason": "관계는 확인되나 이번 차환 시나리오와 정량 전달 경로가 없음", "needed": None}
    return out
