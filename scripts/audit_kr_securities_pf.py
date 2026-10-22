#!/usr/bin/env python3
"""Audit Korean securities firms vs PF network + optional OpenDART status.

Does NOT invent relationships. Writes DATA_CENTER_PF_AUDIT.md and JSON evidence.
"""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
PROJ = ROOT / "frontend" / "public" / "data" / "pf" / "projects.json"
OUT_MD = ROOT / "DATA_CENTER_PF_AUDIT.md"
OUT_JSON = ROOT / "docs" / "DATA_CENTER_PF_AUDIT.json"

# Mandatory starting list (Part 2.1) — presence in list ≠ confirmed exposure
MANDATORY_SECURITIES = [
    ("한국투자증권", ["hankook_inv_sec", "korea_inv_sec", "kis", "han_tu_sec"]),
    ("KB증권", ["kb_sec"]),
    ("메리츠증권", ["meritz_sec"]),
    ("NH투자증권", ["nh_inv_sec", "nh_sec"]),
    ("미래에셋증권", ["mirae_asset_sec", "mirae_sec"]),
    ("삼성증권", ["samsung_sec"]),
    ("신한투자증권", ["shinhan_inv_sec", "shinhan_sec"]),
    ("하나증권", ["hana_sec"]),
    ("대신증권", ["daishin_sec"]),
    ("키움증권", ["kiwoom_sec"]),
    ("IBK투자증권", ["ibk_sec"]),
    ("현대차증권", ["hyundai_motor_sec", "hyundai_sec"]),
    ("SK증권", ["sk_sec"]),
    ("교보증권", ["kyobo_sec"]),
    ("유안타증권", ["yuanta_sec"]),
    ("한화투자증권", ["hanwha_inv_sec", "hanwha_sec"]),
    ("다올투자증권", ["daol_sec"]),
    ("LS증권", ["ls_sec"]),
    ("신영증권", ["shinyoung_sec"]),
    ("DB증권", ["db_sec"]),
    ("유진투자증권", ["eugene_sec"]),
    ("iM증권", ["im_sec"]),
    ("BNK투자증권", ["bnk_sec"]),
    ("부국증권", ["bookook_sec"]),
    ("케이프투자증권", ["cape_sec"]),
]

PAST = {"repaid", "terminated", "historical", "withdrawn", "expired", "refinanced", "transferred",
        "FULLY_REPAID", "REFINANCED", "TRANSFERRED", "EXPIRED", "HISTORICAL_ONLY"}
ARRANGE = {"ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT"}


def find_node(nodes: list[dict], name: str, aliases: list[str]) -> dict | None:
    for n in nodes:
        if n.get("id") in aliases:
            return n
        ko = n.get("name_ko") or ""
        en = (n.get("name") or "").lower()
        if name in ko or any(a.replace("_", " ") in en for a in aliases):
            return n
    return None


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    projects = []
    if PROJ.exists():
        pf = json.loads(PROJ.read_text(encoding="utf-8"))
        projects = pf.get("projects") or pf if isinstance(pf, list) else pf.get("projects", [])

    nodes = net["nodes"]
    edges = net["edges"]
    today = date.today().isoformat()
    key_set = bool((os.environ.get("OPEN_DART_API_KEY") or "").strip())
    # Also peek backend/.env without printing value
    env_path = ROOT / "backend" / ".env"
    if env_path.exists() and not key_set:
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("OPEN_DART_API_KEY=") and line.split("=", 1)[1].strip():
                key_set = True
                break

    firm_rows = []
    confirmed_active = []
    historical = []
    unknown_balances = []
    missing_firms = []

    for name, aliases in MANDATORY_SECURITIES:
        node = find_node(nodes, name, aliases)
        if not node:
            missing_firms.append(name)
            firm_rows.append({
                "legal_name": name,
                "in_map": False,
                "node_id": None,
                "edges": 0,
                "active_economic": 0,
                "arranger_only": 0,
                "repaid_or_historical": 0,
                "notes": "맵에 노드 없음 — DART 공시 조사 대기 (관계 미생성)",
            })
            continue
        links = [e for e in edges if e["source"] == node["id"] or e["target"] == node["id"]]
        active_econ = []
        arr_only = []
        hist = []
        for e in links:
            st = e.get("exposure_status") or e.get("relationship_status") or ""
            rel = e.get("relationship_type") or ""
            past = st in PAST or st.upper() in PAST
            if rel in ARRANGE or e.get("shock_eligible") is False:
                arr_only.append(e)
                historical.append({"firm": name, "edge_id": e.get("id"), "role": rel, "status": st})
            elif past:
                hist.append(e)
                historical.append({"firm": name, "edge_id": e.get("id"), "role": rel, "status": st})
            else:
                active_econ.append(e)
                confirmed_active.append({
                    "firm": name,
                    "edge_id": e.get("id"),
                    "role": rel,
                    "amount_krw_eok": e.get("amount_krw_eok"),
                    "amount_type": e.get("amount_type"),
                    "exposure_status": e.get("exposure_status"),
                    "project_id": e.get("project_id"),
                    "source_url": e.get("source_url"),
                })
                if e.get("amount_krw_eok") is None and rel not in ARRANGE:
                    unknown_balances.append({"firm": name, "edge_id": e.get("id"), "role": rel})
        firm_rows.append({
            "legal_name": name,
            "in_map": True,
            "node_id": node["id"],
            "edges": len(links),
            "active_economic": len(active_econ),
            "arranger_only": len(arr_only),
            "repaid_or_historical": len(hist),
            "notes": "",
        })

    extra_sec = [
        n for n in nodes
        if n.get("group") == "kr_securities"
        and n["id"] not in {r["node_id"] for r in firm_rows if r["node_id"]}
    ]

    payload = {
        "verification_date": today,
        "audit_complete": False,
        "opendart_api_configured": key_set,
        "filings_inspected": 0,
        "reporting_periods": "2018–latest (planned; API key required for live pull)",
        "securities_firms_reviewed": firm_rows,
        "additional_securities_in_map": [
            {"id": n["id"], "name_ko": n.get("name_ko"), "name": n.get("name")} for n in extra_sec
        ],
        "confirmed_active_relationships": confirmed_active,
        "historical_or_arranger_relationships": historical,
        "unknown_balances": unknown_balances,
        "missing_from_map": missing_firms,
        "projects_in_database": len(projects),
        "network_nodes": len(nodes),
        "network_edges": len(edges),
        "limitations": [
            "OPEN_DART_API_KEY unset or empty → live DART full-text / notes search not executed this run.",
            "Existing edges remain news/DART-metadata sourced; arrangement amounts are tagged HISTORICAL_ONLY / shock_eligible=false.",
            "Absence from latest disclosure is NOT treated as repayment (Case E → UNVERIFIED).",
            "No fabricated lender shares from facility totals.",
        ],
        "remaining_work": [
            "Set OPEN_DART_API_KEY and run disclosure keyword crawl for all 25+ firms (2018–latest).",
            "Reconcile bridge→mortgage refinancing successor creditors with explicit evidence.",
            "Cross-check borrower/SPC filings for each ACTIVE_AMOUNT_UNKNOWN loan.",
            f"Investigate missing firms: {', '.join(missing_firms) if missing_firms else '(none)'}",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# DATA CENTER PF AUDIT",
        "",
        f"**Verification date:** {today}",
        f"**Audit complete:** NO (partial — see limitations)",
        f"**OpenDART API configured:** {'yes' if key_set else 'no'}",
        f"**Filings inspected (live):** {payload['filings_inspected']}",
        f"**Network:** {len(nodes)} nodes / {len(edges)} edges · projects file: {len(projects)}",
        "",
        "## Securities firms reviewed (mandatory list)",
        "",
        "| Firm | In map | Node | Edges | Active economic | Arranger-only | Historical/repaid |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for r in firm_rows:
        lines.append(
            f"| {r['legal_name']} | {'Y' if r['in_map'] else 'N'} | {r['node_id'] or '—'} | "
            f"{r['edges']} | {r['active_economic']} | {r['arranger_only']} | {r['repaid_or_historical']} |"
        )
    lines += [
        "",
        "## Classification rules applied",
        "",
        "- Arranger / underwriting / facility_total_context → **not** current credit exposure; `shock_eligible=false`.",
        "- `repaid` / `terminated` / `historical` → FULLY_REPAID or HISTORICAL_ONLY; excluded from loss propagation.",
        "- Missing outstanding balance → ACTIVE_AMOUNT_UNKNOWN or UNVERIFIED; never invent 0 or market-share fill.",
        "",
        f"## Confirmed active economic relationships (map metadata): {len(confirmed_active)}",
        "",
    ]
    for row in confirmed_active[:80]:
        amt = row["amount_krw_eok"]
        amt_s = f"{amt}억" if amt is not None else "미확인"
        lines.append(
            f"- **{row['firm']}** · {row['role']} · {amt_s} · status={row.get('exposure_status')} · "
            f"project={row.get('project_id')} · edge=`{row['edge_id']}`"
        )
    if len(confirmed_active) > 80:
        lines.append(f"- … +{len(confirmed_active) - 80} more (see JSON)")

    lines += [
        "",
        f"## Historical / arranger (informational): {len(historical)}",
        f"## Unknown balances flagged: {len(unknown_balances)}",
        f"## Missing from map (no node): {len(missing_firms)}",
        "",
    ]
    if missing_firms:
        lines.append("Firms without graph nodes (investigation pending, **no edges invented**):")
        for m in missing_firms:
            lines.append(f"- {m}")
        lines.append("")

    if extra_sec:
        lines.append("## Additional securities already in map")
        for n in extra_sec:
            lines.append(f"- {n.get('name_ko') or n.get('name')} (`{n['id']}`)")
        lines.append("")

    lines += [
        "## Limitations",
        "",
    ]
    for L in payload["limitations"]:
        lines.append(f"- {L}")
    lines += ["", "## Remaining work", ""]
    for L in payload["remaining_work"]:
        lines.append(f"- {L}")
    lines += [
        "",
        "## Machine-readable evidence",
        "",
        f"- `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        f"- `docs/pf_exposure_evidence.json` (per-edge source links after normalize_exposure_status.py)",
        "",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", OUT_MD)
    print("wrote", OUT_JSON)
    print("missing", missing_firms)
    print("active", len(confirmed_active), "hist", len(historical), "unknown", len(unknown_balances))


if __name__ == "__main__":
    main()
