#!/usr/bin/env python3
"""Add research-stub nodes for mandatory securities missing from the map.

NO financing edges are created — stubs exist only so the audit roster is visible
and DART follow-up can attach evidence later.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"

STUBS = [
    ("mirae_asset_sec", "미래에셋증권", "Mirae Asset Securities"),
    ("daishin_sec", "대신증권", "Daishin Securities"),
    ("ls_sec", "LS증권", "LS Securities"),
    ("shinyoung_sec", "신영증권", "Shinyoung Securities"),
    ("db_sec", "DB증권", "DB Securities"),
    ("im_sec", "iM증권", "iM Securities"),
    ("bnk_sec", "BNK투자증권", "BNK Investment & Securities"),
    ("bookook_sec", "부국증권", "Bookook Securities"),
    ("cape_sec", "케이프투자증권", "Cape Investment & Securities"),
]


def main() -> None:
    data = json.loads(NET.read_text(encoding="utf-8"))
    ids = {n["id"] for n in data["nodes"]}
    added = []
    for nid, ko, en in STUBS:
        if nid in ids:
            continue
        data["nodes"].append({
            "id": nid,
            "name": en,
            "name_ko": ko,
            "group": "kr_securities",
            "region": "KR",
            "entity_type": "financial",
            "role": "securities",
            "display_size": 5,
            "source_status": "RESEARCH",
            "pf_exposure_class": "research_candidate",
            "key_drivers": ["research_candidate"],
            "note": "감사 대상 증권사 — 검증된 DC 금융 엣지 없음. DART 조사 대기. 관계 미생성.",
        })
        added.append(nid)
        ids.add(nid)
    if added:
        NET.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("added stubs", added)


if __name__ == "__main__":
    main()
