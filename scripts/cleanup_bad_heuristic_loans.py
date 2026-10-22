#!/usr/bin/env python3
"""Remove auto-heuristic PROJECT_LOAN edges that assigned facility totals / dual-column noise.

Keeps curated IDs from patch_gaya_borrowings / patch_borrowings_from_notes.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
COV = ROOT / "docs" / "pfv_borrowings_coverage.json"

KEEP_PREFIXES = (
    "dart_loan_kb_gaya_",
    "dart_loan_ubob_gaya_",
    "dart_loan_hyundai_marine_gaya_",
    "dart_loan_shinhyup_gaya_",
    "dart_loan_hana_bank_gaya_",
    "dart_loan_hana_capital_gaya_",
    "dart_facility_gaya_",
    "dart_loan_ibk_dito_",
    "dart_loan_kdb_dito_",
    "dart_loan_ibk_capital_busan_",
    "dart_loan_kb_ins_edgecore",
    "dart_loan_hyundai_marine_edgecore",
    "dart_loan_shinhan_capital_keppel_",
    "dart_loan_shinhan_sec_keppel_",
    "dart_loan_shinhan_capital_cheongna",
    "dart_loan_shinhan_sec_cheongna",
    "dart_loan_kb_magna",
    "dart_loan_shinhan_magna",
    "dart_loan_hana_magna",
    "dart_loan_ibk_magna",
    "dart_facility_keppel_ansan_",
    "dart_eq_",  # equity edges
)


def keep(eid: str) -> bool:
    return any(eid.startswith(p) for p in KEEP_PREFIXES)


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    cov = json.loads(COV.read_text(encoding="utf-8")) if COV.exists() else {}
    heuristic_ids = set(cov.get("edges_added") or []) | set(cov.get("edges_replaced") or [])

    before = len(net["edges"])
    kept, removed = [], []
    for e in net["edges"]:
        eid = e.get("id") or ""
        # Remove heuristic dart_loan_* with period_basis current_period_only from inventory script
        is_heuristic = (
            eid in heuristic_ids
            or e.get("period_basis") == "current_period_only"
            or (
                eid.startswith("dart_loan_")
                and e.get("evidence_status") == "DART 감사보고서 차입금 주석 당기말"
                and not keep(eid)
            )
        )
        if is_heuristic and not keep(eid):
            removed.append(eid)
            continue
        kept.append(e)

    net["edges"] = kept
    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"edges {before} -> {len(kept)} removed={len(removed)}")


if __name__ == "__main__":
    main()
