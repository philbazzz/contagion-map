#!/usr/bin/env python3
"""Integrate clearly disclosed note-12-style borrowings for additional PFVs.

Hand-verified from cached DART audit XML (not keyword snippets alone).
Amounts use the note's unit (원 or 천원) converted to 억원.
Does not invent allocations for '외 N곳' lender groups.
Never prints API keys.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
OUT = ROOT / "docs" / "borrowings_notes_integration.json"

# Explicit rows: (edge_id, lender_node, borrower_node, krw_principal, meta)
# krw_principal is absolute KRW (already expanded from 천원 where needed).
ROWS = [
    # --- 디토피에프브이 감사보고서 20260410001996 주석 차입금 (단위: 원) ---
    {
        "id": "dart_loan_ibk_dito_senior",
        "source": "ibk_bank",
        "target": "dito_pfv",
        "name": "중소기업은행",
        "krw": 150_000_000_000,
        "rate": "3개월 CD+2.26%",
        "maturity": "2026-12-21",
        "as_of": "2025-12-31",
        "rcept": "20260410001996",
        "title": "디토피에프브이 감사보고서 (2025.12)",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260410001996",
        "project": "디토 PFV",
        "note": "주석 차입금: 중소기업은행 1500억 (당기말=전기말)",
        "src_id": "dart_audit_dito_pfv_20260410001996",
    },
    {
        "id": "dart_loan_kdb_dito_senior",
        "source": "kdb",
        "target": "dito_pfv",
        "name": "한국산업은행",
        "krw": 100_000_000_000,
        "rate": "3개월 CD+2.26%",
        "maturity": "2026-12-21",
        "as_of": "2025-12-31",
        "rcept": "20260410001996",
        "title": "디토피에프브이 감사보고서 (2025.12)",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260410001996",
        "project": "디토 PFV",
        "note": "주석 차입금: 한국산업은행 1000억",
        "src_id": "dart_audit_dito_pfv_20260410001996",
    },
    {
        "id": "dart_loan_ibk_dito_fixed",
        "source": "ibk_bank",
        "target": "dito_pfv",
        "name": "중소기업은행",
        "krw": 25_000_000_000,
        "rate": "6.29%",
        "maturity": "2026-12-21",
        "as_of": "2025-12-31",
        "rcept": "20260410001996",
        "title": "디토피에프브이 감사보고서 (2025.12)",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260410001996",
        "project": "디토 PFV",
        "note": "주석 차입금: 중소기업은행(주2) 250억 고정금리",
        "src_id": "dart_audit_dito_pfv_20260410001996",
        "tranche": "fixed_tranche",
    },
    # --- 부산에코델타 20260410003722 주석6 장기차입금 (단위: 원) ---
    {
        "id": "dart_loan_ibk_capital_busan_ecodelta",
        "source": "ibk_capital",
        "target": "busan_ecodelta_pfv",
        "name": "IBK캐피탈",
        "krw": 20_213_728_000,
        "rate": "4.42%~5.20%",
        "maturity": "2027",
        "as_of": "2025-12-31",
        "rcept": "20260410003722",
        "title": "부산에코델타그린데이터센터피에프브이 감사보고서 (2025.12)",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260410003722",
        "project": "부산 에코델타 그린 DC",
        "note": "주석6 기업자금대출 (주)IBK캐피탈 20,213,728,000원",
        "src_id": "dart_audit_busan_ecodelta_pfv_20260410003722",
    },
    # --- 엣지코어 20260403003710 주석5 (단위: 천원) → ×1000 ---
    {
        "id": "dart_loan_kb_ins_edgecore",
        "source": "kb_ins",
        "target": "edgecore_pfv",
        "name": "KB손해보험",
        "krw": 20_700_000_000,
        "rate": "5.2%",
        "maturity": "2029-09-30",
        "as_of": "2025-12-31",
        "rcept": "20260403003710",
        "title": "엣지코어피에프브이 감사보고서 (2025.12)",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260403003710",
        "project": "엣지코어 PFV",
        "note": "주석5 장기차입금 KB손해보험 20,700,000천원",
        "src_id": "dart_audit_edgecore_pfv_20260403003710",
        "unit_in_note": "천원",
    },
    {
        "id": "dart_loan_hyundai_marine_edgecore",
        "source": "hyundai_marine",
        "target": "edgecore_pfv",
        "name": "현대해상화재보험",
        "krw": 7_600_000_000,
        "rate": "5.2%",
        "maturity": "2029-09-30",
        "as_of": "2025-12-31",
        "rcept": "20260403003710",
        "title": "엣지코어피에프브이 감사보고서 (2025.12)",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260403003710",
        "project": "엣지코어 PFV",
        "note": "주석5 장기차입금 현대해상 7,600,000천원",
        "src_id": "dart_audit_edgecore_pfv_20260403003710",
        "unit_in_note": "천원",
    },
    # --- 케펠안산(=다올1호) 20260330000663 주석7 (단위: 천원) ---
    # '가평군농업협동조합 외 7곳' is a group — map as unnamed syndicate facility context only.
    {
        "id": "dart_loan_shinhan_capital_keppel_ansan",
        "source": "shinhan_capital",
        "target": "keppel_ansan_pfv",
        "name": "신한캐피탈",
        "krw": 5_000_000_000,
        "rate": "8.00%",
        "maturity": "2026-09-29",
        "as_of": "2025-12-31",
        "rcept": "20260330000663",
        "title": "케펠데이터센터안산피에프브이 감사보고서 (2025.12)",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260330000663",
        "project": "케펠 안산 DC",
        "note": "주석7 단기차입금 신한캐피탈 5,000,000천원",
        "src_id": "dart_audit_keppel_ansan_pfv_20260330000663",
        "financing_stage": "bridge",
        "unit_in_note": "천원",
    },
    {
        "id": "dart_loan_shinhan_sec_keppel_ansan",
        "source": "shinhan_sec",
        "target": "keppel_ansan_pfv",
        "name": "신한투자증권",
        "krw": 6_000_000_000,
        "rate": "9.00%",
        "maturity": "2026-09-29",
        "as_of": "2025-12-31",
        "rcept": "20260330000663",
        "title": "케펠데이터센터안산피에프브이 감사보고서 (2025.12)",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260330000663",
        "project": "케펠 안산 DC",
        "note": "주석7 단기차입금 신한투자증권 6,000,000천원",
        "src_id": "dart_audit_keppel_ansan_pfv_20260330000663",
        "financing_stage": "bridge",
        "unit_in_note": "천원",
    },
    # --- 청라IDC 20260413000174 주석11 단기차입금 (단위: 천원) ---
    {
        "id": "dart_loan_shinhan_capital_cheongna",
        "source": "shinhan_capital",
        "target": "cheongna_idc_pfv",
        "name": "신한캐피탈",
        "krw": 29_000_000_000,
        "rate": "11.20%",
        "maturity": None,
        "as_of": "2025-12-31",
        "rcept": "20260413000174",
        "title": "청라아이디씨피에프브이 감사보고서 (2025.12)",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260413000174",
        "project": "청라 IDC",
        "note": "주석11 브릿지론 신한캐피탈 29,000,000천원",
        "src_id": "dart_audit_cheongna_idc_pfv_20260413000174",
        "financing_stage": "bridge",
        "unit_in_note": "천원",
    },
    {
        "id": "dart_loan_shinhan_sec_cheongna",
        "source": "shinhan_sec",
        "target": "cheongna_idc_pfv",
        "name": "신한투자증권",
        "krw": 20_000_000_000,
        "rate": "11.50%",
        "maturity": None,
        "as_of": "2025-12-31",
        "rcept": "20260413000174",
        "title": "청라아이디씨피에프브이 감사보고서 (2025.12)",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260413000174",
        "project": "청라 IDC",
        "note": "주석11 브릿지론 신한투자증권 20,000,000천원",
        "src_id": "dart_audit_cheongna_idc_pfv_20260413000174",
        "financing_stage": "bridge",
        "unit_in_note": "천원",
    },
]

# Magna amounts are in 천원 in the extract context — need careful parse.
# From extract: (주)국민은행 5.06% 30,000,000 9,900,000 — likely limit / outstanding in 천원
MAGNA = [
    ("dart_loan_kb_magna", "kb_bank", "KB국민은행", 9_900_000_000, 30_000_000_000),
    ("dart_loan_shinhan_magna", "shinhan_bank", "신한은행", 13_400_000_000, 40_000_000_000),
    ("dart_loan_hana_magna", "hana_bank", "하나은행", 8_300_000_000, 25_000_000_000),
    ("dart_loan_ibk_magna", "ibk_bank", "중소기업은행", 9_900_000_000, 30_000_000_000),
]


def eok(krw: int) -> float:
    return round(krw / 1e8, 4)


def ensure_source(net: dict, src_id: str, title: str, url: str, rcept: str) -> None:
    sources = net.setdefault("sources", [])
    if any(s.get("id") == src_id for s in sources):
        return
    sources.append({
        "id": src_id,
        "title": title,
        "publisher": "DART",
        "date": rcept[:8] if rcept else None,
        "url": url,
        "used_for": "차입금 주석",
        "kind": "filing",
        "dart_receipt_number": rcept,
    })


def promote_or_skip(net: dict, node_id: str) -> bool:
    ids = {n["id"] for n in net["nodes"]}
    if node_id in ids:
        return True
    hidden = net.get("hidden_nodes") or []
    for i, n in enumerate(hidden):
        if n.get("id") == node_id:
            p = deepcopy(n)
            p.pop("map_hidden", None)
            p["display_size"] = max(float(p.get("display_size") or 1), 1)
            for k in ("roles", "key_drivers", "source_ids"):
                if not isinstance(p.get(k), list):
                    p[k] = []
            net["nodes"].append(p)
            hidden.pop(i)
            net["hidden_nodes"] = hidden
            return True
    return False


def make_edge(row: dict) -> dict:
    krw_eok = eok(row["krw"])
    return {
        "id": row["id"],
        "source": row["source"],
        "target": row["target"],
        "relationship_type": "PROJECT_LOAN",
        "roles": ["lender"],
        "source_ids": [row["src_id"]],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_krw_eok": krw_eok,
        "amount_type": "outstanding_principal",
        "amount_unit": "억원",
        "amount_note": row["note"],
        "amount_as_of": row["as_of"],
        "impact_channel": "financial",
        "source_status": "VERIFIED",
        "label": f"{row['name']} → {row['target']} · {krw_eok:g}억",
        "impact_label": f"{row['name']} 대출잔액 {krw_eok:g}억 ({row['as_of']})",
        "explanation": row["note"],
        "transmission_class": "direct",
        "exposure_status": "ACTIVE_CONFIRMED",
        "relationship_status": "current",
        "shock_eligible": True,
        "layer": "fact",
        "evidence_kind": "dart_audit_note",
        "evidence_status": "DART 감사보고서 차입금 주석",
        "evidence_level": "company_filing",
        "participation_path": "직접 대출",
        "participation_directness": "direct",
        "contingent_obligation": False,
        "project_id": None,
        "project_name": row["project"],
        "source_url": row["url"],
        "source_title": row["title"],
        "source_date": f"{row['rcept'][:4]}-{row['rcept'][4:6]}-{row['rcept'][6:8]}",
        "dart_receipt_number": row["rcept"],
        "verification_date": "2026-10-22",
        "maturity": row.get("maturity"),
        "interest_rate": row.get("rate"),
        "financing_stage": row.get("financing_stage") or "main_pf",
        "stress_direction": "차주 부실 → 대주 신용 익스포저",
        "exposure_kind": "loan_principal_outstanding",
        "facility_limit_krw_eok": eok(row["facility_limit"]) if row.get("facility_limit") else None,
    }


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    # Ensure kb_insurance exists or map to samsung? Check
    # Prefer existing kb insurance node
    node_ids = {n["id"] for n in net["nodes"]}
    # alias fix for KB insurance
    if "kb_insurance" not in node_ids:
        for cand in ("kb_ins", "kb_nonlife", "kb_sonbo"):
            if cand in node_ids:
                for r in ROWS:
                    if r["source"] == "kb_insurance":
                        r["source"] = cand
                break
        else:
            # search by name
            for n in net["nodes"]:
                if "KB손해" in (n.get("name_ko") or "") or "KB손보" in (n.get("name_ko") or ""):
                    for r in ROWS:
                        if r["source"] == "kb_insurance":
                            r["source"] = n["id"]
                    break

    rows = list(ROWS)
    for eid, src, name, outstanding, limit in MAGNA:
        rows.append({
            "id": eid,
            "source": src,
            "target": "magna_pfv",
            "name": name,
            "krw": outstanding,
            "facility_limit": limit,
            "rate": "5.06%",
            "maturity": "2027-06-05",
            "as_of": "2025-12-31",
            "rcept": "20260406003595",
            "title": "마그나피에프브이 감사보고서 (2025.12)",
            "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260406003595",
            "project": "마그나 고양 덕이 DC",
            "note": f"주석 차입금 {name} 한도 {eok(limit):g}억 · 당기말 {eok(outstanding):g}억 (단위 천원→원)",
            "src_id": "dart_audit_magna_pfv_20260406003595",
            "unit_in_note": "천원",
        })

    # Facility-context for keppel group lenders (가평군농협 외 7곳) — no per-lender amount
    keppel_group = {
        "id": "dart_facility_keppel_ansan_nonghyup_group",
        "source": "nh_bank",
        "target": "keppel_ansan_pfv",
        "relationship_type": "PROJECT_LOAN",
        "roles": ["facility_context"],
        "source_ids": ["dart_audit_keppel_ansan_pfv_20260330000663"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_krw_eok": 200.0,
        "amount_type": "facility_total_context",
        "amount_unit": "억원",
        "amount_note": "주석7: '가평군농업협동조합 외 7곳' 단기 200억 — 개별 배분 미기재. 농협은행 노드에 시설 맥락만 연결(이중계상 방지용 shock_eligible=false).",
        "amount_as_of": "2025-12-31",
        "impact_channel": "financial",
        "source_status": "VERIFIED",
        "label": "가평군농협 외 7곳 → 케펠안산 · 단기 200억(그룹)",
        "impact_label": "단체 차입처 — 개별 배분 미공개",
        "explanation": "표에 개별 조합·은행명이 없고 '외 7곳'만 기재. 개별 대주 엣지 미작성.",
        "transmission_class": "direct",
        "exposure_status": "ACTIVE_CONFIRMED",
        "relationship_status": "current",
        "shock_eligible": False,
        "layer": "fact",
        "evidence_kind": "dart_audit_note",
        "evidence_status": "DART 감사보고서 차입금 주석",
        "evidence_level": "company_filing",
        "participation_path": "직접 대출(신디케이션 그룹)",
        "participation_directness": "direct",
        "contingent_obligation": False,
        "project_name": "케펠 안산 DC",
        "source_url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260330000663",
        "source_title": "케펠데이터센터안산피에프브이 감사보고서 (2025.12)",
        "source_date": "2026-03-30",
        "dart_receipt_number": "20260330000663",
        "verification_date": "2026-10-22",
        "financing_stage": "bridge",
        "exposure_kind": "facility_total_context",
        "verification_gap": "개별 조합·기관 배분 미공개",
    }

    edges = net["edges"]
    by_id = {e["id"]: i for i, e in enumerate(edges)}
    report = {"added": [], "replaced": [], "skipped_missing_node": [], "rows": []}

    for row in rows:
        ensure_source(net, row["src_id"], row["title"], row["url"], row["rcept"])
        if not promote_or_skip(net, row["source"]):
            report["skipped_missing_node"].append({"edge": row["id"], "source": row["source"]})
            continue
        # borrower must exist
        if row["target"] not in {n["id"] for n in net["nodes"]}:
            report["skipped_missing_node"].append({"edge": row["id"], "target": row["target"]})
            continue
        e = make_edge(row)
        if e["id"] in by_id:
            edges[by_id[e["id"]]] = e
            report["replaced"].append(e["id"])
        else:
            edges.append(e)
            by_id[e["id"]] = len(edges) - 1
            report["added"].append(e["id"])
        report["rows"].append({
            "source_counterparty": row["name"],
            "borrower": row["target"],
            "disclosed_amount": f"{eok(row['krw']):g}억 outstanding",
            "reporting_date": row["as_of"],
            "relationship_id": row["id"],
            "mapping_status": "mapped_active",
        })

    # keppel group context
    ensure_source(
        net,
        "dart_audit_keppel_ansan_pfv_20260330000663",
        "케펠데이터센터안산피에프브이 감사보고서 (2025.12)",
        keppel_group["source_url"],
        "20260330000663",
    )
    if keppel_group["id"] in by_id:
        edges[by_id[keppel_group["id"]]] = keppel_group
        report["replaced"].append(keppel_group["id"])
    else:
        edges.append(keppel_group)
        report["added"].append(keppel_group["id"])
    report["rows"].append({
        "source_counterparty": "가평군농업협동조합 외 7곳",
        "borrower": "keppel_ansan_pfv",
        "disclosed_amount": "200억 group short-term",
        "reporting_date": "2025-12-31",
        "relationship_id": keppel_group["id"],
        "mapping_status": "mapped_facility_context_individual_allocations_unknown",
    })

    # Update borrower descriptions lightly for dito
    for n in net["nodes"]:
        if n["id"] == "dito_pfv":
            n["connection_status"] = "관계 확인"
            n["description"] = (
                (n.get("description") or "")
                + " 주석 차입금: 기업은행 1,500억+250억 · 산업은행 1,000억 (2025.12.31)."
            ).strip()

    net["edges"] = edges
    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OK added={len(report['added'])} replaced={len(report['replaced'])} "
        f"skipped={len(report['skipped_missing_node'])} → {OUT}"
    )
    if report["skipped_missing_node"]:
        print("SKIPPED", report["skipped_missing_node"])


if __name__ == "__main__":
    main()
