# -*- coding: utf-8 -*-
import json
from pathlib import Path
idx = json.loads(Path("backend/data/opendart_cache/corp_codes_index.json").read_text(encoding="utf-8"))
for q in ["미래에셋", "케이프", "케이에프", "하이투자", "다올"]:
    hits = [r for r in idx if q in (r.get("corp_name") or "") and "증권" in (r.get("corp_name") or "")]
    print("===", q, len(hits))
    for h in hits[:15]:
        print(h)
