#!/usr/bin/env python3
"""Replace dck1 commitment-style edges with 당기말 outstanding from note 11.

rcept 20260410002975, 단위:천원. Prior Tranche A/B/C 당기말 = 0 (refinanced).
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend/public/data/pf/network.json"

RCEPT = "20260410002975"
TITLE = "디씨케이원 감사보고서 (2025.12)"
AS_OF = "2025-12-31"
VERIFY = "2026-10-22"


def eok(cheonwon: int) -> float:
    # 천원 → 억원: 100,000천원 = 1억
    return round(cheonwon / 100_000, 4)


# Per-lender 당기말 (천원) = Tranche1 + Tranche2 outstanding
LENDERS = [
    ("dart_loan_ibk_dck1_t1", "ibk_bank", "중소기업은행", 110_000_000, "Tranche 1", "5.20%"),
    ("dart_loan_kdb_dck1_t1", "kdb", "한국산업은행", 110_000_000, "Tranche 1", "5.20%"),
    ("dart_loan_db_ins_dck1_t1", "db_ins", "디비손해보험", 71_500_000, "Tranche 1", "5.20%"),
    ("dart_loan_hyundai_marine_dck1_t1", "hyundai_marine", "현대해상화재보험", 27_500_000, "Tranche 1", "5.20%"),
    ("dart_loan_kb_ins_dck1_t1", "kb_ins", "케이비손해보험", 24_750_000, "Tranche 1", "5.20%"),
    ("dart_loan_kb_bank_dck1_t1", "kb_bank", "국민은행", 19_250_000, "Tranche 1", "5.20%"),
    ("dart_loan_ibk_capital_dck1_t1", "ibk_capital", "아이비케이캐피탈", 13_750_000, "Tranche 1", "5.20%"),
    ("dart_loan_ing_dck1_t1", "ing_bank", "아이엔지은행", 35_750_000, "Tranche 1", "CD+2.1%"),
    ("dart_loan_ca_cib_dck1_t1", "ca_cib", "크레디아그리콜", 27_500_000, "Tranche 1", "CD+2.1%"),
    ("dart_loan_ibk_dck1_t2", "ibk_bank", "중소기업은행", 15_500_000, "Tranche 2", "5.20%"),
    ("dart_loan_kdb_dck1_t2", "kdb", "한국산업은행", 15_500_000, "Tranche 2", "5.20%"),
    ("dart_loan_db_ins_dck1_t2", "db_ins", "디비손해보험", 10_100_000, "Tranche 2", "5.20%"),
    ("dart_loan_hyundai_marine_dck1_t2", "hyundai_marine", "현대해상화재보험", 3_900_000, "Tranche 2", "5.20%"),
    ("dart_loan_kb_ins_dck1_t2", "kb_ins", "케이비손해보험", 3_500_000, "Tranche 2", "5.20%"),
    ("dart_loan_kb_bank_dck1_t2", "kb_bank", "국민은행", 2_700_000, "Tranche 2", "5.20%"),
    ("dart_loan_ibk_capital_dck1_t2", "ibk_capital", "아이비케이캐피탈", 1_900_000, "Tranche 2", "5.20%"),
    ("dart_loan_ing_dck1_t2", "ing_bank", "아이엔지은행", 5_000_000, "Tranche 2", "CD+2.1%"),
    ("dart_loan_ca_cib_dck1_t2", "ca_cib", "크레디아그리콜", 3_900_000, "Tranche 2", "CD+2.1%"),
]


def edge(eid, src, name, cheon, tranche, rate):
    krw_eok = eok(cheon)
    return {
        "id": eid,
        "source": src,
        "target": "dck1",
        "relationship_type": "PROJECT_LOAN",
        "roles": ["lender"],
        "source_ids": [f"dart_audit_dck1_{RCEPT}"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_krw_eok": krw_eok,
        "amount_type": "outstanding_principal",
        "amount_unit": "억원",
        "amount_note": f"주석11 당기말 {tranche} {name} {cheon:,}천원",
        "amount_as_of": AS_OF,
        "impact_channel": "financial",
        "source_status": "VERIFIED",
        "label": f"{name} → dck1 · {krw_eok:g}억",
        "impact_label": f"{name} 당기말 {krw_eok:g}억",
        "explanation": f"주석11 당기말 {tranche} {name} {cheon:,}천원 (약정≠잔액; Tr.2는 일부인출)",
        "transmission_class": "direct",
        "exposure_status": "ACTIVE_CONFIRMED",
        "relationship_status": "current",
        "shock_eligible": True,
        "layer": "fact",
        "evidence_kind": "dart_audit_note",
        "evidence_status": "DART 감사보고서 차입금 주석 당기말",
        "evidence_level": "company_filing",
        "participation_path": "직접 대출",
        "participation_directness": "direct",
        "contingent_obligation": False,
        "source_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={RCEPT}",
        "source_title": TITLE,
        "source_date": "2026-04-10",
        "dart_receipt_number": RCEPT,
        "verification_date": VERIFY,
        "maturity": "2029-07-14",
        "interest_rate": rate,
        "financing_stage": "main_pf",
        "tranche": tranche,
        "stress_direction": "차주 부실 → 대주 신용 익스포저",
        "exposure_kind": "loan_principal_outstanding",
        "period_basis": "current_period_당기말",
    }


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    edges = net["edges"]
    by_id = {e["id"]: i for i, e in enumerate(edges)}
    src_id = f"dart_audit_dck1_{RCEPT}"
    if not any(s.get("id") == src_id for s in net.get("sources") or []):
        net.setdefault("sources", []).append({
            "id": src_id, "title": TITLE, "publisher": "DART",
            "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={RCEPT}",
            "kind": "filing", "dart_receipt_number": RCEPT,
            "used_for": "차입금 주석 당기말",
        })

    added = []
    for row in LENDERS:
        e = edge(*row)
        if e["id"] in by_id:
            edges[by_id[e["id"]]] = e
        else:
            edges.append(e)
            by_id[e["id"]] = len(edges) - 1
            added.append(e["id"])

    demoted = []
    for e in edges:
        if e.get("target") == "dck1" and str(e.get("id", "")).startswith("v6_dk_pf_"):
            e["exposure_status"] = "SUPERSEDED_BY_DART_AUDIT"
            e["shock_eligible"] = False
            e["verification_gap"] = (
                "v6 약정/커밋먼트 합계를 잔액처럼 사용 — 주석11 당기말 잔액은 dart_loan_*_dck1_* 로 대체"
            )
            demoted.append(e["id"])

    net["edges"] = edges
    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("added", len(added), "demoted", len(demoted))
    # sanity: sum
    s = sum(eok(x[3]) for x in LENDERS)
    print("sum_당기말_억", s, "expected ~5020")


if __name__ == "__main__":
    main()
