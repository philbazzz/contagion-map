# -*- coding: utf-8 -*-
import json
from pathlib import Path

idx = json.loads(Path("backend/data/opendart_cache/corp_codes_index.json").read_text(encoding="utf-8"))
queries = [
    "KB증권", "케이비증권", "KB 증권",
    "IBK투자", "아이비케이투자", "IBK투자증권",
    "유진투자", "유진투자증권",
    "iM증권", "아이엠증권", "아이엠 증권",
    "현대차증권", "현대차 증권",
]
out = []
for q in queries:
    qn = q.replace(" ", "")
    hits = [r for r in idx if qn in (r.get("corp_name") or "").replace(" ", "")]
    out.append({"query": q, "n": len(hits), "hits": hits[:12]})

Path("docs/_corp_alias_resolve.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("wrote docs/_corp_alias_resolve.json")
