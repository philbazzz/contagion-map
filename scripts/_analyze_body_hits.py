#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

hits = json.loads(Path("docs/opendart_borrower28_body_hits.json").read_text(encoding="utf-8"))
inv = json.loads(Path("docs/opendart_borrower28_investigation.json").read_text(encoding="utf-8"))

print("=== body scan status ===")
st = Counter(r["status"] for r in hits["results"])
for k, v in st.most_common():
    print(f"  {v:2d}  {k}")

print("\n=== lender mentions in snippets (NOT verified balances) ===")
for r in hits["results"]:
    lenders = []
    for s in r.get("snippets") or []:
        lenders.extend(s.get("lenders_mentioned") or [])
    if lenders:
        print(f"{r['id']} {r['seed_name']}: {Counter(lenders).most_common(8)}")
        # show one excerpt with amount
        for s in r.get("snippets") or []:
            if s.get("amounts_nearby") and s.get("lenders_mentioned"):
                print(f"  ex: {s['excerpt'][:160]}")
                print(f"     amounts={s['amounts_nearby'][:3]}")
                break

print("\n=== classification after body ===")
for k, v in sorted(inv.get("by_classification", {}).items(), key=lambda x: -x[1]):
    print(f"  {v:2d}  {k}")

print("\n=== per borrower ===")
by_id = {r["id"]: r for r in inv["results"]}
for r in hits["results"]:
    inv_r = by_id.get(r["id"], {})
    print(f"{r['id']}|{r['status']}|corp={r.get('corp_name')}|snips={len(r.get('snippets') or [])}|class={inv_r.get('classification','')[:40]}")
