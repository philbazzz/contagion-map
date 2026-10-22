#!/usr/bin/env python3
"""Resolve DART corp codes for KR PFV/SPC inventory items and fetch latest audit OR periodic report ZIP.

Preference order for filings:
1. 감사보고서 (latest by rcept_dt)
2. 사업보고서 / 반기보고서 / 분기보고서 (for borrowings notes when no audit)

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
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
INV = ROOT / "docs" / "pfv_spv_inventory.json"
INDEX = ROOT / "backend" / "data" / "opendart_cache" / "corp_codes_index.json"
OUT = ROOT / "docs" / "opendart_pfv_resolve_fetch.json"


def norm(s: str) -> str:
    return re.sub(r"[\s()（）㈜株式会社주식회사]", "", s or "")


def find_corp(index: list[dict], name: str) -> dict | None:
    qn = norm(name)
    if len(qn) < 4:
        return None
    exact = [r for r in index if norm(r.get("corp_name") or "") == qn]
    if exact:
        return exact[0]
    # strong contains
    hits = [r for r in index if qn in norm(r.get("corp_name") or "") or norm(r.get("corp_name") or "") in qn]
    hits = [h for h in hits if len(norm(h.get("corp_name") or "")) >= len(qn) - 2]
    if len(hits) == 1:
        return hits[0]
    # prefer PFV/SPC suffix match
    pfv = [h for h in hits if "피에프브이" in (h.get("corp_name") or "") or "PFV" in (h.get("corp_name") or "")]
    if len(pfv) == 1:
        return pfv[0]
    return None


def pick_filing(filings: list[dict]) -> dict | None:
    def score(f: dict) -> tuple:
        nm = f.get("report_nm") or ""
        dt = f.get("rcept_dt") or ""
        if "감사보고서" in nm:
            tier = 3
        elif "사업보고서" in nm:
            tier = 2
        elif "반기보고서" in nm:
            tier = 1
        elif "분기보고서" in nm:
            tier = 0
        else:
            tier = -1
        return (tier, dt)

    ranked = sorted(filings, key=score, reverse=True)
    for f in ranked:
        if score(f)[0] >= 0:
            return f
    return None


def main() -> None:
    from app.opendart.client import OpenDartClient

    client = OpenDartClient()
    if not client.configured:
        print("SKIP: no API key")
        return
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else []
    net = json.loads(NET.read_text(encoding="utf-8"))
    inv = json.loads(INV.read_text(encoding="utf-8")) if INV.exists() else {"items": []}
    today = date.today().strftime("%Y%m%d")
    results = []

    for it in inv.get("items", []):
        nid = it["id"]
        name = it.get("name") or ""
        if nid.startswith("seed:"):
            continue
        # skip US / unnamed
        if any(x in name for x in ("LLC", "Helios", "Finance I", "ELN", "미공개", "미확인")):
            results.append({"id": nid, "status": "skip_non_dart_target"})
            continue
        node = next((n for n in net["nodes"] if n["id"] == nid), None)
        code = it.get("dart_corp_code") or (node or {}).get("dart_corp_code")
        resolved = None
        if not code:
            resolved = find_corp(index, name)
            if not resolved and name.endswith("PFV"):
                resolved = find_corp(index, name.replace("PFV", "피에프브이"))
            if resolved:
                code = resolved.get("corp_code")
        if not code:
            results.append({"id": nid, "name": name, "status": "corp_unresolved"})
            continue

        # already have audit zip?
        rcept = it.get("dart_last_audit_rcept") or (node or {}).get("dart_last_audit_rcept")
        if rcept and (ROOT / "backend/data/opendart_cache/docs" / f"{rcept}.zip").exists():
            # stamp corp if missing
            if node and not node.get("dart_corp_code"):
                node["dart_corp_code"] = code
            results.append({"id": nid, "corp_code": code, "rcept_no": rcept, "status": "already_cached"})
            continue

        try:
            resp = client.disclosure_list(corp_code=code, bgn_de="20180101", end_de=today, page_count=100)
        except Exception as e:
            results.append({"id": nid, "corp_code": code, "status": f"list_error:{type(e).__name__}"})
            continue
        filings = resp.get("list") or []
        chosen = pick_filing(filings)
        if not chosen:
            results.append({"id": nid, "corp_code": code, "status": "no_usable_filing", "filing_count": len(filings)})
            time.sleep(0.2)
            continue
        rcept = chosen["rcept_no"]
        try:
            client.download_document_zip(rcept)
            results.append({
                "id": nid,
                "name": name,
                "corp_code": code,
                "corp_name_resolved": (resolved or {}).get("corp_name"),
                "rcept_no": rcept,
                "report_nm": chosen.get("report_nm"),
                "rcept_dt": chosen.get("rcept_dt"),
                "status": "fetched",
            })
            if node:
                node["dart_corp_code"] = code
                node["dart_last_audit_rcept"] = rcept
        except Exception as e:
            results.append({"id": nid, "corp_code": code, "rcept_no": rcept, "status": f"doc_error:{type(e).__name__}"})
        time.sleep(0.35)

    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fetched = sum(1 for r in results if r.get("status") == "fetched")
    cached = sum(1 for r in results if r.get("status") == "already_cached")
    unresolved = sum(1 for r in results if r.get("status") == "corp_unresolved")
    print(f"fetched={fetched} cached={cached} unresolved={unresolved} total={len(results)}")


if __name__ == "__main__":
    main()
