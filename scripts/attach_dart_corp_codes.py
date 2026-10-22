# -*- coding: utf-8 -*-
"""Attach dart_corp_code from OpenDART body-scan results onto kr_securities nodes."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
HITS = ROOT / "docs" / "opendart_body_keyword_hits.json"
SUMMARY = ROOT / "docs" / "opendart_body_hit_summary.json"

NAME_TO_ID = {
    "한국투자증권": "korea_inv_sec",
    "KB증권": "kb_sec",
    "메리츠증권": "meritz_sec",
    "NH투자증권": "nh_inv_sec",
    "미래에셋증권": "mirae_asset_sec",
    "삼성증권": "samsung_sec",
    "신한투자증권": "shinhan_sec",
    "하나증권": "hana_sec",
    "대신증권": "daishin_sec",
    "키움증권": "kiwoom_sec",
    "IBK투자증권": "ibk_sec",
    "현대차증권": "hyundai_motor_sec",
    "SK증권": "sk_sec",
    "교보증권": "kyobo_sec",
    "유안타증권": "yuanta_sec",
    "한화투자증권": "hanwha_inv_sec",
    "다올투자증권": "daol_sec",
    "LS증권": "ls_sec",
    "신영증권": "shinyoung_sec",
    "DB증권": "db_sec",
    "유진투자증권": "eugene_inv_sec",
    "iM증권": "im_sec",
    "BNK투자증권": "bnk_sec",
    "부국증권": "bookook_sec",
    "케이프투자증권": "cape_sec",
}


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    hits = json.loads(HITS.read_text(encoding="utf-8"))
    by_id = {n["id"]: n for n in net["nodes"]}
    updated = 0
    for r in hits.get("results") or []:
        nid = NAME_TO_ID.get(r["firm"])
        if not nid or nid not in by_id:
            continue
        node = by_id[nid]
        node["dart_corp_code"] = r.get("corp_code")
        node["dart_corp_name"] = r.get("corp_name")
        if r.get("stock_code"):
            node["dart_stock_code"] = r["stock_code"]
        updated += 1
    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Append discovery notes to audit
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    discoveries = []
    for s in summary.get("by_firm") or []:
        for ex in s.get("examples") or []:
            sn = ex.get("snippet") or ""
            if "데이터센터" in sn or "IDC" in sn or "케이스퀘어" in sn:
                discoveries.append({
                    "firm": s["firm"],
                    "snippet": sn[:240],
                    "url": ex.get("url"),
                    "report": ex.get("report"),
                    "date": ex.get("date"),
                })
    note_path = ROOT / "docs" / "opendart_discovery_leads.json"
    note_path.write_text(json.dumps({
        "note": "Leads only — do not auto-create ACTIVE exposure edges from snippets.",
        "nodes_updated_with_dart_corp_code": updated,
        "leads": discoveries[:80],
        "firms_with_datacenter_keyword": summary.get("firms_with_datacenter_keyword"),
        "firms_no_filings": summary.get("firms_no_filings"),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("updated nodes", updated)
    print("leads", len(discoveries))
    print("wrote", note_path)


if __name__ == "__main__":
    main()
