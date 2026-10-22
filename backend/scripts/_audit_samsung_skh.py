import json
from pathlib import Path

ents = json.loads(Path("data/entities.json").read_text(encoding="utf-8"))["entities"]
rels = json.loads(Path("data/relationships.json").read_text(encoding="utf-8"))["relationships"]
print("entities", len(ents), "edges", len(rels))
for oid in ["samsung", "sk_hynix", "hanmi_semi", "micron", "nvidia", "tsmc", "amd", "apple"]:
    edges = [r for r in rels if r["source"] == oid or r["target"] == oid]
    print(f"--- {oid} ({len(edges)})")
    for r in edges:
        print(f"  {r['id']}: {r['source']}->{r['target']} {r['relationship_type']} {r['source_status']}")
print("KR", [e["id"] for e in ents if e.get("exchange") in ("KOSPI", "KOSDAQ")])
