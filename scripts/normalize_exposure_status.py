#!/usr/bin/env python3
"""Normalize exposure_status on PF edges: arranger ≠ retained exposure; repaid = HISTORICAL_ONLY."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
OUT_EVIDENCE = ROOT / "docs" / "pf_exposure_evidence.json"

PAST = {"repaid", "terminated", "historical", "withdrawn", "expired", "refinanced", "transferred"}
NON_LOSS_REL = {
    "ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT",
    "ASSET_MANAGER", "TRUST_SERVICES", "PRIORITY_BENEFICIARY",
    "SUPPLIER", "CUSTOMER", "SECTOR_SUPPLY", "STRATEGIC_PARTNERSHIP",
    "PARENT_SPV", "PARENT_AFFILIATE", "ASSET_SALE", "ABS_SPONSOR",
    "HISTORICAL_FINANCING",
}
NON_LOSS_AMT = {"facility_total_context", "fee_paid", "underwrite_commitment"}
LOAN = {
    "PROJECT_LOAN", "ACQUISITION_LOAN", "CORPORATE_LOAN", "BRIDGE_LOAN",
    "DIRECT_LOAN", "MORTGAGE_LOAN", "PROJECT_FINANCE_LOAN",
}
EQUITY = {
    "EQUITY_INVESTMENT", "EQUITY_SPONSOR", "PREFERRED_EQUITY",
    "SHAREHOLDER_LOAN", "SUBORDINATED_INVESTMENT", "ABS_HOLDING",
}
GUAR = {
    "CREDIT_ENHANCEMENT", "COMPLETION_GUARANTEE", "DEBT_ASSUMPTION",
    "LOAN_GUARANTEE", "FINANCIAL_GUARANTEE", "LIQUIDITY_COMMITMENT",
    "REFINANCING_UNDERWRITE", "SHARE_PLEDGE",
}


def classify(e: dict) -> str:
    rel = e.get("relationship_type") or ""
    st = (e.get("relationship_status") or "").lower()
    amt = e.get("amount_type") or ""
    # Preserve explicit lifecycle statuses already set by integration
    existing = (e.get("exposure_status") or "").upper()
    if existing in {
        "FULLY_REPAID", "REFINANCED", "TRANSFERRED", "EXPIRED",
        "HISTORICAL_ONLY", "UNVERIFIED", "ACTIVE_CONFIRMED",
        "ACTIVE_AMOUNT_UNKNOWN", "PARTIALLY_REPAID",
    } and e.get("dart_receipt_number"):
        return existing

    if st in PAST:
        if st == "repaid":
            return "FULLY_REPAID"
        if st == "refinanced":
            return "REFINANCED"
        if st == "transferred" or st == "terminated":
            # terminated with zero balance after disposal → TRANSFERRED when flagged
            if (e.get("amount_krw_eok") == 0 or e.get("ownership_pct") == 0) and "처분" in (e.get("amount_note") or ""):
                return "TRANSFERRED"
            if st == "transferred":
                return "TRANSFERRED"
            return "HISTORICAL_ONLY"
        if st == "expired":
            return "EXPIRED"
        return "HISTORICAL_ONLY"
    if amt in NON_LOSS_AMT:
        # Arrangement / facility headline / fee — never treated as retained outstanding
        return "HISTORICAL_ONLY"
    if rel in NON_LOSS_REL:
        return "HISTORICAL_ONLY" if rel in {"ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT"} else "ACTIVE_AMOUNT_UNKNOWN"
    if rel in LOAN or rel in EQUITY:
        if e.get("amount_krw_eok") is not None and amt in {
            "outstanding", "institution_commitment", "equity_paid_in",
            "equity_investment", "historical_outstanding",
        }:
            # historical_outstanding without current confirmation → unverified for loss
            if amt == "historical_outstanding" and st not in {"funded", "current", "committed", "operating"}:
                return "UNVERIFIED"
            if amt == "historical_outstanding":
                return "ACTIVE_AMOUNT_UNKNOWN"
            return "ACTIVE_CONFIRMED"
        return "ACTIVE_AMOUNT_UNKNOWN" if st in {"funded", "current", "committed", "operating", "unknown", ""} else "UNVERIFIED"
    if rel in GUAR or e.get("contingent_obligation"):
        return "ACTIVE_AMOUNT_UNKNOWN"
    if e.get("impact_channel") == "financial":
        return "UNVERIFIED"
    return "HISTORICAL_ONLY"


def main() -> None:
    data = json.loads(NET.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    evidence = []
    for e in data["edges"]:
        status = classify(e)
        e["exposure_status"] = status
        # Informational arranger edges: keep on relationship graph, exclude from active loss
        amt = e.get("amount_type") or ""
        rel = e.get("relationship_type") or ""
        if rel in NON_LOSS_REL or amt in NON_LOSS_AMT or status in {
            "HISTORICAL_ONLY", "FULLY_REPAID", "REFINANCED", "TRANSFERRED", "EXPIRED", "UNVERIFIED",
        }:
            e["shock_eligible"] = False
            note = e.get("amount_note") or ""
            if rel in {"ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT"} or amt in NON_LOSS_AMT:
                if "보유 익스포저 아님" not in note:
                    e["amount_note"] = (note + " · 주선·인수·시설총액 ≠ 보유 익스포저").strip(" ·")
        else:
            e["shock_eligible"] = status in {
                "ACTIVE_CONFIRMED", "ACTIVE_AMOUNT_UNKNOWN", "PARTIALLY_REPAID",
            } and rel not in NON_LOSS_REL
        counts[status] = counts.get(status, 0) + 1
        if e.get("source_url") or e.get("source_title"):
            evidence.append({
                "edge_id": e.get("id"),
                "relationship_type": e.get("relationship_type"),
                "exposure_status": status,
                "amount_type": e.get("amount_type"),
                "amount_krw_eok": e.get("amount_krw_eok"),
                "source_title": e.get("source_title"),
                "source_url": e.get("source_url"),
                "source_date": e.get("source_date"),
                "project_id": e.get("project_id"),
            })
    NET.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    OUT_EVIDENCE.write_text(json.dumps({
        "verification_date": "2026-10-21",
        "edge_count": len(data["edges"]),
        "exposure_status_counts": counts,
        "evidence_rows": evidence,
        "note": "Partial reconciliation from existing network metadata; DART full-text audit incomplete without API key.",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("updated", NET)
    print("counts", counts)
    print("evidence", OUT_EVIDENCE, len(evidence))


if __name__ == "__main__":
    main()
