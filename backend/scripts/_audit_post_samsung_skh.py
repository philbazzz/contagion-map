import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ents = json.loads((ROOT / "backend/data/entities.json").read_text(encoding="utf-8"))["entities"]
rels = json.loads((ROOT / "backend/data/relationships.json").read_text(encoding="utf-8"))["relationships"]
prof = json.loads((ROOT / "backend/data/profiles.json").read_text(encoding="utf-8"))

ids = {e["id"] for e in ents}
deg = {i: 0 for i in ids}
for r in rels:
    deg[r["source"]] = deg.get(r["source"], 0) + 1
    deg[r["target"]] = deg.get(r["target"], 0) + 1

kr = [e for e in ents if e.get("exchange") in ("KOSPI", "KOSDAQ")]
cw = sum(1 for r in rels if r["source"] == "coreweave" or r["target"] == "coreweave")
non_cw = len(rels) - cw
us_kr = 0
ex = {e["id"]: e.get("exchange") for e in ents}
for r in rels:
    a, b = ex.get(r["source"]), ex.get(r["target"])
    kr_set = {"KOSPI", "KOSDAQ"}
    us_set = {"Nasdaq", "NYSE"}
    if (a in kr_set and b in us_set) or (b in kr_set and a in us_set):
        us_kr += 1

isolated = [e["id"] for e in ents if deg.get(e["id"], 0) == 0]
one = [e["id"] for e in ents if deg.get(e["id"], 0) == 1]


def dump_hub(oid):
    edges = [r for r in rels if r["source"] == oid or r["target"] == oid]
    print(f"\n=== {oid} degree={len(edges)} profile={'yes' if oid in prof else 'no'} ===")
    for r in edges:
        print(f"  {r['id']}: {r['source']}->{r['target']} {r['relationship_type']} [{r['source_status']}]")
        print(f"    {r['label']}")


print("entities", len(ents), "edges", len(rels))
print("KR listed", len(kr), [e["id"] for e in kr])
print("coreweave_edges", cw, "non_coreweave_edges", non_cw)
print("us_korea_edges", us_kr)
print("isolated", isolated)
print("degree1_sample", one[:20], "... total", len(one))
dump_hub("samsung")
dump_hub("sk_hynix")
print("\nnew entities present:", [x for x in ("qualcomm", "tesla", "jusung_eng") if x in ids])
