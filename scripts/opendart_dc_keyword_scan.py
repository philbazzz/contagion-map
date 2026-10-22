#!/usr/bin/env python3
"""Keyword scan for data-center PF disclosures via OpenDART (server-side key only).

Requires OPEN_DART_API_KEY in env or backend/.env.
Does not invent graph edges — writes a research queue for verified integration.
Never prints the API key.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

OUT = ROOT / "docs" / "opendart_dc_keyword_queue.json"
AUDIT_JSON = ROOT / "docs" / "DATA_CENTER_PF_AUDIT.json"

KEYWORDS = [
    "데이터센터", "데이터 센터", "AI 데이터센터", "IDC", "전산센터",
    "부동산 PF", "프로젝트파이낸싱", "프로젝트 파이낸싱", "브릿지론", "본PF",
    "담보대출", "금융주선", "채무보증", "지급보증", "신용공여", "매입확약",
    "ABCP", "ABSTB", "Data Center", "Project Finance", "캠스퀘어", "케이스퀘어",
    "가산", "용인", "안산", "부천", "인천", "에코델타",
]

FIRMS = [
    "한국투자증권", "KB증권", "메리츠증권", "NH투자증권", "미래에셋증권",
    "삼성증권", "신한투자증권", "하나증권", "대신증권", "키움증권",
    "IBK투자증권", "현대차증권", "SK증권", "교보증권", "유안타증권",
    "한화투자증권", "다올투자증권", "LS증권", "신영증권", "DB증권",
    "유진투자증권", "iM증권", "BNK투자증권", "부국증권", "케이프투자증권",
]


def pick_corp(hits: list[dict], firm: str) -> dict | None:
    if not hits:
        return None
    exact = [h for h in hits if (h.get("corp_name") or "").replace(" ", "") == firm.replace(" ", "")]
    if exact:
        # Prefer stock-listed (has stock_code)
        listed = [h for h in exact if (h.get("stock_code") or "").strip()]
        return listed[0] if listed else exact[0]
    # Partial: firm name contained
    partial = [h for h in hits if firm.replace(" ", "") in (h.get("corp_name") or "").replace(" ", "")]
    listed = [h for h in partial if (h.get("stock_code") or "").strip()]
    return (listed or partial or hits)[0]


def main() -> None:
    from app.opendart.client import OpenDartClient, OpenDartError

    client = OpenDartClient()
    if not client.configured:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({
            "verification_date": date.today().isoformat(),
            "status": "skipped",
            "reason": "OPEN_DART_API_KEY not configured",
            "hits": [],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("SKIP: no API key")
        return

    # Sync corp codes if missing
    index = client.cache_dir / "corp_codes_index.json"
    if not index.exists():
        print("syncing corp codes…")
        sync = client.sync_corp_codes()
        print("corp codes", sync.get("count"))
    else:
        print("corp codes cache present")

    hits = []
    errors = []
    filings_inspected = 0
    end = date.today().strftime("%Y%m%d")
    bgn = "20180101"

    for firm in FIRMS:
        try:
            res = client.company_list(firm)
            corp_row = pick_corp(res.get("list") or [], firm)
            if not corp_row or not corp_row.get("corp_code"):
                errors.append({"firm": firm, "error": "corp_code not found", "candidates": len(res.get("list") or [])})
                continue
            corp = corp_row["corp_code"]
            matched = []
            page_no = 1
            total_pages = 1
            # Cap pages to keep rate limits reasonable; prefer recent filings first
            max_pages = 8
            while page_no <= min(total_pages, max_pages):
                disc = client.disclosure_list(
                    corp_code=corp, bgn_de=bgn, end_de=end, page_count=100, page_no=page_no,
                )
                status = disc.get("status")
                if status and status not in ("000", "013"):
                    errors.append({"firm": firm, "error": f"list status={status} msg={disc.get('message')}"})
                    break
                rows = disc.get("list") or []
                if page_no == 1:
                    try:
                        total_pages = max(1, int(disc.get("total_page") or 1))
                    except (TypeError, ValueError):
                        total_pages = 1
                filings_inspected += len(rows)
                for row in rows:
                    title = f"{row.get('report_nm') or ''} {row.get('corp_name') or ''}"
                    matched_kw = [k for k in KEYWORDS if k.lower() in title.lower()]
                    if matched_kw:
                        matched.append({
                            "rcept_no": row.get("rcept_no"),
                            "report_nm": row.get("report_nm"),
                            "rcept_dt": row.get("rcept_dt"),
                            "corp_code": corp,
                            "corp_name": corp_row.get("corp_name"),
                            "keywords": matched_kw,
                            "viewer_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={row.get('rcept_no')}",
                        })
                if not rows:
                    break
                page_no += 1
                time.sleep(0.15)

            hits.append({
                "firm": firm,
                "corp_code": corp,
                "corp_name": corp_row.get("corp_name"),
                "stock_code": corp_row.get("stock_code"),
                "title_keyword_hits": matched[:80],
                "hit_count": len(matched),
            })
            print(f"OK {firm}: hits={len(matched)} corp={corp}")
            time.sleep(0.2)
        except OpenDartError as ex:
            errors.append({"firm": firm, "error": str(ex), "code": getattr(ex, "code", None)})
            print(f"ERR {firm}: {ex}")
        except Exception as ex:  # noqa: BLE001
            errors.append({"firm": firm, "error": repr(ex)})
            print(f"ERR {firm}: {ex!r}")

    payload = {
        "verification_date": date.today().isoformat(),
        "status": "partial_title_scan",
        "note": (
            "Title-keyword hits from OpenDART list API. "
            "Full notes / contingent-liability text review still required before creating ACTIVE edges. "
            "Do not treat arrangement headlines as retained exposure."
        ),
        "firms_scanned": len([h for h in hits if h.get("corp_code")]),
        "filings_inspected_approx": filings_inspected,
        "reporting_period": f"{bgn}-{end}",
        "hits": hits,
        "errors": errors,
        "total_keyword_hits": sum(h.get("hit_count", 0) for h in hits),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Merge into audit JSON if present
    if AUDIT_JSON.exists():
        try:
            audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
            audit["opendart_api_configured"] = True
            audit["filings_inspected"] = filings_inspected
            audit["opendart_title_scan"] = {
                "status": payload["status"],
                "total_keyword_hits": payload["total_keyword_hits"],
                "queue_file": "docs/opendart_dc_keyword_queue.json",
            }
            audit["verification_date"] = date.today().isoformat()
            AUDIT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception as ex:  # noqa: BLE001
            print("audit merge failed", repr(ex))

    print("wrote", OUT)
    print("firms_ok", len(hits), "errors", len(errors), "keyword_hits", payload["total_keyword_hits"])


if __name__ == "__main__":
    main()
