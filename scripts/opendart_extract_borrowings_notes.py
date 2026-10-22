#!/usr/bin/env python3
"""Extract 차입금 note tables from cached DART audit-report ZIPs.

Fixes the pipeline gap where body_scan stopped after 12 early keyword hits
and never reached the borrowings note.

Writes docs/opendart_borrowings_note_extract.json
Does NOT invent amounts or auto-write edges for ambiguous rows.
Never prints API keys.
"""
from __future__ import annotations

import html
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "backend" / "data" / "opendart_cache" / "docs"
INV = ROOT / "docs" / "opendart_borrower28_investigation.json"
OUT = ROOT / "docs" / "opendart_borrowings_note_extract.json"

# Known institution name → node id (extend carefully; do not merge lookalikes).
NAME_TO_ID = {
    "주식회사 국민은행": "kb_bank",
    "국민은행": "kb_bank",
    "KB국민은행": "kb_bank",
    "대화은행 서울지점": "ubob_seoul",
    "대화은행서울지점": "ubob_seoul",
    "현대해상화재보험(주)": "hyundai_marine",
    "현대해상화재보험": "hyundai_marine",
    "주식회사 하나은행": "hana_bank",
    "하나은행": "hana_bank",
    "하나캐피탈(주)": "hana_capital",
    "하나캐피탈": "hana_capital",
    "신용협동조합중앙회": "shinhyup_federation",
    "신협중앙회": "shinhyup_federation",
    "농협은행": "nh_bank",
    "주식회사 농협은행": "nh_bank",
    "기업은행": "ibk_bank",
    "중소기업은행": "ibk_bank",
    "산업은행": "kdb",
    "한국산업은행": "kdb",
    "신한은행": "shinhan_bank",
    "주식회사 신한은행": "shinhan_bank",
    "우리은행": "woori_bank",
    "삼성화재해상보험": "samsung_fire",
    "삼성화재": "samsung_fire",
    "NH투자증권": "nh_inv_sec",
    "한국투자증권": "korea_inv_sec",
    "KB증권": "kb_sec",
}


def flatten_xml(raw: bytes) -> str:
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            t = raw.decode(enc)
            break
        except UnicodeDecodeError:
            t = None
    if t is None:
        t = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", t)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text)


def extract_note_chunk(text: str) -> str | None:
    """Locate the borrowings *schedule* note, not BS/CF line items.

    Earlier body_scan matched '장기차입금' in the balance sheet first and stopped
    after 12 hits — never reaching '12. 차입금 (1) … 차입처 …'. Prefer chunks that
    contain 차입처 / Term Loan / 약정한도.
    """
    patterns = [
        r"\d+\.\s*차입금\s*\(",
        r"\d+\.\s*차입금\b",
        r"\d+\.\s*장기차입금\b",
        r"\d+\.\s*단기차입금\b",
        r"장기차입금의\s*내역",
        r"차입금의\s*내역",
        r"차입금\s*현황",
        r"장단기차입금의\s*구성내역",
    ]
    candidates: list[tuple[int, str]] = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            start = m.start()
            # Skip cash-flow / BS one-liners like '2. 장기차입금 상환'
            head = text[start : start + 80]
            if re.search(r"차입금\s*상환|차입금\s*차입|장기차입금\s+\d", head):
                continue
            rest = text[start + 5 :]
            m2 = re.search(r"\s\d{1,2}\.\s+[가-힣A-Za-z(]", rest)
            end = start + 5 + m2.start() if m2 else min(len(text), start + 8000)
            chunk = text[start:end]
            if len(chunk) < 80:
                continue
            score = 0
            if "차입처" in chunk:
                score += 5
            if "Term Loan" in chunk or "텀론" in chunk:
                score += 3
            if "약정한도" in chunk or "당기말" in chunk:
                score += 2
            if "이자율" in chunk:
                score += 1
            candidates.append((score, chunk))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
    return candidates[0][1]


def find_lenders(chunk: str) -> list[dict]:
    found = []
    seen = set()
    for name, nid in NAME_TO_ID.items():
        if name in chunk and nid not in seen:
            # Grab nearby amount candidates (large integers)
            pos = chunk.find(name)
            window = chunk[max(0, pos - 40) : pos + 160]
            amounts = re.findall(r"(\d{1,3}(?:,\d{3}){2,})", window)
            found.append({
                "name_in_doc": name,
                "resolved_node_id": nid,
                "nearby_amounts_raw": amounts[:4],
                "context": window[:200],
            })
            seen.add(nid)
    return found


def read_zip_text(zpath: Path) -> str | None:
    try:
        with zipfile.ZipFile(zpath) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith((".xml", ".htm", ".html"))]
            if not names:
                return None
            # Prefer largest XML (full report)
            names.sort(key=lambda n: zf.getinfo(n).file_size, reverse=True)
            return flatten_xml(zf.read(names[0]))
    except Exception as e:
        return None


def main() -> None:
    inv = json.loads(INV.read_text(encoding="utf-8")) if INV.exists() else {"results": []}
    # Map corp → latest audit rcept from investigation
    targets = []
    for r in inv.get("results", []):
        primary = r.get("primary_corp") or {}
        doc = None
        for f in (r.get("filings") or []):
            if "감사보고서" in (f.get("report_nm") or ""):
                doc = f
                break
        # body_hits style
        bh = None
        targets.append({
            "id": r.get("id"),
            "seed_name": r.get("seed_name"),
            "corp_code": primary.get("corp_code") or r.get("corp_code"),
            "corp_name": primary.get("corp_name") or r.get("corp_name"),
            "map_node": (r.get("map_match") or {}).get("node_id") if isinstance(r.get("map_match"), dict) else r.get("map_node"),
        })

    # Enrich rcept from body_hits if present
    bh_path = ROOT / "docs" / "opendart_borrower28_body_hits.json"
    rcept_by_id = {}
    if bh_path.exists():
        bh = json.loads(bh_path.read_text(encoding="utf-8"))
        for r in bh.get("results", []):
            doc = r.get("document") or {}
            if doc.get("rcept_no"):
                rcept_by_id[r["id"]] = doc

    results = []
    for t in targets:
        doc = rcept_by_id.get(t["id"]) or {}
        rcept = doc.get("rcept_no")
        entry = {
            **t,
            "rcept_no": rcept,
            "report_nm": doc.get("report_nm"),
            "status": "no_rcept",
            "note_found": False,
            "lenders": [],
            "note_excerpt": None,
        }
        if not rcept:
            results.append(entry)
            continue
        zpath = DOCS / f"{rcept}.zip"
        if not zpath.exists():
            entry["status"] = "zip_missing"
            results.append(entry)
            continue
        text = read_zip_text(zpath)
        if not text:
            entry["status"] = "text_empty"
            results.append(entry)
            continue
        chunk = extract_note_chunk(text)
        if not chunk:
            entry["status"] = "note_not_found"
            entry["text_chars"] = len(text)
            results.append(entry)
            continue
        lenders = find_lenders(chunk)
        entry.update({
            "status": "ok",
            "note_found": True,
            "text_chars": len(text),
            "note_chars": len(chunk),
            "lenders": lenders,
            "note_excerpt": chunk[:1200],
            "has_term_loan": "Term Loan" in chunk or "텀론" in chunk,
            "has_당기말": "당기말" in chunk,
        })
        results.append(entry)

    OUT.write_text(
        json.dumps({
            "method": [
                "Read cached OpenDART document ZIP XML",
                "Locate 차입금/장기차입금 note section",
                "Match known lender legal names to node IDs",
                "Nearby amounts are candidates only — confirm before edge write",
            ],
            "pipeline_fix": (
                "Prior body_scan used LOAN_PAT with max_snips=12, capturing BS line items "
                "before the note table; lenders_mentioned stayed empty for gaya."
            ),
            "results": results,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    ok = sum(1 for r in results if r.get("note_found"))
    with_lenders = sum(1 for r in results if r.get("lenders"))
    print(f"OK notes={ok}/{len(results)} with_named_lenders={with_lenders} → {OUT}")


if __name__ == "__main__":
    main()
