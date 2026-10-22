#!/usr/bin/env python3
"""Deepen borrower28 investigation: fetch latest audit-report document text snippets.

Does NOT invent outstanding balances. Writes body excerpts + lender/loan keyword hits
into docs/opendart_borrower28_body_hits.json and updates investigation notes.
Never prints OPEN_DART_API_KEY.
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

INV = ROOT / "docs" / "opendart_borrower28_investigation.json"
OUT = ROOT / "docs" / "opendart_borrower28_body_hits.json"
INDEX = ROOT / "backend" / "data" / "opendart_cache" / "corp_codes_index.json"

# Extra alias resolution (rename / spelling) — lookalikes are NOT merged into one entity.
ALIASES = {
    "b03": ["케펠데이터센터안산피에프브이", "케펠데이터센터안산"],
    "b11": ["신영식사피에프브이"],  # reject loose 신영* matches
    "b23": ["캠스퀘어안산데이터센터피에프브이"],
    "b24": ["캠스퀘어용인데이터센터피에프브이", "캄스퀘어용인데이터센터피에프브이"],
}

LENDER_PAT = re.compile(
    r"(KB증권|한국투자증권|메리츠증권|NH투자증권|미래에셋증권|삼성증권|신한투자증권|"
    r"하나증권|키움증권|한화투자증권|IBK투자증권|현대차증권|유안타증권|신영증권|"
    r"다올투자증권|국민은행|신한은행|하나은행|우리은행|농협은행|기업은행|"
    r"산업은행|수협은행|저축은행|보험|공제|신탁|리츠|대우건설|현대건설|삼성물산)",
)
LOAN_PAT = re.compile(r"(차입금|단기차입|장기차입|대여금|대출|PF|브릿지|담보대출|사채|보증|채무보증|자금보충|매입확약|출자|지분|약정)")
AMOUNT_PAT = re.compile(r"([\d,]+)\s*(백만원|천원|원|억원)")


def norm(s: str) -> str:
    return re.sub(r"[\s()（）㈜株式会社주식회사]", "", s or "")


def log(msg: str) -> None:
    print(msg, flush=True)


def find_alias(index: list[dict], queries: list[str]) -> list[dict]:
    out, seen = [], set()
    for q in queries:
        qn = norm(q)
        if len(qn) < 4:
            continue
        for r in index:
            cn = norm(r.get("corp_name") or "")
            if qn not in cn:
                continue
            code = r.get("corp_code")
            if not code or code in seen:
                continue
            # Require strong overlap for short queries
            if len(qn) < 8 and cn != qn and not cn.startswith(qn):
                continue
            seen.add(code)
            out.append({"corp_code": code, "corp_name": r.get("corp_name"), "query": q})
    return out


def pick_audit(filings: list[dict]) -> dict | None:
    audits = [f for f in filings if "감사보고서" in (f.get("report_nm") or "")]
    if not audits:
        return None
    audits.sort(key=lambda f: f.get("rcept_dt") or "", reverse=True)
    return audits[0]


def extract_borrowings_note(text: str) -> dict | None:
    """Prefer the 차입금 note table over early BS/CF keyword hits.

    Historical bug: max_snips=12 stopped inside the balance sheet, so gaya's
    '12. 차입금 … 차입처 국민은행…' table never entered body_hits and edges
    were skipped as '대주 개별 배분 미확인'.
    """
    flat = re.sub(r"\s+", " ", text or "")
    candidates = []
    for m in re.finditer(r"\d+\.\s*차입금\b|\d+\.\s*장기차입금\b|장단기차입금의\s*구성내역", flat):
        head = flat[m.start() : m.start() + 60]
        if re.search(r"차입금\s*상환|차입금\s*차입", head):
            continue
        chunk = flat[m.start() : m.start() + 3500]
        score = ("차입처" in chunk) * 5 + ("Term Loan" in chunk) * 3 + ("약정한도" in chunk) * 2
        candidates.append((score, chunk))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    chunk = candidates[0][1]
    return {
        "keyword": "차입금_주석표",
        "excerpt": chunk[:900],
        "lenders_mentioned": sorted(set(LENDER_PAT.findall(chunk))),
        "amounts_nearby": [{"raw": a, "unit": u} for a, u in AMOUNT_PAT.findall(chunk)[:8]],
        "note_table": True,
    }


def extract_snippets(text: str, max_snips: int = 12) -> list[dict]:
    if not text:
        return []
    # Normalize whitespace for search
    flat = re.sub(r"\s+", " ", text)
    hits = []
    note = extract_borrowings_note(flat)
    if note:
        hits.append(note)
    for m in LOAN_PAT.finditer(flat):
        start = max(0, m.start() - 80)
        end = min(len(flat), m.end() + 160)
        snip = flat[start:end]
        # Skip pure BS line-item hits when we already have the note table
        if note and re.search(r"비유동부채|재무활동현금흐름", snip) and "차입처" not in snip:
            continue
        lenders = sorted(set(LENDER_PAT.findall(snip)))
        amounts = [{"raw": a, "unit": u} for a, u in AMOUNT_PAT.findall(snip)[:4]]
        hits.append({
            "keyword": m.group(0),
            "excerpt": snip[:240],
            "lenders_mentioned": lenders,
            "amounts_nearby": amounts,
        })
        if len(hits) >= max_snips:
            break
    return hits


def main() -> None:
    from app.opendart.client import OpenDartClient

    client = OpenDartClient()
    if not client.configured:
        log("SKIP: no API key")
        return
    inv = json.loads(INV.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else []

    body_results = []
    for r in inv["results"]:
        bid = r["id"]
        primary = r.get("primary_corp")
        # Fix / extend corp via aliases
        if bid in ALIASES:
            alias_hits = find_alias(index, ALIASES[bid])
            if alias_hits:
                # For b11, only accept exact-ish 신영식사*
                if bid == "b11":
                    alias_hits = [h for h in alias_hits if "식사" in (h.get("corp_name") or "")]
                if alias_hits and (not primary or bid in ("b03", "b24")):
                    primary = alias_hits[0]
                    r["primary_corp"] = {**primary, "stock_code": None, "modify_date": None}
                    r["corp_candidates"] = (r.get("corp_candidates") or []) + alias_hits
                    r["notes"] = list(r.get("notes") or []) + [f"alias resolved: {primary.get('corp_name')}"]
            if bid == "b11" and primary and "식사" not in (primary.get("corp_name") or ""):
                r["notes"] = list(r.get("notes") or []) + [
                    f"lookalike rejected: primary was {primary.get('corp_name')} — not 신영식사"
                ]
                r["classification"] = "검색했으나 관련 공시 미확인(동명이인·유사명 제외)"
                primary = None
                r["primary_corp"] = None

        row_out = {
            "id": bid,
            "seed_name": r["seed_name"],
            "corp_code": (primary or {}).get("corp_code"),
            "corp_name": (primary or {}).get("corp_name"),
            "document": None,
            "snippets": [],
            "status": "skipped",
        }
        if not primary:
            row_out["status"] = "no_corp"
            body_results.append(row_out)
            continue

        filings = (r.get("disclosures") or {}).get("recent") or []
        # If alias newly set, refresh disclosure list
        if bid in ALIASES and primary:
            try:
                end = date.today().strftime("%Y%m%d")
                disc = client.disclosure_list(
                    corp_code=primary["corp_code"], bgn_de="20180101", end_de=end,
                    page_count=100, page_no=1,
                )
                filings = []
                for row in disc.get("list") or []:
                    title = row.get("report_nm") or ""
                    filings.append({
                        "rcept_no": row.get("rcept_no"),
                        "report_nm": title,
                        "rcept_dt": row.get("rcept_dt"),
                    })
                r["disclosures"] = {
                    **(r.get("disclosures") or {}),
                    "status": disc.get("status"),
                    "filing_count": len(filings),
                    "recent": filings[:20],
                }
                time.sleep(0.15)
            except Exception as e:  # noqa: BLE001
                row_out["status"] = f"disclosure_error:{e}"
                body_results.append(row_out)
                continue

        audit = pick_audit(filings)
        if not audit or not audit.get("rcept_no"):
            row_out["status"] = "no_audit_report"
            body_results.append(row_out)
            continue

        rcept = audit["rcept_no"]
        log(f"body {bid} {r['seed_name']} rcept={rcept}")
        try:
            doc = client.document_text(rcept, max_chars=1_500_000)
            text = (doc.get("text") if isinstance(doc, dict) else "") or ""
            snippets = extract_snippets(text)
            row_out.update({
                "status": "ok" if snippets else "ok_no_keyword",
                "document": {
                    "rcept_no": rcept,
                    "report_nm": audit.get("report_nm"),
                    "rcept_dt": audit.get("rcept_dt"),
                    "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}",
                    "text_chars": len(text or ""),
                },
                "snippets": snippets,
            })
            # Annotate investigation — never invent edge amounts from snippets alone
            if snippets:
                r["notes"] = list(r.get("notes") or []) + [
                    f"감사보고서 본문 키워드 {len(snippets)}건 (rcept {rcept}) — 잔액 확정 전 엣지 미작성"
                ]
                if r["classification"].startswith("법인·맵"):
                    r["classification"] = "법인 및 데이터센터 관련 공시 확인 · 본문 키워드 확보(잔액 수동확정 전)"
            time.sleep(0.25)
        except Exception as e:  # noqa: BLE001
            row_out["status"] = f"doc_error:{e}"
            r["notes"] = list(r.get("notes") or []) + [f"document fetch failed: {e}"]
        body_results.append(row_out)

    # Recompute classification counts
    by = {}
    for r in inv["results"]:
        by[r["classification"]] = by.get(r["classification"], 0) + 1
    inv["by_classification"] = by
    inv["body_scan_date"] = date.today().isoformat()
    inv["body_scan_file"] = "docs/opendart_borrower28_body_hits.json"
    INV.write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload = {
        "verification_date": date.today().isoformat(),
        "method": [
            "Latest 감사보고서 document() per resolved corp_code",
            "Keyword excerpts only — amounts nearby are NOT treated as verified outstanding",
            "No network edges written by this script",
        ],
        "results": body_results,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok = sum(1 for x in body_results if str(x["status"]).startswith("ok"))
    log(f"wrote {OUT} body_ok={ok}/{len(body_results)}")
    log(f"updated {INV}")


if __name__ == "__main__":
    main()
