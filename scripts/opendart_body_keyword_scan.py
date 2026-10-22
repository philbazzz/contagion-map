#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download latest annual/half-year filings and search body text for DC/PF keywords.

Does NOT create graph edges. Writes evidence queue for human/model reconciliation.
Never prints API key.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

OUT = ROOT / "docs" / "opendart_body_keyword_hits.json"
QUEUE = ROOT / "docs" / "opendart_dc_keyword_queue.json"
AUDIT_MD = ROOT / "DATA_CENTER_PF_AUDIT.md"
AUDIT_JSON = ROOT / "docs" / "DATA_CENTER_PF_AUDIT.json"

# firm label -> DART corp_name search aliases (first match with stock preferred)
FIRM_ALIASES: list[tuple[str, list[str]]] = [
    ("한국투자증권", ["한국투자증권"]),
    ("KB증권", ["케이비증권", "KB증권"]),
    ("메리츠증권", ["메리츠증권"]),
    ("NH투자증권", ["NH투자증권"]),
    ("미래에셋증권", ["미래에셋증권"]),
    ("삼성증권", ["삼성증권"]),
    ("신한투자증권", ["신한투자증권"]),
    ("하나증권", ["하나증권"]),
    ("대신증권", ["대신증권"]),
    ("키움증권", ["키움증권"]),
    ("IBK투자증권", ["아이비케이투자증권", "IBK투자증권"]),
    ("현대차증권", ["현대차증권"]),
    ("SK증권", ["SK증권"]),
    ("교보증권", ["교보증권"]),
    ("유안타증권", ["유안타증권"]),
    ("한화투자증권", ["한화투자증권"]),
    ("다올투자증권", ["다올투자증권"]),
    ("LS증권", ["LS증권"]),
    ("신영증권", ["신영증권"]),
    ("DB증권", ["DB증권"]),
    ("유진투자증권", ["유진투자증권", "유진증권"]),
    ("iM증권", ["아이엠증권", "iM증권"]),
    ("BNK투자증권", ["BNK투자증권"]),
    ("부국증권", ["부국증권"]),
    ("케이프투자증권", ["케이프투자증권"]),
]

BODY_KEYWORDS = [
    "데이터센터", "데이터 센터", "AI 데이터센터", "IDC", "전산센터",
    "부동산 PF", "프로젝트파이낸싱", "프로젝트 파이낸싱", "브릿지론", "본PF",
    "ABCP", "ABSTB", "매입확약", "신용공여", "유동화",
    "캠스퀘어", "케이스퀘어", "가산동", "용인", "안산", "에코델타",
]


def pick_corp(client, aliases: list[str]) -> dict | None:
    for alias in aliases:
        res = client.company_list(alias)
        hits = res.get("list") or []
        exact = [h for h in hits if (h.get("corp_name") or "").replace(" ", "") == alias.replace(" ", "")]
        pool = exact or [h for h in hits if alias.replace(" ", "") in (h.get("corp_name") or "").replace(" ", "")]
        if not pool:
            continue
        listed = [h for h in pool if (h.get("stock_code") or "").strip()]
        return (listed or pool)[0]
    return None


def latest_periodic(client, corp_code: str, *, limit: int = 4) -> list[dict]:
    """Prefer 사업보고서 / 반기 / 분기 from recent years (정기공시 A, paginated)."""
    end = date.today().strftime("%Y%m%d")
    bgn = "20200101"
    wanted: list[dict] = []
    total_pages = 1
    page_no = 1
    while page_no <= min(total_pages, 5):
        disc = client.disclosure_list(
            corp_code=corp_code, bgn_de=bgn, end_de=end,
            pblntf_ty="A", page_count=100, page_no=page_no,
        )
        if page_no == 1:
            try:
                total_pages = max(1, int(disc.get("total_page") or 1))
            except (TypeError, ValueError):
                total_pages = 1
        rows = disc.get("list") or []
        if not rows:
            break
        for row in rows:
            nm = row.get("report_nm") or ""
            if any(x in nm for x in ("사업보고서", "반기보고서", "분기보고서", "감사보고서")):
                wanted.append(row)
        page_no += 1
        time.sleep(0.12)
    # Dedupe by report type family, keep newest (list is typically newest-first)
    picked: list[dict] = []
    seen_types: set[str] = set()
    for row in wanted:
        nm = row.get("report_nm") or ""
        kind = "annual" if "사업보고서" in nm else "half" if "반기" in nm else "quarter" if "분기" in nm else "audit"
        key = f"{kind}:{(row.get('rcept_dt') or '')[:4]}"
        if key in seen_types:
            continue
        seen_types.add(key)
        picked.append(row)
        if len(picked) >= limit:
            break
    return picked


def snippets(text: str, keyword: str, *, width: int = 120, max_n: int = 3) -> list[str]:
    out = []
    start = 0
    while len(out) < max_n:
        i = text.find(keyword, start)
        if i < 0:
            break
        a = max(0, i - width)
        b = min(len(text), i + len(keyword) + width)
        frag = text[a:b].strip()
        frag = re.sub(r"\s+", " ", frag)
        out.append(frag)
        start = i + len(keyword)
    return out


def main() -> None:
    from app.opendart.client import OpenDartClient, OpenDartError

    client = OpenDartClient()
    if not client.configured:
        print("SKIP: key not configured")
        return

    results = []
    errors = []
    docs_scanned = 0
    total_hits = 0

    for firm, aliases in FIRM_ALIASES:
        try:
            corp = pick_corp(client, aliases)
            if not corp:
                errors.append({"firm": firm, "error": "corp_code not found", "aliases": aliases})
                print(f"MISS {firm}")
                continue
            corp_code = corp["corp_code"]
            filings = latest_periodic(client, corp_code, limit=3)
            firm_hits = []
            for fil in filings:
                rcept = fil.get("rcept_no")
                if not rcept:
                    continue
                try:
                    doc = client.document_text(rcept)
                except OpenDartError as ex:
                    errors.append({"firm": firm, "rcept_no": rcept, "error": str(ex)})
                    continue
                docs_scanned += 1
                text = doc.get("text") or ""
                kw_hits = []
                for kw in BODY_KEYWORDS:
                    if kw in text:
                        kw_hits.append({
                            "keyword": kw,
                            "count": text.count(kw),
                            "snippets": snippets(text, kw),
                        })
                if kw_hits:
                    total_hits += len(kw_hits)
                    firm_hits.append({
                        "rcept_no": rcept,
                        "report_nm": fil.get("report_nm"),
                        "rcept_dt": fil.get("rcept_dt"),
                        "publication_date": fil.get("rcept_dt"),
                        "viewer_url": doc.get("viewer_url"),
                        "text_len": doc.get("text_len"),
                        "keyword_hits": kw_hits,
                    })
                time.sleep(0.25)
            results.append({
                "firm": firm,
                "corp_code": corp_code,
                "corp_name": corp.get("corp_name"),
                "stock_code": corp.get("stock_code"),
                "filings_scanned": len(filings),
                "filings_with_hits": firm_hits,
                "hit_filing_count": len(firm_hits),
            })
            print(f"OK {firm}: docs={len(filings)} hit_filings={len(firm_hits)}")
            time.sleep(0.2)
        except Exception as ex:  # noqa: BLE001
            errors.append({"firm": firm, "error": repr(ex)})
            print(f"ERR {firm}: {ex!r}")

    payload = {
        "verification_date": date.today().isoformat(),
        "status": "partial_body_scan",
        "note": (
            "Body keyword hits from recent periodic filings. "
            "Snippets are leads only — verify outstanding exposure vs arrangement before graph updates. "
            "No ACTIVE edges auto-created from this scan."
        ),
        "docs_scanned": docs_scanned,
        "firms_scanned": len(results),
        "total_keyword_types_hit": total_hits,
        "results": results,
        "errors": errors,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Summarize into audit MD appendix
    lines = [
        "",
        "## OpenDART body keyword scan (live)",
        "",
        f"- Verification date: {payload['verification_date']}",
        f"- Docs scanned: {docs_scanned}",
        f"- Firms with corp match: {len(results)}",
        f"- Keyword-type hits across filings: {total_hits}",
        f"- Detail: `docs/opendart_body_keyword_hits.json`",
        "",
    ]
    for r in results:
        if not r["filings_with_hits"]:
            continue
        lines.append(f"### {r['firm']} (`{r['corp_code']}`)")
        for f in r["filings_with_hits"]:
            kws = ", ".join(f"{h['keyword']}×{h['count']}" for h in f["keyword_hits"][:12])
            lines.append(f"- {f['report_nm']} ({f['rcept_dt']}) — {kws}")
            lines.append(f"  - {f['viewer_url']}")
        lines.append("")
    if errors:
        lines.append("### Scan errors / unresolved corp codes")
        for e in errors:
            lines.append(f"- {e.get('firm')}: {e.get('error')}")
        lines.append("")

    if AUDIT_MD.exists():
        md = AUDIT_MD.read_text(encoding="utf-8")
        marker = "## OpenDART body keyword scan (live)"
        if marker in md:
            md = md.split(marker)[0].rstrip() + "\n"
        AUDIT_MD.write_text(md + "\n".join(lines) + "\n", encoding="utf-8")

    if AUDIT_JSON.exists():
        audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
        audit["opendart_api_configured"] = True
        audit["filings_inspected"] = docs_scanned
        audit["opendart_body_scan"] = {
            "status": payload["status"],
            "docs_scanned": docs_scanned,
            "file": "docs/opendart_body_keyword_hits.json",
        }
        AUDIT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Merge corp aliases into title queue meta
    if QUEUE.exists():
        q = json.loads(QUEUE.read_text(encoding="utf-8"))
        q["body_scan_file"] = "docs/opendart_body_keyword_hits.json"
        q["opendart_api_configured"] = True
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("wrote", OUT)
    print("docs", docs_scanned, "keyword_types", total_hits, "errors", len(errors))


if __name__ == "__main__":
    main()
