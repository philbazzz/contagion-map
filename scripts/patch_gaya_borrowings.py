#!/usr/bin/env python3
"""Map 가야피에프브이 note-12 borrowings into pf/network.json from the original DART XML.

Evidence: 감사보고서 (2025.12) rcept 20260408000296, 주석 12 차입금.
Does not invent unnamed syndicate allocations.
Never prints API keys.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
OUT_RECON = ROOT / "docs" / "gaya_borrowings_reconciliation.json"

SRC = "dart_audit_gaya_pfv_20260408000296"
URL = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260408000296"
TITLE = "가야피에프브이 감사보고서 (2025.12)"
RCEPT = "20260408000296"
AS_OF = "2025-12-31"
VERIFY = "2026-10-22"
PROJECT = "가야 데이터센터 PFV"

# Gross outstanding principal from note 12 (당기) — 약정한도액 = 당기말 for each row.
# Unit: KRW. amount_krw_eok = KRW / 1e8.
CURRENT = [
    {
        "id": "dart_loan_kb_gaya_tla",
        "source": "kb_bank",
        "name": "KB국민은행",
        "tranche": "Term Loan A",
        "krw": 119_000_000_000,
        "rate": "CD+1.5%",
        "maturity": "2030-12-11",
        "facility_limit_krw": 119_000_000_000,
    },
    {
        "id": "dart_loan_ubob_gaya_tla",
        "source": "ubob_seoul",
        "name": "대화은행 서울지점",
        "tranche": "Term Loan A",
        "krw": 79_500_000_000,
        "rate": "CD+1.5%",
        "maturity": "2030-12-11",
        "facility_limit_krw": 79_500_000_000,
    },
    {
        "id": "dart_loan_hyundai_marine_gaya_tla",
        "source": "hyundai_marine",
        "name": "현대해상화재보험",
        "tranche": "Term Loan A",
        "krw": 10_000_000_000,
        "rate": "CD+1.5%",
        "maturity": "2030-12-11",
        "facility_limit_krw": 10_000_000_000,
    },
    {
        "id": "dart_loan_hyundai_marine_gaya_tlb",
        "source": "hyundai_marine",
        "name": "현대해상화재보험",
        "tranche": "Term Loan B",
        "krw": 30_000_000_000,
        "rate": "4.31%",
        "maturity": "2030-12-11",
        "facility_limit_krw": 30_000_000_000,
    },
]

# Prior facility (전기) — footnote: 2025.12 refinanced into Term Loan A/B.
HISTORICAL = [
    {
        "id": "dart_loan_shinhyup_gaya_facility_prior",
        "source": "shinhyup_federation",
        "name": "신용협동조합중앙회",
        "tranche": "시설자금(전기)",
        "krw": 50_000_000_000,
        "rate": "7.30%",
        "maturity": "2026-04-20",
    },
    {
        "id": "dart_loan_hana_bank_gaya_facility_prior",
        "source": "hana_bank",
        "name": "하나은행",
        "tranche": "시설자금(전기)",
        "krw": 30_000_000_000,
        "rate": "7.30%",
        "maturity": "2026-04-20",
    },
    {
        "id": "dart_loan_hana_capital_gaya_facility_prior",
        "source": "hana_capital",
        "name": "하나캐피탈",
        "tranche": "시설자금(전기)",
        "krw": 30_000_000_000,
        "rate": "7.30%",
        "maturity": "2026-04-20",
    },
]

FACILITY_GROSS = 238_500_000_000
FACILITY_CARRYING = 235_303_230_593
PV_DISCOUNT = 3_196_769_407


def eok(krw: int) -> float:
    return round(krw / 1e8, 4)


def base_edge(**kw):
    e = {
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "impact_channel": "financial",
        "source_status": "VERIFIED",
        "transmission_class": "direct",
        "layer": "fact",
        "evidence_kind": "dart_audit_note",
        "evidence_status": "DART 감사보고서 주석12 차입금",
        "evidence_level": "company_filing",
        "participation_path": "직접 대출",
        "participation_directness": "direct",
        "contingent_obligation": False,
        "project_id": None,
        "project_name": PROJECT,
        "source_url": URL,
        "source_title": TITLE,
        "source_date": "2026-04-08",
        "dart_receipt_number": RCEPT,
        "verification_date": VERIFY,
        "financing_stage": "main_pf",
        "relationship_type": "PROJECT_LOAN",
        "roles": ["lender"],
        "source_ids": [SRC],
        "target": "gaya_pfv",
        "stress_direction": "차주 부실 → 대주 신용 익스포저",
        "exposure_kind": "loan_principal_outstanding",
    }
    e.update(kw)
    return e


def current_edge(row: dict) -> dict:
    krw_eok = eok(row["krw"])
    return base_edge(
        id=row["id"],
        source=row["source"],
        label=f"{row['name']} → 가야PFV · {row['tranche']} {krw_eok:g}억",
        impact_label=f"{row['name']} {row['tranche']} 잔액 {krw_eok:g}억 (2025.12.31)",
        explanation=(
            f"주석12(당기) Term Loan: 차입처 {row['name']}, "
            f"만기 {row['maturity']}, 이자율 {row['rate']}, "
            f"약정한도 {eok(row['facility_limit_krw']):g}억, 당기말 잔액 {krw_eok:g}억. "
            f"시설 총액(할인 전) {eok(FACILITY_GROSS):g}억 · 장부가 {eok(FACILITY_CARRYING):g}억 "
            f"(현재가치할인차금 {eok(PV_DISCOUNT):g}억) — 개별 잔액은 할인 전 원금."
        ),
        amount_krw_eok=krw_eok,
        amount_type="outstanding_principal_gross",
        amount_unit="억원",
        amount_note=(
            f"감사보고서 주석12 당기말 원금 {row['krw']:,}원. "
            "장부가 할인차금은 시설 합계에만 배분되어 개별 장부가는 미기재."
        ),
        amount_as_of=AS_OF,
        maturity=row["maturity"],
        interest_rate=row["rate"],
        facility_limit_krw_eok=eok(row["facility_limit_krw"]),
        facility_total_krw_eok=eok(FACILITY_GROSS),
        tranche=row["tranche"],
        exposure_status="ACTIVE_CONFIRMED",
        relationship_status="current",
        shock_eligible=True,
        verification_gap="개별 현재가치할인차금 미배분 — 표시는 표상 원금(약정=잔액)",
        evidence_quote=(
            f"{row['tranche']} {row['name']} 2030-12-11 {row['rate']} "
            f"{row['facility_limit_krw']:,} {row['krw']:,}"
        ),
    )


def historical_edge(row: dict) -> dict:
    krw_eok = eok(row["krw"])
    return base_edge(
        id=row["id"],
        source=row["source"],
        label=f"{row['name']} → 가야PFV · 시설자금(전기·차환) {krw_eok:g}억",
        impact_label=f"{row['name']} 전기 시설자금 {krw_eok:g}억 — 2025.12 차환으로 종료",
        explanation=(
            f"주석12(전기) 시설자금: 차입처 {row['name']}, 만기 {row['maturity']}, "
            f"이자율 {row['rate']}, 전기말 {krw_eok:g}억. "
            "주석(*) : 2025년 12월 기존 선순위 대출을 Term Loan A/B로 차환. "
            "현금흐름표 장기차입금 상환 1,100억과 정합."
        ),
        amount_krw_eok=krw_eok,
        amount_type="outstanding_principal_prior_period",
        amount_unit="억원",
        amount_note="전기말 잔액. 당기말 시설은 Term Loan A/B로 대체되어 현재 익스포저에서 제외.",
        amount_as_of="2024-12-31",
        maturity=row["maturity"],
        interest_rate=row["rate"],
        tranche=row["tranche"],
        exposure_status="REFINANCED",
        relationship_status="historical",
        shock_eligible=False,
        verification_gap=None,
        refinanced_into="Term Loan A/B (2025-12)",
        evidence_quote=(
            f"시설자금 {row['name']} 2026-04-20 7.30% {row['krw']:,} {row['krw']:,}"
        ),
    )


def promote_hidden(net: dict, node_id: str) -> dict | None:
    """Move a hidden institution into visible nodes if present only in hidden_nodes."""
    nodes_by = {n["id"]: n for n in net["nodes"]}
    if node_id in nodes_by:
        return nodes_by[node_id]
    hidden = net.get("hidden_nodes") or []
    for i, n in enumerate(hidden):
        if n.get("id") == node_id:
            promoted = deepcopy(n)
            promoted.pop("map_hidden", None)
            promoted["display_size"] = max(float(promoted.get("display_size") or 1), 1)
            promoted["connection_status"] = "관계 확인"
            promoted["pf_exposure_class"] = promoted.get("pf_exposure_class") or "confirmed_dc_finance"
            if "roles" in promoted and not isinstance(promoted["roles"], list):
                promoted["roles"] = []
            for key in ("key_drivers", "source_ids", "roles"):
                if key not in promoted or promoted[key] is None:
                    promoted[key] = []
                elif not isinstance(promoted[key], list):
                    promoted[key] = []
            net["nodes"].append(promoted)
            hidden.pop(i)
            net["hidden_nodes"] = hidden
            return promoted
    return None


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    # Historical counterparty lives in hidden_nodes — promote for graph visibility.
    promote_hidden(net, "shinhyup_federation")
    nodes = {n["id"]: n for n in net["nodes"]}
    edges = net["edges"]
    by_id = {e["id"]: i for i, e in enumerate(edges)}

    missing_nodes = []
    for row in CURRENT + HISTORICAL:
        if row["source"] not in nodes:
            missing_nodes.append(row["source"])
    if missing_nodes:
        raise SystemExit(f"Missing institution nodes: {missing_nodes}")

    new_edges = [current_edge(r) for r in CURRENT] + [historical_edge(r) for r in HISTORICAL]
    added, replaced = [], []
    for e in new_edges:
        if e["id"] in by_id:
            edges[by_id[e["id"]]] = e
            replaced.append(e["id"])
        else:
            edges.append(e)
            added.append(e["id"])

    # Update gaya_pfv node metadata
    g = nodes["gaya_pfv"]
    g["connection_status"] = "관계 확인"
    g["description"] = (
        "DART 법인코드 01748611. 감사보고서(2025.12) 주석12: "
        f"Term Loan A/B 원금 합계 {eok(FACILITY_GROSS):g}억 "
        f"(장부가 {eok(FACILITY_CARRYING):g}억). "
        "대주: KB국민은행·대화은행 서울지점·현대해상. "
        "전기 시설자금(신협중앙회·하나은행·하나캐피탈)은 2025.12 차환."
    )
    g["dart_borrowings_note"] = (
        f"주석12 당기: TLA KB 1,190억 + UOB서울 795억 + 현대해상 100억; "
        f"TLB 현대해상 300억; 합계 원금 2,385억 / 장부가 2,353.03억 (as_of {AS_OF}). "
        "전기 시설자금 1,100억은 차환(REFINANCED)."
    )
    g["amount_as_of"] = AS_OF
    g["source_status"] = "VERIFIED"

    # Facility-level context edge (not shock-eligible as double-count)
    fac_id = "dart_facility_gaya_term_loan_2025"
    fac = base_edge(
        id=fac_id,
        source="kb_bank",  # lead named first in table; amount is facility total context only
        target="gaya_pfv",
        relationship_type="PROJECT_LOAN",
        roles=["facility_context"],
        label=f"가야PFV Term Loan A/B 시설총액 {eok(FACILITY_GROSS):g}억 (맥락)",
        impact_label="시설총액 맥락 — 개별 대주 잔액과 합산 금지",
        explanation=(
            "주석12 소계 238,500,000,000원(할인 전). "
            "개별 대주 엣지(dart_loan_*_gaya_*)에 이미 원금이 배분되어 있으므로 "
            "본 레코드는 facility_total_context이며 shock_eligible=false."
        ),
        amount_krw_eok=eok(FACILITY_GROSS),
        amount_type="facility_total_context",
        amount_unit="억원",
        amount_note="시설 합계(할인 전). 개별 대주 익스포저와 이중계상하지 않음.",
        amount_as_of=AS_OF,
        maturity="2030-12-11",
        facility_total_krw_eok=eok(FACILITY_GROSS),
        carrying_amount_krw_eok=eok(FACILITY_CARRYING),
        exposure_status="ACTIVE_CONFIRMED",
        relationship_status="current",
        shock_eligible=False,
        exposure_kind="facility_total_context",
        verification_gap="리드 주관 여부 미기재 — 맥락 레코드의 source는 표 첫 차입처",
    )
    if fac_id in by_id:
        edges[by_id[fac_id]] = fac
        replaced.append(fac_id)
    else:
        edges.append(fac)
        added.append(fac_id)

    net["edges"] = edges
    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    recon = {
        "borrower": "가야피에프브이",
        "node_id": "gaya_pfv",
        "rcept": RCEPT,
        "reporting_date": AS_OF,
        "filing_date": "2026-04-08",
        "source_note": "주석 12 차입금",
        "pipeline_failure": (
            "opendart_borrower28_body_scan.py stopped after max_snips=12 keyword hits "
            "in the balance sheet / accounting policy section; note-12 lender table "
            "was never parsed. Integration then recorded "
            "'대주 개별 배분은 본 발췌에서 미확인' and skipped PROJECT_LOAN edges."
        ),
        "rows": [],
        "added_edge_ids": added,
        "replaced_edge_ids": replaced,
    }
    for row in CURRENT:
        recon["rows"].append({
            "source_counterparty": row["name"],
            "disclosed_amount": f"{eok(row['krw']):g}억 outstanding principal (gross)",
            "basis": "주석12 당기말 원금(=약정한도)",
            "reporting_date": AS_OF,
            "graph_entity": row["source"],
            "relationship_id": row["id"],
            "mapping_status": "mapped_active",
            "gap": None,
        })
    for row in HISTORICAL:
        recon["rows"].append({
            "source_counterparty": row["name"],
            "disclosed_amount": f"{eok(row['krw']):g}억 prior-period principal",
            "basis": "주석12 전기말 — 2025.12 차환",
            "reporting_date": "2024-12-31",
            "graph_entity": row["source"],
            "relationship_id": row["id"],
            "mapping_status": "mapped_refinanced_excluded_from_shock",
            "gap": None,
        })
    recon["rows"].append({
        "source_counterparty": "(시설 합계 / 현재가치할인차금)",
        "disclosed_amount": f"원금 {eok(FACILITY_GROSS):g}억 / 장부가 {eok(FACILITY_CARRYING):g}억",
        "basis": "주석12 소계·할인차금",
        "reporting_date": AS_OF,
        "graph_entity": "facility_context",
        "relationship_id": fac_id,
        "mapping_status": "mapped_facility_context_not_shock_eligible",
        "gap": "할인차금은 대주별 미배분",
    })
    recon["rows"].append({
        "source_counterparty": "지급보증약정 (주석(*) 문구)",
        "disclosed_amount": "undisclosed",
        "basis": "신규 금융약정에 지급보증약정 포함 — 보증인·한도 미기재",
        "reporting_date": AS_OF,
        "graph_entity": None,
        "relationship_id": None,
        "mapping_status": "unmapped",
        "gap": "보증 상대방·한도가 표에 없어 엣지 미작성",
    })

    OUT_RECON.write_text(json.dumps(recon, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK added={len(added)} replaced={len(replaced)} recon={OUT_RECON}")


if __name__ == "__main__":
    main()
