#!/usr/bin/env python3
"""Audit PF network for non-company nodes and coverage gaps."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PF = ROOT / "frontend" / "public" / "data" / "pf"

def main() -> None:
    net = json.loads((PF / "network.json").read_text(encoding="utf-8"))
    lines = []
    lines.append(f"nodes={len(net['nodes'])} edges={len(net['edges'])}")
    lines.append("entity_types=" + str(Counter(n.get("entity_type") for n in net["nodes"]).most_common()))
    lines.append("groups=" + str(Counter(n.get("group") for n in net["nodes"]).most_common()))

    nonco = []
    for n in net["nodes"]:
        et = n.get("entity_type") or ""
        gid = n.get("id") or ""
        name = n.get("name") or ""
        flags = []
        if et in ("operating_asset", "project", "permit", "market_aggregate", "facility"):
            flags.append(f"etype={et}")
        if gid.startswith("kr_permit") or "permit" in gid:
            flags.append("permit_id")
        if gid == "kr_pf_market" or et == "market_aggregate":
            flags.append("aggregate")
        if "IDC" in name and et in ("operating_asset", "project"):
            flags.append("facility_name")
        if flags:
            nonco.append((gid, et, name, n.get("group"), flags))
    lines.append(f"non_company_candidates={len(nonco)}")
    for row in nonco:
        lines.append(f"  NONCO {row}")

    for key in [
        "hanwha_inv_sec", "hanwha_sec", "hanwha",
        "kakao", "kakao_enterprise", "nhn", "nhn_cloud", "gabia", "hostway_kr",
        "aws", "amazon", "microsoft", "google", "naver_cloud",
        "sejong_telecom", "kinx", "lg_uplus", "sk_broadband",
        "lf_corp", "koramco_am", "koramco_trust",
    ]:
        hit = next((n for n in net["nodes"] if n["id"] == key or key in n["id"]), None)
        lines.append(f"LOOKUP {key} -> {hit['id'] if hit else 'MISSING'} {hit.get('name') if hit else ''}")

    ids = {n["id"] for n in net["nodes"]}
    for term in ["한화", "카카오", "NHN", "가비아", "세종", "KINX", "유플러스"]:
        hits = [n["id"] for n in net["nodes"] if term in (n.get("name") or "") + (n.get("name_ko") or "") + n["id"]]
        lines.append(f"TERM {term}: {hits}")

    # edges touching hostway / casequare / aggregate
    for e in net["edges"]:
        if "kr_pf_market" in (e["source"], e["target"]) or "hostway" in e["source"] + e["target"]:
            lines.append(f"EDGE {e['id']} {e['source']}->{e['target']} {e.get('relationship_type')} {e.get('source_status')}")

    out = PF / "_company_audit.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} lines={len(lines)}")

if __name__ == "__main__":
    main()
