#!/usr/bin/env python3
"""Validate AI DC PF finance-first expansion: no zero-for-unknown, no syndicate double-count."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

PF = Path(__file__).resolve().parents[1] / "frontend" / "public" / "data" / "pf"


def main() -> None:
    net = json.loads((PF / "network.json").read_text(encoding="utf-8"))
    proj = json.loads((PF / "projects.json").read_text(encoding="utf-8"))
    by = {n["id"]: n for n in net["nodes"]}
    edges = net["edges"]

    checks = []
    fin = [
        e
        for e in edges
        if e.get("impact_channel") == "financial"
        or e.get("relationship_type")
        in (
            "PROJECT_LOAN",
            "CREDIT_ENHANCEMENT",
            "ARRANGER",
            "EQUITY_INVESTMENT",
            "EQUITY_SPONSOR",
            "REFINANCING_UNDERWRITE",
            "PREFERRED_EQUITY",
        )
    ]

    # Unknown must never be stored as zero
    zero_bad = [
        e["id"]
        for e in fin
        if e.get("amount_krw_eok") == 0
        and ("미공개" in (e.get("amount_note") or "") or e.get("amount_type") == "institution_commitment")
    ]
    checks.append(("no_zero_for_undisclosed", len(zero_bad) == 0, zero_bad[:5]))

    # Magna lenders must not each carry 2730
    magna = [e for e in edges if e.get("project_id") == "magna_deogi" and e.get("relationship_type") == "PROJECT_LOAN"]
    magna_bad = [e["id"] for e in magna if e.get("amount_krw_eok") == 2730]
    checks.append(("magna_no_full_facility_per_lender", len(magna_bad) == 0, magna_bad))
    checks.append(("magna_named_lenders_ge_8", len(magna) >= 8, len(magna)))

    # Casequare lenders have institution amounts
    case = [e for e in edges if e.get("project_id") == "casequare_gasan" and e.get("relationship_type") == "PROJECT_LOAN"]
    case_with_amt = [e for e in case if e.get("amount_krw_eok")]
    checks.append(("casequare_lenders_with_amounts", len(case_with_amt) >= 10, len(case_with_amt)))

    # Multi-project institution
    by_inst = defaultdict(set)
    for e in fin:
        for nid in (e["source"], e["target"]):
            if by.get(nid, {}).get("group") in (
                "kr_bank",
                "kr_securities",
                "kr_insurance",
                "kr_am",
                "kr_savings",
                "kr_cooperative",
                "kr_construction",
                "financial",
            ):
                pid = e.get("project_id")
                if pid:
                    by_inst[nid].add(pid)
    multi = {k: sorted(v) for k, v in by_inst.items() if len(v) >= 2}
    checks.append(("institution_across_projects", len(multi) >= 3, {k: v for k, v in list(multi.items())[:8]}))

    # Camsquare securitization path
    has_spc = any(e["id"] == "pf_camsquare_first_to_pfv" for e in edges)
    has_support = any(e["id"] == "pf_samsung_camsquare_abstb_support" for e in edges)
    checks.append(("camsquare_abstb_path", has_spc and has_support, {"spc": has_spc, "support": has_support}))

    # Yuanta credit support for Casequare ABS
    has_yuanta = any(
        e["source"] == "yuanta_sec"
        and e["target"] == "mountain_rich"
        and e.get("relationship_type") == "CREDIT_ENHANCEMENT"
        for e in edges
    )
    checks.append(("yuanta_mountain_credit_support", has_yuanta, has_yuanta))

    # Contractor contingent vs funded
    daewoo = next((e for e in edges if e["id"] == "pf_daewoo_fine_guar"), None)
    checks.append(
        (
            "daewoo_contingent_guarantee",
            bool(daewoo and daewoo.get("contingent_obligation") and daewoo.get("amount_type") == "guarantee_limit"),
            daewoo.get("amount_type") if daewoo else None,
        )
    )

    # Undisclosed amount present
    und = [e for e in fin if e.get("amount_krw_eok") is None and "미공개" in (e.get("amount_note") or "")]
    checks.append(("undisclosed_amount_edges", len(und) >= 5, len(und)))

    # Kiwoom underwrite not treated as funded loan type
    kiw = next((e for e in edges if e["id"] == "pf_kiwoom_refin"), None)
    checks.append(
        (
            "kiwoom_underwrite_typed",
            bool(kiw and kiw.get("amount_type") == "underwrite_commitment"),
            kiw.get("amount_type") if kiw else None,
        )
    )

    # Type / stage breakdown
    by_group = Counter()
    for nid, pids in by_inst.items():
        by_group[by[nid]["group"]] += 1
    by_stage = Counter(e.get("financing_stage") or "unset" for e in fin)
    by_amt = Counter(e.get("amount_type") or "unset" for e in fin)

    report = {
        "checks": [{ "id": a, "ok": b, "detail": c } for a, b, c in checks],
        "passed": all(b for _, b, _ in checks),
        "counts": {
            "nodes": len(net["nodes"]),
            "edges": len(edges),
            "financial_edges": len(fin),
            "institutions_with_finance_edges": len(by_inst),
            "projects_financing_disclosed": sum(1 for p in proj["projects"] if p.get("financing_disclosed")),
            "magna_lenders": len(magna),
            "casequare_loan_edges": len(case),
        },
        "by_institution_group": dict(by_group),
        "by_financing_stage": dict(by_stage),
        "by_amount_type": dict(by_amt),
        "multi_project_institutions_sample": {k: v for k, v in list(multi.items())[:12]},
    }
    out = PF / "_finance_validation_v5.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASSED" if report["passed"] else "FAILED")
    for c in report["checks"]:
        print(("OK" if c["ok"] else "FAIL"), c["id"], c["detail"] if not c["ok"] else "")
    print(json.dumps(report["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
