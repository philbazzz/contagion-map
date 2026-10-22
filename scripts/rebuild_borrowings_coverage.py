#!/usr/bin/env python3
"""Rebuild honest coverage table from inventory + live network edges + extract cache."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
INV = ROOT / "docs" / "pfv_spv_inventory.json"
RESOLVE = ROOT / "docs" / "opendart_pfv_resolve_fetch.json"
OUT = ROOT / "docs" / "pfv_borrowings_coverage.json"
OUT_MD = ROOT / "docs" / "PFV_BORROWINGS_COVERAGE.md"


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    inv = json.loads(INV.read_text(encoding="utf-8"))
    resolve = {r["id"]: r for r in (json.loads(RESOLVE.read_text(encoding="utf-8")).get("results") if RESOLVE.exists() else [])}

    # Rebuild inventory stamp from network
    items = inv.get("items") or []
    # refresh rcept from nodes
    node_by = {n["id"]: n for n in net["nodes"]}
    for it in items:
        n = node_by.get(it["id"])
        if n and n.get("dart_last_audit_rcept"):
            it["dart_last_audit_rcept"] = n["dart_last_audit_rcept"]
            it["dart_corp_code"] = n.get("dart_corp_code") or it.get("dart_corp_code")
        rr = resolve.get(it["id"])
        if rr and rr.get("rcept_no"):
            it["dart_last_audit_rcept"] = rr["rcept_no"]
            it["report_nm"] = rr.get("report_nm") or it.get("report_nm")

    coverage = []
    by_status = {}
    for it in items:
        nid = it["id"]
        rcept = it.get("dart_last_audit_rcept")
        loans = [
            e for e in net["edges"]
            if e.get("target") == nid
            and e.get("relationship_type") == "PROJECT_LOAN"
            and str(e.get("exposure_status", "")).startswith("ACTIVE")
            and e.get("amount_type") != "facility_total_context"
            and not e.get("facility_total_context")
            and "facility_context" not in (e.get("roles") or [])
        ]
        zip_ok = bool(rcept) and (ROOT / "backend/data/opendart_cache/docs" / f"{rcept}.zip").exists()

        dart_verified_loans = [
            e for e in loans
            if e.get("period_basis") == "current_period_당기말"
            or str(e.get("id", "")).startswith("dart_loan_")
            or e.get("evidence_kind") == "dart_audit_note"
            or e.get("dart_receipt_number")
        ]
        if dart_verified_loans:
            loans = dart_verified_loans
            status = "Reviewed and mapped"
            note_reviewed = True
        elif loans and zip_ok:
            # Edges exist from secondary sources but latest audit 당기말 not hand-verified
            status = "Latest report lacks sufficient detail"
            note_reviewed = False
            loans = []  # do not claim mapped from unverified secondary edges
        elif loans and not zip_ok:
            # Named lenders from press/other; no current audit in hand
            status = "Report unavailable"
            note_reviewed = False
            loans = []
        elif nid.startswith("seed:") or it.get("visibility") == "no_map_node":
            status = "Report unavailable"
            note_reviewed = False
        elif not rcept or not zip_ok:
            # US / unnamed / no DART
            name = it.get("name") or ""
            if any(x in name for x in ("LLC", "Helios", "Finance I", "ELN", "미공개", "미확인")):
                status = "Report unavailable"
            elif (it.get("region") or "") not in ("KR", None, "") and not any("\uac00" <= c <= "\ud7a3" for c in name):
                status = "Report unavailable"
            else:
                status = "Report unavailable"
            note_reviewed = False
        else:
            # have report — check if note likely present without claiming mapped
            status = "Latest report lacks sufficient detail"
            note_reviewed = False
            # special known: gasan no audit body borrowings etc.
            rr = resolve.get(nid) or {}
            if rr.get("status") == "no_usable_filing" or rr.get("status") == "no_audit_in_list":
                status = "Report unavailable"
            elif rr.get("report_nm") and "감사" not in (rr.get("report_nm") or "") and "보고서" in (rr.get("report_nm") or ""):
                status = "Latest report lacks sufficient detail"

        # Hand-reviewed: latest note shows 당기말 outstanding = 0 / none.
        # ansan_green_energy_pfv was wrongly listed here previously (has 주석5 장기차입금).
        NO_OUTSTANDING = {
            "blueribbon_dev",  # 주석6 단기차입금 당기말 전부 -
            "koramco_siheung_pfv",  # 당기말 차입부채 없음 명시
        }
        if nid in NO_OUTSTANDING and not loans:
            status = "Reviewed — no outstanding borrowings disclosed"
            note_reviewed = True
        # seed:b28 하양에너지발전 — note6 has related-party 단기차입금 but entity is
        # energy-gen seed (no_map_node), not confirmed DC PFV; do not claim mapped.
        seed_b28_gap = None
        if nid == "seed:b28":
            status = "Report unavailable"
            note_reviewed = True
            seed_b28_gap = (
                "주석6 당기말 단기차입금 44.5억(관련당사자) 확인했으나 "
                "DC PFV 미확정·맵 노드 없음(visibility=no_map_node)"
            )

        row = {
            "pfv_spc": it.get("name"),
            "node_id": nid,
            "visibility": it.get("visibility"),
            "latest_report_reviewed": it.get("report_nm") or (f"rcept {rcept}" if rcept else None),
            "reporting_date": "2025-12-31" if rcept and loans else (it.get("reporting_date")),
            "filing_date": it.get("rcept_dt"),
            "borrowings_note_reviewed": note_reviewed or bool(loans),
            "named_lenders_found": [
                f"{e.get('source')} ({e.get('amount_krw_eok')}억)" for e in loans
            ],
            "relationships_mapped": [e["id"] for e in loans],
            "unresolved_gaps": [],
            "status": status,
        }
        if status == "Report unavailable" and not rcept:
            row["unresolved_gaps"].append("DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인)")
        if status == "Latest report lacks sufficient detail":
            row["unresolved_gaps"].append("보고서 확보됐으나 당기말 대주 행 단위 확정 매핑 미완 또는 차입처 미기재")
        if seed_b28_gap:
            row["unresolved_gaps"] = [seed_b28_gap]
            row["latest_report_reviewed"] = "하양에너지발전 감사보고서 (2025.12)"
            row["reporting_date"] = "2025-12-31"
        coverage.append(row)
        by_status[status] = by_status.get(status, 0) + 1

    # Fix reporting dates for mapped from edges
    for row in coverage:
        if row["relationships_mapped"]:
            e0 = next(e for e in net["edges"] if e["id"] == row["relationships_mapped"][0])
            row["reporting_date"] = e0.get("amount_as_of") or row["reporting_date"]
            row["latest_report_reviewed"] = e0.get("source_title") or row["latest_report_reviewed"]
            row["status"] = "Reviewed and mapped"
            row["borrowings_note_reviewed"] = True

    by_status = {}
    for row in coverage:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1

    payload = {
        "verification_date": "2026-10-22",
        "inventory_count": len(items),
        "coverage_count": len(coverage),
        "by_status": by_status,
        "policy": [
            "당기말 only for ACTIVE exposure",
            "전기말 never presented as current",
            "facility totals not assigned to each syndicate member",
            "unnamed groups remain facility_context",
            "honest gaps: unavailable vs unnamed vs not yet carefully mapped",
        ],
        "coverage": coverage,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# PFV/SPC Borrowings Coverage",
        "",
        f"- Verification date: **2026-10-22**",
        f"- Inventory: **{len(items)}** entities (visible + hidden + unresolved seeds)",
        f"- Status counts: `{json.dumps(by_status, ensure_ascii=False)}`",
        "",
        "## Critical correction — 안산그린에너지피에프브이",
        "",
        "Previously mis-labeled as “no outstanding borrowings.” Audit `20260406003916` 주석5 "
        "장기차입금 discloses **당기말 104,000,000천원 (1,040억)** across **17 named lenders**. "
        "Pipeline failure: note never written to `network.json` + false hard-coded coverage status. "
        "Now mapped as `dart_loan_*_ansan_green_*`. Row-by-row: "
        "`docs/ansan_green_borrowings_reconciliation.json`. Source sweep: "
        "`docs/pfv_source_vs_graph_audit.json`.",
        "",
        "| PFV/SPC | Latest report | Reporting date | Note reviewed | Named lenders (current) | Mapped relationships | Status | Gaps |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(coverage, key=lambda x: x.get("node_id") or ""):
        lenders = ", ".join(r["named_lenders_found"][:8]) or "—"
        if len(r["named_lenders_found"]) > 8:
            lenders += f" …(+{len(r['named_lenders_found'])-8})"
        gaps = "; ".join(r["unresolved_gaps"]) or "—"
        lines.append(
            f"| {r['pfv_spc']} (`{r['node_id']}`) | {r['latest_report_reviewed'] or '—'} | "
            f"{r['reporting_date'] or '—'} | {'Y' if r['borrowings_note_reviewed'] else 'N'} | "
            f"{lenders} | {len(r['relationships_mapped'])} | {r['status']} | {gaps} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(by_status, ensure_ascii=True))
    print("wrote", str(OUT_MD))


if __name__ == "__main__":
    main()
