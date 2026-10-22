#!/usr/bin/env python3
"""Map 안산그린에너지피에프브이 note-5 장기차입금 (당기말) into network.json.

Evidence: 감사보고서 (2025.12) rcept 20260406003916, 주석5 장기차입금.
Unit in note: 천원. Columns verified: 총약정액 | 당기말 (current outstanding).
Never uses 전기 (전기 BS 장기차입금 was '-').
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend/public/data/pf/network.json"
OUT_RECON = ROOT / "docs/ansan_green_borrowings_reconciliation.json"

RCEPT = "20260406003916"
TITLE = "안산그린에너지피에프브이 감사보고서 (2025.12)"
AS_OF = "2025-12-31"
VERIFY = "2026-10-22"
TARGET = "ansan_green_energy_pfv"
URL = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={RCEPT}"


def eok_from_cheon(cheon: int) -> float:
    """천원 → 억원 (100,000천원 = 1억)."""
    return round(cheon / 100_000, 4)


# (edge_id, source_id, display_name, 당기말_천원, 총약정_천원, tranche, rate)
# source_id is the disclosed counterparty legal/vehicle identity.
ROWS = [
    # Tr.A-1 6.7% 2029-06-16
    ("dart_loan_kb_capital_ansan_green_ta1", "kb_capital", "KB캐피탈", 5_777_778, 50_000_000, "Tr.A-1", "6.7%"),
    ("dart_loan_nh_inv_ansan_green_ta1", "nh_inv_sec", "NH투자증권", 1_155_556, 10_000_000, "Tr.A-1", "6.7%"),
    ("dart_loan_thek_ansan_green_ta1", "thek_savings", "더케이저축은행", 1_155_556, 10_000_000, "Tr.A-1", "6.7%"),
    ("dart_loan_nh_federation_ansan_green_ta1", "nh_federation", "농협중앙회", 23_111_110, 200_000_000, "Tr.A-1", "6.7%"),
    ("dart_loan_hana_alt_gg1_ansan_green_ta1", "hana_alt_geongungoong_1", "하나대체자산운용(건근공)1", 1_155_556, 10_000_000, "Tr.A-1", "6.7%"),
    # Tr.A-2 6.3% 2029-06-16
    ("dart_loan_nh_inv_ansan_green_ta2", "nh_inv_sec", "NH투자증권", 1_155_556, 10_000_000, "Tr.A-2", "6.3%"),
    ("dart_loan_fund_kb_re2_ansan_green_ta2", "fund_kb_re_loan_pe2", "KB부동산대출일반사모부동산투자신탁제2호", 8_088_889, 70_000_000, "Tr.A-2", "6.3%"),
    ("dart_loan_db_ins_ansan_green_ta2", "db_ins", "DB손해보험", 23_111_110, 200_000_000, "Tr.A-2", "6.3%"),
    ("dart_loan_hana_alt_gg2_ansan_green_ta2", "hana_alt_geongungoong_2", "하나대체자산운용(건근공)2", 4_622_222, 40_000_000, "Tr.A-2", "6.3%"),
    ("dart_loan_hyundai_capital_ansan_green_ta2", "hyundai_capital", "현대캐피탈", 5_777_778, 50_000_000, "Tr.A-2", "6.3%"),
    ("dart_loan_shinhan_capital_a_ansan_green_ta2", "shinhan_capital", "신한캐피탈A", 2_311_111, 20_000_000, "Tr.A-2", "6.3%"),
    ("dart_loan_nh_capital_ansan_green_ta2", "nh_capital", "농협캐피탈", 1_155_556, 10_000_000, "Tr.A-2", "6.3%"),
    ("dart_loan_lotte_ins_ansan_green_ta2", "lotte_ins", "롯데손해보험", 2_311_111, 20_000_000, "Tr.A-2", "6.3%"),
    # Tr.B 7.8% 2029-06-16
    ("dart_loan_fund_aip_re2_ansan_green_tb", "fund_aip_re2", "에이아이파트너스일반사모부동산투자신탁2호", 8_088_889, 70_000_000, "Tr.B", "7.8%"),
    ("dart_loan_shinhan_core_ii_ansan_green_tb", "shinhan_core_re_loan_ii", "신한코어부동산론II", 9_937_777, 86_000_000, "Tr.B", "7.8%"),
    ("dart_loan_shinhan_core_iv_ansan_green_tb", "shinhan_core_re_loan_iv", "신한코어부동산론IV", 3_928_889, 34_000_000, "Tr.B", "7.8%"),
    ("dart_loan_shinhan_capital_ansan_green_tb", "shinhan_capital", "신한캐피탈", 1_155_556, 10_000_000, "Tr.B", "7.8%"),
]

TRUSTEE_NOTE = {
    "fund_kb_re_loan_pe2": "공시 차입처: 중소기업은행(KB부동산대출일반사모부동산투자신탁제2호(전문) 신탁업자) — 펀드 법인으로 매핑, 신탁업자=IBK",
    "fund_aip_re2": "공시 차입처: 농협은행 주식회사(에이아이파트너스일반사모부동산투자신탁2호(전문투자자) 신탁업자) — 펀드 법인으로 매핑, 신탁업자=NH농협은행",
}


def promote(net, node_id: str, name: str) -> None:
    ids = {n["id"] for n in net["nodes"]}
    if node_id in ids:
        return
    for i, n in enumerate(net.get("hidden_nodes") or []):
        if n.get("id") == node_id:
            p = deepcopy(n)
            p.pop("map_hidden", None)
            for k in ("roles", "key_drivers", "source_ids"):
                if not isinstance(p.get(k), list):
                    p[k] = []
            net["nodes"].append(p)
            net["hidden_nodes"].pop(i)
            return
    net["nodes"].append({
        "id": node_id,
        "name": name,
        "name_ko": name,
        "group": "financial",
        "entity_type": "lender",
        "region": "KR",
        "listed": False,
        "display_size": 1,
        "source_status": "VERIFIED",
        "roles": ["lender"],
        "key_drivers": [],
        "source_ids": [],
        "connection_status": "관계 확인",
        "is_company": True,
        "pf_exposure_class": "confirmed_dc_finance",
    })


def edge_from(row) -> dict:
    eid, src, name, outstanding_cheon, limit_cheon, tranche, rate = row
    krw_eok = eok_from_cheon(outstanding_cheon)
    limit_eok = eok_from_cheon(limit_cheon)
    note = (
        f"주석5 당기말 {tranche} {name} 잔액 {outstanding_cheon:,}천원"
        f" (총약정 {limit_cheon:,}천원, 만기 2029-06-16, {rate})"
    )
    if src in TRUSTEE_NOTE:
        note += " · " + TRUSTEE_NOTE[src]
    return {
        "id": eid,
        "source": src,
        "target": TARGET,
        "relationship_type": "PROJECT_LOAN",
        "roles": ["lender"],
        "source_ids": [f"dart_audit_{TARGET}_{RCEPT}"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_krw_eok": krw_eok,
        "amount_type": "outstanding_principal",
        "amount_unit": "억원",
        "amount_note": note,
        "amount_as_of": AS_OF,
        "impact_channel": "financial",
        "source_status": "VERIFIED",
        "label": f"{name} → 안산그린에너지 · {krw_eok:g}억",
        "impact_label": f"{name} 당기말 {krw_eok:g}억 ({tranche})",
        "explanation": note,
        "transmission_class": "direct",
        "exposure_status": "ACTIVE_CONFIRMED",
        "relationship_status": "current",
        "shock_eligible": True,
        "layer": "fact",
        "evidence_kind": "dart_audit_note",
        "evidence_status": "DART 감사보고서 주석5 장기차입금 당기말",
        "evidence_level": "company_filing",
        "participation_path": "직접 대출",
        "participation_directness": "direct",
        "contingent_obligation": False,
        "source_url": URL,
        "source_title": TITLE,
        "source_date": "2026-04-06",
        "dart_receipt_number": RCEPT,
        "verification_date": VERIFY,
        "maturity": "2029-06-16",
        "interest_rate": rate,
        "financing_stage": "main_pf",
        "facility_limit_krw_eok": limit_eok,
        "tranche": tranche,
        "stress_direction": "차주 부실 → 대주 신용 익스포저",
        "exposure_kind": "loan_principal_outstanding",
        "period_basis": "current_period_당기말",
        "repayment_method": "만기일시상환",
    }


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    edges = net["edges"]
    by_id = {e["id"]: i for i, e in enumerate(edges)}

    src_id = f"dart_audit_{TARGET}_{RCEPT}"
    if not any(s.get("id") == src_id for s in net.get("sources") or []):
        net.setdefault("sources", []).append({
            "id": src_id,
            "title": TITLE,
            "publisher": "DART",
            "url": URL,
            "kind": "filing",
            "dart_receipt_number": RCEPT,
            "used_for": "주석5 장기차입금 당기말",
        })

    # Ensure borrower node has dart metadata
    for n in net["nodes"]:
        if n["id"] == TARGET:
            n["dart_corp_code"] = n.get("dart_corp_code") or "01843299"
            n["dart_last_audit_rcept"] = RCEPT
            break

    added, replaced = [], []
    recon_rows = []
    for row in ROWS:
        eid, src, name, outstanding_cheon, limit_cheon, tranche, rate = row
        promote(net, src, name)
        e = edge_from(row)
        if eid in by_id:
            edges[by_id[eid]] = e
            replaced.append(eid)
            prior = "updated"
        else:
            edges.append(e)
            by_id[eid] = len(edges) - 1
            added.append(eid)
            prior = "missing — created"
        recon_rows.append({
            "source_table_row": f"{tranche} / {name}",
            "lender": name,
            "lender_node_id": src,
            "current_period_amount": f"{outstanding_cheon:,}천원 (= {eok_from_cheon(outstanding_cheon):g}억)",
            "facility_limit": f"{limit_cheon:,}천원 (= {eok_from_cheon(limit_cheon):g}억)",
            "rate": rate,
            "maturity": "2029-06-16",
            "existing_graph_status": prior,
            "applied_correction": "Insert/replace dart_loan_* from note5 당기말; prior false 'no borrowings' status removed",
            "final_graph_relationship_id": eid,
        })

    # Facility-level context (합계) — not assigned to each lender
    fac_id = "dart_facility_ansan_green_term_loan_2025"
    fac = {
        "id": fac_id,
        "source": "kb_capital",  # lead/context only
        "target": TARGET,
        "relationship_type": "PROJECT_LOAN",
        "roles": ["facility_context"],
        "source_ids": [src_id],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_krw_eok": eok_from_cheon(104_000_000),
        "amount_type": "facility_total_context",
        "amount_unit": "억원",
        "amount_note": (
            "주석5 당기말 장기차입금 소계 104,000,000천원 (총약정 900,000,000천원). "
            "개별 대주 잔액은 dart_loan_*_ansan_green_* 에 매핑. PV할인차금 차감 후 장부가 75,323,545천원."
        ),
        "amount_as_of": AS_OF,
        "impact_channel": "financial",
        "source_status": "VERIFIED",
        "label": "안산그린에너지 장기차입금 합계 · 1040억",
        "impact_label": "시설 합계 컨텍스트 1040억",
        "explanation": "Facility total context only — do not double-count with lender rows",
        "transmission_class": "direct",
        "exposure_status": "ACTIVE_CONFIRMED",
        "relationship_status": "current",
        "shock_eligible": False,
        "layer": "fact",
        "evidence_kind": "dart_audit_note",
        "evidence_status": "DART 감사보고서 주석5 합계",
        "evidence_level": "company_filing",
        "participation_path": "시설 합계",
        "participation_directness": "direct",
        "contingent_obligation": False,
        "source_url": URL,
        "source_title": TITLE,
        "source_date": "2026-04-06",
        "dart_receipt_number": RCEPT,
        "verification_date": VERIFY,
        "maturity": "2029-06-16",
        "financing_stage": "main_pf",
        "facility_limit_krw_eok": eok_from_cheon(900_000_000),
        "facility_total_context": True,
        "exposure_kind": "facility_total_context",
        "period_basis": "current_period_당기말",
    }
    if fac_id in by_id:
        edges[by_id[fac_id]] = fac
        replaced.append(fac_id)
    else:
        edges.append(fac)
        added.append(fac_id)

    net["edges"] = edges
    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sum_eok = sum(eok_from_cheon(r[3]) for r in ROWS)
    payload = {
        "pfv": "안산그린에너지피에프브이",
        "node_id": TARGET,
        "rcept": RCEPT,
        "reporting_date": AS_OF,
        "filing_date": "2026-04-06",
        "note": "주석5 장기차입금",
        "unit_in_note": "천원",
        "pipeline_failure": (
            "Report WAS cached (20260406003916) but borrowings note was never mapped; "
            "coverage script hard-coded status 'Reviewed — no outstanding borrowings disclosed' "
            "despite BS 장기차입금 당기말 104,000,000,000원 and note5 lender table. "
            "Zero PROJECT_LOAN edges existed before this patch."
        ),
        "facility_outstanding_eok": eok_from_cheon(104_000_000),
        "facility_limit_eok": eok_from_cheon(900_000_000),
        "lender_rows_sum_eok": round(sum_eok, 4),
        "added": added,
        "replaced": replaced,
        "row_by_row": recon_rows,
    }
    OUT_RECON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ansan_green added={len(added)} replaced={len(replaced)} sum_eok={sum_eok:.4f} expected~1040")


if __name__ == "__main__":
    main()
