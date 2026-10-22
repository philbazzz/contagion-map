# -*- coding: utf-8 -*-
import json
from pathlib import Path

idx = json.loads(Path("backend/data/opendart_cache/corp_codes_index.json").read_text(encoding="utf-8"))
hits = [r for r in idx if "유진" in (r.get("corp_name") or "") and "증권" in (r.get("corp_name") or "")]
Path("docs/_eugene_hits.json").write_text(json.dumps(hits[:30], ensure_ascii=False, indent=2), encoding="utf-8")
print(len(hits))
