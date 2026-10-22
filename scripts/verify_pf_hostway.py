#!/usr/bin/env python3
"""Quick structural checks: Hostway is not a financing hub; Hangul primary names."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

PF = Path(__file__).resolve().parents[1] / "frontend" / "public" / "data" / "pf"

def main() -> None:
    net = json.loads((PF / "network.json").read_text(encoding="utf-8"))
    proj = json.loads((PF / "projects.json").read_text(encoding="utf-8"))
    hw = [e for e in net["edges"] if "hostway" in e["source"] + e["target"]]
    assert len(hw) == 5, f"expected 5 Hostway edges, got {len(hw)}"
    for e in hw:
        assert e["source_status"] in ("VERIFIED", "INFERRED")
        assert e["relationship_type"] != "PROJECT_LOAN"
    # no ASSUMED bank→Hostway
    bad = [e for e in hw if e["source_status"] == "ASSUMED"]
    assert not bad
    deg = Counter()
    for e in net["edges"]:
        deg[e["source"]] += 1
        deg[e["target"]] += 1
    assert deg["bundang_hostway_idc"] <= deg["casequare_pfv"]
    kr = [n for n in net["nodes"] if n.get("region") == "KR"]
    hangul = sum(1 for n in kr if re.search(r"[가-힣]", n.get("name") or ""))
    assert hangul >= 170, hangul
    stages = Counter(p["construction_stage"] for p in proj["projects"])
    print("OK hostway_edges=5 casequare_deg=%s hostway_deg=%s projects=%s stages=%s hangul=%s/%s"
          % (deg["casequare_pfv"], deg["bundang_hostway_idc"], len(proj["projects"]), dict(stages), hangul, len(kr)))

if __name__ == "__main__":
    main()
