#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

PF = Path(__file__).resolve().parents[1] / "frontend" / "public" / "data" / "pf"
net = json.loads((PF / "network.json").read_text(encoding="utf-8"))
proj = json.loads((PF / "projects.json").read_text(encoding="utf-8"))
out = []
out.append("=== FINAL VALIDATION SNAPSHOT ===")
out.append(f"nodes={len(net['nodes'])} edges={len(net['edges'])} projects={len(proj['projects'])}")
out.append(f"KR_nodes={sum(1 for n in net['nodes'] if n.get('region') == 'KR')}")
out.append("stages=" + json.dumps(Counter(p["construction_stage"] for p in proj["projects"]), ensure_ascii=False))
sido = Counter(p.get("sido") or "unknown" for p in proj["projects"] if (p.get("country") or p.get("region")) == "KR")
out.append("sido=" + json.dumps(dict(sido.most_common()), ensure_ascii=False))
out.append(f"financing_disclosed={sum(1 for p in proj['projects'] if p.get('financing_disclosed'))}")
out.append(f"incomplete_fin={sum(1 for p in proj['projects'] if not p.get('financing_disclosed'))}")
ver = [e for e in net["edges"] if e.get("source_status") == "VERIFIED"]
out.append(f"verified_edges={len(ver)}")
out.append(f"project_loan={sum(1 for e in ver if e.get('relationship_type') == 'PROJECT_LOAN')}")
out.append(f"epc={sum(1 for e in ver if e.get('relationship_type') == 'EPC_CONTRACT')}")
hw = [e for e in net["edges"] if "hostway" in e["source"] + e["target"]]
out.append(f"hostway_edges={len(hw)} types={[e['relationship_type'] for e in hw]}")
deg = Counter()
for e in net["edges"]:
    deg[e["source"]] += 1
    deg[e["target"]] += 1
out.append("top_deg=" + str(deg.most_common(8)))
iso = sum(
    1
    for n in net["nodes"]
    if n.get("region") == "KR"
    and not any(e["source"] == n["id"] or e["target"] == n["id"] for e in net["edges"])
)
out.append(f"isolated_kr_nodes={iso} (permit/pipeline without fabricated PF — intentional)")
text = "\n".join(out)
(PF / "_validation_snapshot.txt").write_text(text, encoding="utf-8")
print(text)

if __name__ == "__main__":
    pass
