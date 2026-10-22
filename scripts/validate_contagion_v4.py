#!/usr/bin/env python3
"""Validation checks for Contagion Map data integrity (v4 expansion)."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend" / "public" / "data"
PF = PUBLIC / "pf"

errors: list[str] = []
warns: list[str] = []


def main() -> int:
    semi = json.loads((PUBLIC / "network.json").read_text(encoding="utf-8"))
    pf = json.loads((PF / "network.json").read_text(encoding="utf-8"))
    projects = json.loads((PF / "projects.json").read_text(encoding="utf-8"))
    elig = json.loads((PUBLIC / "_us_mcap_eligibility.json").read_text(encoding="utf-8"))

    # Duplicate entity ids
    for label, nodes in (("semi", semi["nodes"]), ("pf", pf["nodes"])):
        c = Counter(n["id"] for n in nodes)
        dups = [i for i, n in c.items() if n > 1]
        if dups:
            errors.append(f"{label} duplicate ids: {dups[:10]}")

    # Non-company nodes in PF graph
    for n in pf["nodes"]:
        if n.get("entity_type") in ("project", "operating_asset", "market_aggregate") or str(n["id"]).startswith("kr_permit"):
            errors.append(f"PF non-company node: {n['id']}")
        if n["id"] == "kr_pf_market":
            errors.append("aggregate hub kr_pf_market present")

    # Edge endpoints exist
    for label, net in (("semi", semi), ("pf", pf)):
        ids = {n["id"] for n in net["nodes"]}
        for e in net["edges"]:
            if e["source"] not in ids or e["target"] not in ids:
                errors.append(f"{label} broken edge {e['id']}")

    # Syndicated amount double-count heuristic: same project_id + amount_note containing same total
    by_proj = defaultdict(list)
    for e in pf["edges"]:
        pid = e.get("project_id")
        if pid and e.get("amount_note"):
            by_proj[pid].append(e)
    for pid, edges in by_proj.items():
        totals = [e for e in edges if "1,590" in (e.get("amount_note") or "") or "1590" in (e.get("amount_note") or "")]
        if len(totals) > 1:
            # OK if notes say not to assign full amount
            bad = [e["id"] for e in totals if "단독" not in (e.get("amount_note") or "") and "배분" not in (e.get("amount_note") or "") and "개별" not in (e.get("amount_note") or "")]
            if bad:
                warns.append(f"possible syndicated double-count on {pid}: {bad}")

    # CoreWeave direct KR PF without VERIFIED
    for e in pf["edges"]:
        if "coreweave" in (e["source"], e["target"]):
            other = e["target"] if e["source"] == "coreweave" else e["source"]
            n = next((x for x in pf["nodes"] if x["id"] == other), None)
            if n and n.get("region") == "KR" and e.get("source_status") == "VERIFIED" and e.get("relationship_type") in ("PROJECT_LOAN", "CREDIT_ENHANCEMENT"):
                warns.append(f"CW↔KR financial VERIFIED check: {e['id']}")

    # US eligibility: newly added US nodes should be eligible or pre-existing
    eligible = set(elig["eligible_ids"])
    for n in semi["nodes"]:
        if n.get("region") == "US" and n.get("listed") and n["id"] in elig["eligible_ids"]:
            pass
        if n["id"] in elig.get("excluded_ids", []) and n.get("listed"):
            # private exclusions are by id not in network
            pass

    # Project SPV references
    pf_ids = {n["id"] for n in pf["nodes"]}
    for pr in projects["projects"]:
        if pr.get("country") != "KR" and pr.get("region") != "KR":
            continue
        for field in ("spv", "developer", "operator", "owner", "tenant"):
            v = pr.get(field)
            if v and v not in pf_ids and pr.get("financing_disclosed"):
                warns.append(f"project {pr['id']} {field}={v} not in PF graph")

    # FX recorded
    if not elig.get("fx", {}).get("rate"):
        errors.append("missing FX rate in eligibility file")

    out = {"errors": errors, "warnings": warns, "semi": {"nodes": len(semi["nodes"]), "edges": len(semi["edges"])},
           "pf": {"nodes": len(pf["nodes"]), "edges": len(pf["edges"])},
           "projects": len(projects["projects"]), "fx": elig.get("fx")}
    path = PF / "_validation_v4.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
