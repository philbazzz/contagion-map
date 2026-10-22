#!/usr/bin/env python3
import json
from pathlib import Path

d = json.loads(Path("docs/opendart_borrower28_investigation.json").read_text(encoding="utf-8"))
print("date", d["verification_date"])
print("by_class:")
for k, v in sorted(d["by_classification"].items(), key=lambda x: -x[1]):
    print(f"  {v:2d}  {k}")
print()
for r in d["results"]:
    pc = r.get("primary_corp") or {}
    print(f"{r['id']} | {r['seed_name']}")
    print(f"  class: {r['classification']}")
    print(f"  corp: {pc.get('corp_name')} ({pc.get('corp_code')})")
    print(f"  map: {[m['id'] for m in (r.get('map_nodes') or [])]}")
    disc = r.get("disclosures") or {}
    print(f"  filings: {disc.get('filing_count')} dc={disc.get('dc_title_hits')} fin={disc.get('fin_title_hits')}")
    rev = [h for h in (r.get("reverse_hits") or []) if h.get("rcept_no")]
    if rev:
        print(f"  reverse: {len(rev)} e.g. {(rev[0].get('report_nm') or '')[:70]}")
    for f in (disc.get("recent") or [])[:4]:
        if f.get("dc_hint") or f.get("fin_hint"):
            print(f"  filing: {f.get('rcept_dt')} {f.get('report_nm')}")
