# -*- coding: utf-8 -*-
import json
from pathlib import Path
from collections import Counter, defaultdict

p = Path("docs/opendart_body_keyword_hits.json")
d = json.loads(p.read_text(encoding="utf-8"))

dc_kw = {"데이터센터", "데이터 센터", "AI 데이터센터", "IDC", "전산센터", "캠스퀘어", "케이스퀘어"}
pf_kw = {"부동산 PF", "프로젝트파이낸싱", "프로젝트 파이낸싱", "브릿지론", "본PF", "ABCP", "ABSTB", "매입확약"}

summary = []
for r in d.get("results", []):
    dc = Counter()
    pf = Counter()
    other = Counter()
    examples = []
    for f in r.get("filings_with_hits") or []:
        for h in f.get("keyword_hits") or []:
            k = h["keyword"]
            c = h.get("count") or 0
            if k in dc_kw:
                dc[k] += c
            elif k in pf_kw:
                pf[k] += c
            else:
                other[k] += c
            if k in dc_kw and h.get("snippets") and len(examples) < 2:
                examples.append({
                    "report": f.get("report_nm"),
                    "date": f.get("rcept_dt"),
                    "keyword": k,
                    "snippet": h["snippets"][0][:200],
                    "url": f.get("viewer_url"),
                })
    summary.append({
        "firm": r["firm"],
        "corp_code": r.get("corp_code"),
        "filings_scanned": r.get("filings_scanned"),
        "dc_mentions": dict(dc),
        "pf_mentions": dict(pf),
        "dc_total": sum(dc.values()),
        "pf_total": sum(pf.values()),
        "examples": examples,
    })

summary.sort(key=lambda x: (-x["dc_total"], -x["pf_total"], x["firm"]))
out = {
    "verification_date": d.get("verification_date"),
    "docs_scanned": d.get("docs_scanned"),
    "errors": d.get("errors"),
    "by_firm": summary,
    "firms_with_datacenter_keyword": [s["firm"] for s in summary if s["dc_total"] > 0],
    "firms_with_pf_keyword_only": [s["firm"] for s in summary if s["dc_total"] == 0 and s["pf_total"] > 0],
    "firms_no_hits": [s["firm"] for s in summary if s["dc_total"] == 0 and s["pf_total"] == 0 and s["filings_scanned"]],
    "firms_no_filings": [s["firm"] for s in summary if not s["filings_scanned"]],
}
Path("docs/opendart_body_hit_summary.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("dc firms", len(out["firms_with_datacenter_keyword"]))
print("pf only", len(out["firms_with_pf_keyword_only"]))
print("no filings", out["firms_no_filings"])
print("errors", out["errors"])
for s in summary:
    if s["dc_total"] or s["pf_total"]:
        print(f"{s['firm']}\tdc={s['dc_total']}\tpf={s['pf_total']}")
