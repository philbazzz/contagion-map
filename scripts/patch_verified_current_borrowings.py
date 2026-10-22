#!/usr/bin/env python3
"""Hand-verified current-period borrowing edges from original note tables.

Only rows where lender is named and 당기말 outstanding is unambiguous.
Amounts already converted to KRW (원). Never uses 전기말 as current.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
OUT = ROOT / "docs" / "verified_current_borrowings.json"

# Explicit verified rows from reading note tables (당기말 only).
# Format documented in evidence field.
ROWS = [
    # --- 가야 already curated in patch_gaya_borrowings (re-assert) ---
    # --- 디토 20260410001996 단위:원 ---
    {"id": "dart_loan_ibk_dito_senior", "source": "ibk_bank", "target": "dito_pfv", "name": "중소기업은행",
     "krw": 150_000_000_000, "rate": "3M CD+2.26%", "maturity": "2026-12-21",
     "rcept": "20260410001996", "as_of": "2025-12-31", "title": "디토피에프브이 감사보고서 (2025.12)",
     "note": "주석 차입금 당기말 중소기업은행 150,000,000,000원"},
    {"id": "dart_loan_kdb_dito_senior", "source": "kdb", "target": "dito_pfv", "name": "한국산업은행",
     "krw": 100_000_000_000, "rate": "3M CD+2.26%", "maturity": "2026-12-21",
     "rcept": "20260410001996", "as_of": "2025-12-31", "title": "디토피에프브이 감사보고서 (2025.12)",
     "note": "주석 차입금 당기말 한국산업은행 100,000,000,000원"},
    {"id": "dart_loan_ibk_dito_fixed", "source": "ibk_bank", "target": "dito_pfv", "name": "중소기업은행",
     "krw": 25_000_000_000, "rate": "6.29%", "maturity": "2026-12-21",
     "rcept": "20260410001996", "as_of": "2025-12-31", "title": "디토피에프브이 감사보고서 (2025.12)",
     "note": "주석 차입금 당기말 중소기업은행(주2) 25,000,000,000원"},
    # --- 부산에코델타 20260410003722 단위:원 ---
    {"id": "dart_loan_ibk_capital_busan_ecodelta", "source": "ibk_capital", "target": "busan_ecodelta_pfv",
     "name": "IBK캐피탈", "krw": 20_213_728_000, "rate": "4.42%~5.20%", "maturity": "2027",
     "rcept": "20260410003722", "as_of": "2025-12-31",
     "title": "부산에코델타그린데이터센터피에프브이 감사보고서 (2025.12)",
     "note": "주석6 당기말 기업자금대출 (주)IBK캐피탈 20,213,728,000원"},
    # --- 엣지코어 20260403003710 단위:천원 ---
    {"id": "dart_loan_msedc1_edgecore", "source": "msedc1_spc", "target": "edgecore_pfv",
     "name": "엠에스이디씨제일차", "krw": 3_700_000_000, "rate": "5.2%", "maturity": "2029-09-30",
     "rcept": "20260403003710", "as_of": "2025-12-31", "title": "엣지코어피에프브이 감사보고서 (2025.12)",
     "note": "주석5 당기말 Tr.A_엠에스이디씨제일차 3,700,000천원"},
    {"id": "dart_loan_kb_ins_edgecore", "source": "kb_ins", "target": "edgecore_pfv",
     "name": "KB손해보험", "krw": 20_700_000_000, "rate": "5.2%", "maturity": "2029-09-30",
     "rcept": "20260403003710", "as_of": "2025-12-31", "title": "엣지코어피에프브이 감사보고서 (2025.12)",
     "note": "주석5 당기말 KB손해보험 20,700,000천원"},
    {"id": "dart_loan_hyundai_marine_edgecore", "source": "hyundai_marine", "target": "edgecore_pfv",
     "name": "현대해상화재보험", "krw": 7_600_000_000, "rate": "5.2%", "maturity": "2029-09-30",
     "rcept": "20260403003710", "as_of": "2025-12-31", "title": "엣지코어피에프브이 감사보고서 (2025.12)",
     "note": "주석5 당기말 현대해상화재보험 7,600,000천원"},
    {"id": "dart_loan_msedc2_edgecore", "source": "msedc2_spc", "target": "edgecore_pfv",
     "name": "엠에스이디씨제이차", "krw": 50_000_000_000, "rate": "4.5%", "maturity": "2029-09-30",
     "rcept": "20260403003710", "as_of": "2025-12-31", "title": "엣지코어피에프브이 감사보고서 (2025.12)",
     "note": "주석5 당기말 Tr.B_엠에스이디씨제이차 50,000,000천원"},
    # --- 케펠안산 20260330000663 단위:천원 ---
    {"id": "dart_loan_shinhan_capital_keppel_ansan", "source": "shinhan_capital", "target": "keppel_ansan_pfv",
     "name": "신한캐피탈", "krw": 5_000_000_000, "rate": "8.00%", "maturity": "2026-09-29",
     "rcept": "20260330000663", "as_of": "2025-12-31", "title": "케펠데이터센터안산피에프브이 감사보고서 (2025.12)",
     "note": "주석7 당기말 단기 신한캐피탈 5,000,000천원", "financing_stage": "bridge"},
    {"id": "dart_loan_shinhan_sec_keppel_ansan", "source": "shinhan_sec", "target": "keppel_ansan_pfv",
     "name": "신한투자증권", "krw": 6_000_000_000, "rate": "9.00%", "maturity": "2026-09-29",
     "rcept": "20260330000663", "as_of": "2025-12-31", "title": "케펠데이터센터안산피에프브이 감사보고서 (2025.12)",
     "note": "주석7 당기말 단기 신한투자증권 6,000,000천원", "financing_stage": "bridge"},
    {"id": "dart_loan_shinyoung_keppel_ansan", "source": "shinyoung", "target": "keppel_ansan_pfv",
     "name": "주식회사 신영", "krw": 21_000_000_000, "rate": "4.60%", "maturity": None,
     "rcept": "20260330000663", "as_of": "2025-12-31", "title": "케펠데이터센터안산피에프브이 감사보고서 (2025.12)",
     "note": "주석7 당기말 장기 주식회사 신영 21,000,000천원"},
    # facility context for unnamed coop group
    {"id": "dart_facility_keppel_ansan_nonghyup_group", "source": "nh_bank", "target": "keppel_ansan_pfv",
     "name": "가평군농업협동조합 외 7곳", "krw": 20_000_000_000, "rate": "6.5%", "maturity": "2026-09-29",
     "rcept": "20260330000663", "as_of": "2025-12-31", "title": "케펠데이터센터안산피에프브이 감사보고서 (2025.12)",
     "note": "주석7 당기말 단기 '가평군농업협동조합 외 7곳' 20,000,000천원 — 개별 배분 미공개",
     "financing_stage": "bridge", "facility_context": True},
    # --- 청라 20260413000174 단위:천원 ---
    {"id": "dart_loan_wonchang_cheongna", "source": "wonchang_idc", "target": "cheongna_idc_pfv",
     "name": "원창아이디씨", "krw": 10_000_000_000, "rate": "11.00%", "maturity": None,
     "rcept": "20260413000174", "as_of": "2025-12-31", "title": "청라아이디씨피에프브이 감사보고서 (2025.12)",
     "note": "주석11 당기말 브릿지론 원창아이디씨 10,000,000천원", "financing_stage": "bridge"},
    {"id": "dart_loan_gps23_cheongna", "source": "gps23_spc", "target": "cheongna_idc_pfv",
     "name": "쥐피에스23제일차", "krw": 31_000_000_000, "rate": "11.00%", "maturity": None,
     "rcept": "20260413000174", "as_of": "2025-12-31", "title": "청라아이디씨피에프브이 감사보고서 (2025.12)",
     "note": "주석11 당기말 브릿지론 쥐피에스23제일차 31,000,000천원", "financing_stage": "bridge"},
    {"id": "dart_loan_shinhan_capital_cheongna", "source": "shinhan_capital", "target": "cheongna_idc_pfv",
     "name": "신한캐피탈", "krw": 29_000_000_000, "rate": "11.20%", "maturity": None,
     "rcept": "20260413000174", "as_of": "2025-12-31", "title": "청라아이디씨피에프브이 감사보고서 (2025.12)",
     "note": "주석11 당기말 브릿지론 신한캐피탈 29,000,000천원", "financing_stage": "bridge"},
    {"id": "dart_loan_shinhan_sec_cheongna", "source": "shinhan_sec", "target": "cheongna_idc_pfv",
     "name": "신한투자증권", "krw": 20_000_000_000, "rate": "11.50%", "maturity": None,
     "rcept": "20260413000174", "as_of": "2025-12-31", "title": "청라아이디씨피에프브이 감사보고서 (2025.12)",
     "note": "주석11 당기말 브릿지론 신한투자증권 20,000,000천원", "financing_stage": "bridge"},
    {"id": "dart_loan_ido_cheongna_bridge", "source": "ido", "target": "cheongna_idc_pfv",
     "name": "이도", "krw": 5_000_000_000, "rate": "11.70%", "maturity": None,
     "rcept": "20260413000174", "as_of": "2025-12-31", "title": "청라아이디씨피에프브이 감사보고서 (2025.12)",
     "note": "주석11 당기말 브릿지론 ㈜이도 5,000,000천원", "financing_stage": "bridge"},
    {"id": "dart_loan_ido_cheongna_shareholder", "source": "ido", "target": "cheongna_idc_pfv",
     "name": "이도", "krw": 23_239_604_000, "rate": "4.60%", "maturity": None,
     "rcept": "20260413000174", "as_of": "2025-12-31", "title": "청라아이디씨피에프브이 감사보고서 (2025.12)",
     "note": "주석11 당기말 주주차입금 ㈜이도 23,239,604천원"},
    # --- 마그나 20260406003595 단위:천원 — 한도 / 당기말 쌍 ---
    {"id": "dart_loan_kb_magna", "source": "kb_bank", "target": "magna_pfv", "name": "KB국민은행",
     "krw": 9_900_000_000, "limit_krw": 30_000_000_000, "rate": "5.06%", "maturity": "2027-06-05",
     "rcept": "20260406003595", "as_of": "2025-12-31", "title": "마그나피에프브이 감사보고서 (2025.12)",
     "note": "주석 차입금 당기말 (주)국민은행 한도 30,000,000 / 잔액 9,900,000천원"},
    {"id": "dart_loan_shinhan_magna", "source": "shinhan_bank", "target": "magna_pfv", "name": "신한은행",
     "krw": 13_400_000_000, "limit_krw": 40_000_000_000, "rate": "5.06%", "maturity": "2027-06-05",
     "rcept": "20260406003595", "as_of": "2025-12-31", "title": "마그나피에프브이 감사보고서 (2025.12)",
     "note": "주석 차입금 당기말 (주)신한은행 한도 40,000,000 / 잔액 13,400,000천원"},
    {"id": "dart_loan_hana_magna", "source": "hana_bank", "target": "magna_pfv", "name": "하나은행",
     "krw": 8_300_000_000, "limit_krw": 25_000_000_000, "rate": "5.06%", "maturity": "2027-06-05",
     "rcept": "20260406003595", "as_of": "2025-12-31", "title": "마그나피에프브이 감사보고서 (2025.12)",
     "note": "주석 차입금 당기말 (주)하나은행 한도 25,000,000 / 잔액 8,300,000천원"},
    {"id": "dart_loan_ibk_magna", "source": "ibk_bank", "target": "magna_pfv", "name": "중소기업은행",
     "krw": 9_900_000_000, "limit_krw": 30_000_000_000, "rate": "5.06%", "maturity": "2027-06-05",
     "rcept": "20260406003595", "as_of": "2025-12-31", "title": "마그나피에프브이 감사보고서 (2025.12)",
     "note": "주석 차입금 당기말 중소기업은행 한도 30,000,000 / 잔액 9,900,000천원"},
]

# Additional lenders from magna note (한화생명, 현대캐피탈) — from earlier extract context
MAGNA_EXTRA = [
    ("dart_loan_hanwha_life_magna", "hanwha_life", "한화생명보험", 23_200_000_000, 70_000_000_000),
    ("dart_loan_hyundai_capital_magna", "hyundai_capital", "현대캐피탈", None, 43_000_000_000),  # outstanding unclear in snippet
]


def eok(krw: int) -> float:
    return round(krw / 1e8, 4)


def promote(net, node_id, name=None):
    ids = {n["id"] for n in net["nodes"]}
    if node_id in ids:
        return True
    for i, n in enumerate(net.get("hidden_nodes") or []):
        if n.get("id") == node_id:
            p = deepcopy(n)
            p.pop("map_hidden", None)
            for k in ("roles", "key_drivers", "source_ids"):
                if not isinstance(p.get(k), list):
                    p[k] = []
            net["nodes"].append(p)
            net["hidden_nodes"].pop(i)
            return True
    if name:
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
        return True
    return False


def edge_from(row: dict) -> dict:
    fac = bool(row.get("facility_context"))
    krw_eok = eok(row["krw"])
    rcept = row["rcept"]
    src_id = f"dart_audit_{row['target']}_{rcept}"
    return {
        "id": row["id"],
        "source": row["source"],
        "target": row["target"],
        "relationship_type": "PROJECT_LOAN",
        "roles": ["facility_context"] if fac else ["lender"],
        "source_ids": [src_id],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_krw_eok": krw_eok,
        "amount_type": "facility_total_context" if fac else "outstanding_principal",
        "amount_unit": "억원",
        "amount_note": row["note"],
        "amount_as_of": row["as_of"],
        "impact_channel": "financial",
        "source_status": "VERIFIED",
        "label": f"{row['name']} → {row['target']} · {krw_eok:g}억",
        "impact_label": f"{row['name']} 당기말 {krw_eok:g}억",
        "explanation": row["note"],
        "transmission_class": "direct",
        "exposure_status": "ACTIVE_CONFIRMED",
        "relationship_status": "current",
        "shock_eligible": not fac,
        "layer": "fact",
        "evidence_kind": "dart_audit_note",
        "evidence_status": "DART 감사보고서 차입금 주석 당기말",
        "evidence_level": "company_filing",
        "participation_path": "직접 대출",
        "participation_directness": "direct",
        "contingent_obligation": False,
        "source_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}",
        "source_title": row["title"],
        "source_date": f"{rcept[:4]}-{rcept[4:6]}-{rcept[6:8]}",
        "dart_receipt_number": rcept,
        "verification_date": "2026-10-22",
        "maturity": row.get("maturity"),
        "interest_rate": row.get("rate"),
        "financing_stage": row.get("financing_stage") or "main_pf",
        "facility_limit_krw_eok": eok(row["limit_krw"]) if row.get("limit_krw") else None,
        "stress_direction": "차주 부실 → 대주 신용 익스포저",
        "exposure_kind": "facility_total_context" if fac else "loan_principal_outstanding",
        "period_basis": "current_period_당기말",
        "verification_gap": "개별 배분 미공개" if fac else None,
    }


def main() -> None:
    # First re-apply gaya curated
    import subprocess
    subprocess.check_call(["python", str(ROOT / "scripts" / "patch_gaya_borrowings.py")])

    net = json.loads(NET.read_text(encoding="utf-8"))
    rows = list(ROWS)
    for eid, src, name, outstanding, limit in MAGNA_EXTRA:
        if outstanding is None:
            continue  # skip incomplete
        rows.append({
            "id": eid, "source": src, "target": "magna_pfv", "name": name,
            "krw": outstanding, "limit_krw": limit, "rate": "5.06%", "maturity": "2027-06-05",
            "rcept": "20260406003595", "as_of": "2025-12-31",
            "title": "마그나피에프브이 감사보고서 (2025.12)",
            "note": f"주석 차입금 당기말 {name} 한도 {eok(limit):g}억 / 잔액 {eok(outstanding):g}억",
        })

    edges = net["edges"]
    by_id = {e["id"]: i for i, e in enumerate(edges)}
    added, replaced = [], []
    for row in rows:
        promote(net, row["source"], row["name"])
        if row["target"] not in {n["id"] for n in net["nodes"]}:
            continue
        e = edge_from(row)
        src_id = e["source_ids"][0]
        if not any(s.get("id") == src_id for s in net.get("sources") or []):
            net.setdefault("sources", []).append({
                "id": src_id, "title": row["title"], "publisher": "DART",
                "url": e["source_url"], "kind": "filing", "dart_receipt_number": row["rcept"],
                "used_for": "차입금 주석 당기말",
            })
        if e["id"] in by_id:
            edges[by_id[e["id"]]] = e
            replaced.append(e["id"])
        else:
            edges.append(e)
            by_id[e["id"]] = len(edges) - 1
            added.append(e["id"])

    net["edges"] = edges
    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.write_text(json.dumps({"added": added, "replaced": replaced, "rows": len(rows)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"verified loans added={len(added)} replaced={len(replaced)}")


if __name__ == "__main__":
    main()
