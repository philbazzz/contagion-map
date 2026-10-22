#!/usr/bin/env python3
"""Re-audit every inventory PFV: cached report signal vs live network dart_loan edges.

Flags entities where the report likely has current borrowings but graph lacks dart_loan_*.
Does not auto-write network.json.
"""
from __future__ import annotations

import html
import json
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend/public/data/pf/network.json"
INV = ROOT / "docs/pfv_spv_inventory.json"
RESOLVE = ROOT / "docs/opendart_pfv_resolve_fetch.json"
CACHE = ROOT / "backend/data/opendart_cache/docs"
OUT = ROOT / "docs/pfv_source_vs_graph_audit.json"


def plain_from_zip(zpath: Path) -> str:
    texts = []
    with zipfile.ZipFile(zpath) as zf:
        for name in zf.namelist():
            if not name.lower().endswith((".xml", ".html", ".htm", ".txt")):
                continue
            raw = zf.read(name)
            for enc in ("utf-8", "cp949", "euc-kr"):
                try:
                    texts.append(raw.decode(enc))
                    break
                except Exception:
                    continue
    t = "\n".join(texts)
    t = html.unescape(t)
    t = re.sub(r"</t[rdh]>", "\n", t, flags=re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "\n", t)
    t = t.replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t


LENDER_HINT = re.compile(
    r"(은행|캐피탈|생명|화재|보험|증권|저축|신탁|농협|수협|신협|산업은행|기업은행|"
    r"국민은행|하나은행|신한은행|우리은행|제일차|제이차|제삼차|대출|론)"
)


def analyze_text(text: str) -> dict:
    has_note = bool(re.search(r"(장기차입금|단기차입금|유동성장기차입금|차입금)", text))
    # crude: look for "당기말" near 차입금 sections and large numbers
    note_hits = len(re.findall(r"(장기차입금|단기차입금|유동성장기차입금)", text))
    # extract windows around 차입금 notes
    windows = []
    for m in re.finditer(r"(?:주\s*석\s*)?\d+\s*[\.．]?\s*[^\n]{0,20}차입금", text):
        windows.append(text[m.start() : m.start() + 8000])
    if not windows:
        for m in re.finditer(r"장기차입금|단기차입금", text):
            windows.append(text[m.start() : m.start() + 5000])
            if len(windows) >= 3:
                break
    body = "\n".join(windows[:4])
    lender_lines = []
    for ln in body.splitlines():
        ln = ln.strip()
        if LENDER_HINT.search(ln) and re.search(r"\d", ln):
            lender_lines.append(ln[:120])
    # also count standalone lender-name lines followed by amounts in window
    named = set()
    for ln in body.splitlines():
        s = ln.strip()
        if not s or len(s) > 80:
            continue
        if LENDER_HINT.search(s) and not re.search(r"(당기말|전기말|약정|구분|차입처|이자율|만기|합계|소계|단위)", s):
            named.add(s)
    # BS signal: 장기차입금 / 단기차입금 line with number
    bs_long = re.search(r"장기차입금[^\d\-]{0,40}([\d,]+)", text[:15000])
    bs_short = re.search(r"단기차입금[^\d\-]{0,40}([\d,]+)", text[:15000])
    def parse_num(m):
        if not m:
            return None
        try:
            return int(m.group(1).replace(",", ""))
        except Exception:
            return None
    return {
        "has_borrowings_keyword": has_note,
        "note_keyword_hits": note_hits,
        "named_lender_candidates": sorted(named)[:40],
        "named_lender_candidate_count": len(named),
        "bs_long_term_sample": parse_num(bs_long),
        "bs_short_term_sample": parse_num(bs_short),
        "text_len": len(text),
    }


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    inv = json.loads(INV.read_text(encoding="utf-8"))
    resolve = {r["id"]: r for r in json.loads(RESOLVE.read_text(encoding="utf-8")).get("results", [])}

    rows = []
    for it in inv.get("items") or []:
        nid = it["id"]
        rr = resolve.get(nid) or {}
        rcept = it.get("dart_last_audit_rcept") or rr.get("rcept_no")
        zpath = CACHE / f"{rcept}.zip" if rcept else None
        dart_loans = [
            e for e in net["edges"]
            if e.get("target") == nid
            and e.get("relationship_type") == "PROJECT_LOAN"
            and str(e.get("id", "")).startswith("dart_loan_")
            and str(e.get("exposure_status", "")).startswith("ACTIVE")
        ]
        other_active = [
            e for e in net["edges"]
            if e.get("target") == nid
            and e.get("relationship_type") == "PROJECT_LOAN"
            and str(e.get("exposure_status", "")).startswith("ACTIVE")
            and not str(e.get("id", "")).startswith("dart_loan_")
            and e.get("amount_type") != "facility_total_context"
            and "facility_context" not in (e.get("roles") or [])
        ]

        entry = {
            "node_id": nid,
            "name": it.get("name"),
            "rcept": rcept,
            "zip_present": bool(zpath and zpath.exists()),
            "dart_loan_count": len(dart_loans),
            "other_active_loan_count": len(other_active),
            "dart_loan_ids": [e["id"] for e in dart_loans],
            "dart_loan_sum_eok": round(sum(e.get("amount_krw_eok") or 0 for e in dart_loans), 4),
            "report_signal": None,
            "audit_flag": None,
        }

        if not entry["zip_present"]:
            entry["audit_flag"] = "report_unavailable"
            rows.append(entry)
            continue

        try:
            text = plain_from_zip(zpath)
            sig = analyze_text(text)
        except Exception as ex:
            entry["audit_flag"] = f"zip_read_error:{ex}"
            rows.append(entry)
            continue

        entry["report_signal"] = sig
        bs_amt = sig.get("bs_long_term_sample") or sig.get("bs_short_term_sample") or 0
        likely_outstanding = (
            (bs_amt and bs_amt > 0)
            or sig["named_lender_candidate_count"] >= 2
            or sig["note_keyword_hits"] >= 2
        )

        if dart_loans:
            entry["audit_flag"] = "mapped_dart_loans_present"
        elif not likely_outstanding and sig["named_lender_candidate_count"] == 0:
            # check explicit zero phrases
            t = plain_from_zip(zpath)
            if re.search(r"차입부채가 없|차입금이 없|당기말.*차입금.*없", t):
                entry["audit_flag"] = "likely_no_outstanding"
            elif bs_amt == 0 or bs_amt is None:
                entry["audit_flag"] = "needs_manual_note_read"
            else:
                entry["audit_flag"] = "POSSIBLE_OMISSION"
        elif likely_outstanding and not dart_loans:
            entry["audit_flag"] = "POSSIBLE_OMISSION"
        else:
            entry["audit_flag"] = "needs_manual_note_read"

        # special: secondary-only edges without dart
        if other_active and not dart_loans:
            entry["audit_flag"] = entry["audit_flag"] + "+secondary_edges_only"

        rows.append(entry)

    by_flag = {}
    for r in rows:
        by_flag[r["audit_flag"]] = by_flag.get(r["audit_flag"], 0) + 1

    omissions = [r for r in rows if r["audit_flag"] and "POSSIBLE_OMISSION" in r["audit_flag"]]
    payload = {
        "verification_date": "2026-10-22",
        "inventory_count": len(rows),
        "by_flag": by_flag,
        "possible_omissions": [
            {
                "node_id": r["node_id"],
                "name": r["name"],
                "rcept": r["rcept"],
                "named_candidates": (r.get("report_signal") or {}).get("named_lender_candidate_count"),
                "bs_long": (r.get("report_signal") or {}).get("bs_long_term_sample"),
                "bs_short": (r.get("report_signal") or {}).get("bs_short_term_sample"),
                "other_active": r["other_active_loan_count"],
            }
            for r in omissions
        ],
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("by_flag", json.dumps(by_flag, ensure_ascii=True))
    print("possible_omissions", len(omissions))
    for o in omissions:
        print(" ", o["node_id"], o.get("named_candidates"), "bsL", o.get("bs_long"), "bsS", o.get("bs_short"), "other", o.get("other_active"))


if __name__ == "__main__":
    main()
