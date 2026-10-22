#!/usr/bin/env python3
"""Fetch latest 감사보고서 ZIP for KR PFVs that have corp_code but no cached rcept."""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
INV = ROOT / "docs" / "pfv_spv_inventory.json"
OUT = ROOT / "docs" / "opendart_pfv_audit_fetch.json"


def main() -> None:
    from app.opendart.client import OpenDartClient

    client = OpenDartClient()
    if not client.configured:
        print("SKIP: no API key")
        return

    net = json.loads(NET.read_text(encoding="utf-8"))
    inv = json.loads(INV.read_text(encoding="utf-8")) if INV.exists() else {"items": []}
    results = []
    today = date.today().strftime("%Y%m%d")

    targets = []
    for it in inv.get("items", []):
        if it.get("dart_last_audit_rcept"):
            continue
        code = it.get("dart_corp_code")
        node = next((n for n in net["nodes"] if n["id"] == it["id"]), None)
        if not code and node:
            code = node.get("dart_corp_code")
        if not code:
            continue
        name = it.get("name") or ""
        if any(x in name for x in ("미공개", "LLC", "Helios", "Finance I", "ELN")):
            continue
        if (it.get("region") or (node or {}).get("region")) not in (None, "KR", ""):
            # still allow if Korean name
            if not any("\uac00" <= ch <= "\ud7a3" for ch in name):
                continue
        targets.append({"id": it["id"], "name": name, "corp_code": code})

    # Also stamp corp codes from investigation onto nodes that still lack rcept
    for t in targets:
        try:
            resp = client.disclosure_list(
                corp_code=t["corp_code"],
                bgn_de="20180101",
                end_de=today,
                page_count=100,
            )
        except Exception as e:
            results.append({**t, "status": f"list_error:{type(e).__name__}"})
            continue
        filings = resp.get("list") or []
        audits = [f for f in filings if "감사보고서" in (f.get("report_nm") or "")]
        audits.sort(key=lambda f: f.get("rcept_dt") or "", reverse=True)
        if not audits:
            results.append({**t, "status": "no_audit_in_list", "filing_count": len(filings)})
            time.sleep(0.25)
            continue
        latest = audits[0]
        rcept = latest.get("rcept_no")
        try:
            client.download_document_zip(rcept)
            text_info = client.document_text(rcept, max_chars=50_000)
            results.append({
                **t,
                "status": "fetched",
                "rcept_no": rcept,
                "report_nm": latest.get("report_nm"),
                "rcept_dt": latest.get("rcept_dt"),
                "text_chars": text_info.get("text_len"),
            })
            for n in net["nodes"]:
                if n["id"] == t["id"]:
                    n["dart_corp_code"] = t["corp_code"]
                    n["dart_last_audit_rcept"] = rcept
                    break
        except Exception as e:
            results.append({**t, "status": f"doc_error:{type(e).__name__}", "rcept_no": rcept})
        time.sleep(0.4)

    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fetched = sum(1 for r in results if r.get("status") == "fetched")
    print(f"targets={len(targets)} fetched={fetched}")


if __name__ == "__main__":
    main()
