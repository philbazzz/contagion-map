"""Baseline inventory of entities and relationships."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
ents = json.loads((DATA / "entities.json").read_text(encoding="utf-8"))["entities"]
rels = json.loads((DATA / "relationships.json").read_text(encoding="utf-8"))["relationships"]
ids = sorted(x["id"] for x in ents)
print("ENTITIES", len(ids))
for x in sorted(ents, key=lambda z: z["id"]):
    print(f"{x['id']}|{x['group']}|{x.get('ticker')}|{x['name']}")
print("EDGES", len(rels))
deg: dict[str, int] = defaultdict(int)
cw = 0
for edge in rels:
    deg[edge["source"]] += 1
    deg[edge["target"]] += 1
    if edge["source"] == "coreweave" or edge["target"] == "coreweave":
        cw += 1
print("CW-touching", cw, "non-CW", len(rels) - cw)
print("avg_degree", round(sum(deg.values()) / max(len(ids), 1), 2))
print("zero", [i for i in ids if deg[i] == 0])
print("deg1", sorted(i for i in ids if deg[i] == 1))
print("types", dict(Counter(x["relationship_type"] for x in rels)))
print("NON_CW_EDGES")
for edge in rels:
    if edge["source"] != "coreweave" and edge["target"] != "coreweave":
        print(edge["id"], edge["source"], "->", edge["target"], edge["relationship_type"], edge.get("source_status"))
print("ALL_PAIRS")
pairs = {(min(e["source"], e["target"]), max(e["source"], e["target"])) for e in rels}
print("unique_undirected_pairs", len(pairs))
