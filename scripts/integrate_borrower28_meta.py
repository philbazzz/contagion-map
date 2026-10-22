#!/usr/bin/env python3
"""Attach DART corp codes + audit sources to PF network for the 28 borrowers.

STRICT RULES:
- Does NOT invent outstanding balances or syndicate shares from keyword snippets.
- Does NOT create lender edges from name co-occurrence alone.
- May add isolated seed nodes when DART corp is confirmed but map lacked a node.
- May attach dart_corp_code / source ids to existing nodes.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
INV = ROOT / "docs" / "opendart_borrower28_investigation.json"
BODY = ROOT / "docs" / "opendart_borrower28_body_hits.json"
REPORT = ROOT / "docs" / "opendart_borrower28_integration.json"

# seed label → existing map node id (do not merge lookalikes)
SEED_TO_NODE = {
    "b01": None,  # 가야 — create seed if corp confirmed
    "b02": "gasan_dc_sl1",
    "b03": "keppel_ansan_pfv",  # 다올1호 → 케펠안산 (rename)
    "b04": None,  # 더엣지영등포 — no corp
    "b05": "dcity_bucheon_pfv",
    "b06": None,  # 디토
    "b07": "magna_pfv",
    "b08": "bukhang_idc_pfv",
    "b09": "busan_ecodelta_pfv",
    "b10": None,  # 신영문봉 — corp found
    "b11": None,  # 신영식사 — lookalike rejected
    "b12": None,
    "b13": None,  # 안산그린에너지
    "b14": None,
    "b15": None,  # 에포크
    "b16": "edgecore_pfv",
    "b17": "yongin_deokseong_pfv",
    "b18": "cheongna_idc_pfv",
    "b19": None,
    "b20": "casequare_pfv",
    "b21": "casequare_busan_jangnim_pfv",
    "b22": "koramco_siheung_pfv",
    "b23": "camsquare_pfv",
    "b24": "camsquare_yongin_pfv",
    "b25": "fine_dc_pfv",
    "b26": "peach_pfv",
    "b27": "hanam_edge_pfv",
    "b28": None,  # 하양에너지 — DC 미확인, do not add as DC PFV
}

NEW_SEED_IDS = {
    "b01": "gaya_pfv",
    "b06": "dito_pfv",
    "b10": "shinyoung_munbong_pfv",
    "b13": "ansan_green_energy_pfv",
    "b15": "epoch_pfv",
}


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    inv = json.loads(INV.read_text(encoding="utf-8"))
    body = json.loads(BODY.read_text(encoding="utf-8")) if BODY.exists() else {"results": []}
    body_by = {r["id"]: r for r in body.get("results") or []}
    inv_by = {r["id"]: r for r in inv["results"]}
    nodes_by = {n["id"]: n for n in net["nodes"]}

    added_nodes = []
    updated_nodes = []
    added_sources = []
    skipped = []

    for bid, map_id in SEED_TO_NODE.items():
        row = inv_by[bid]
        br = body_by.get(bid) or {}
        corp = row.get("primary_corp") or {}
        corp_code = corp.get("corp_code") or br.get("corp_code")
        corp_name = corp.get("corp_name") or br.get("corp_name")

        if bid == "b28":
            skipped.append({"id": bid, "reason": "에너지발전 — DC PFV로 반영 제외"})
            continue
        if bid == "b11":
            skipped.append({"id": bid, "reason": "유사명 제외 — 신영식사 법인 미확정"})
            continue
        if not corp_code and not map_id:
            skipped.append({"id": bid, "reason": "법인코드·맵노드 모두 없음 — 엣지/노드 미작성"})
            continue

        # Resolve / create node
        nid = map_id
        if not nid and bid in NEW_SEED_IDS and corp_code:
            nid = NEW_SEED_IDS[bid]
            if nid not in nodes_by:
                node = {
                    "id": nid,
                    "name": corp_name or row["seed_name"],
                    "name_ko": corp_name or row["seed_name"],
                    "group": "project_finance",
                    "entity_type": "spv",
                    "region": "KR",
                    "role": "차주 PFV",
                    "listed": False,
                    "ticker": None,
                    "exchange": None,
                    "sector": "datacenter_pf",
                    "display_size": 7,
                    "is_company": True,
                    "connection_status": "연결관계 확인 필요",
                    "description": (
                        f"DART 법인코드 {corp_code} 확인. "
                        "감사보고서 키워드만으로는 대주별 잔액을 확정하지 않아 금융 엣지를 자동 생성하지 않음."
                    ),
                    "dart_corp_code": corp_code,
                    "dart_verification_date": date.today().isoformat(),
                    "source_ids": [],
                    "roles": ["borrower", "spv"],
                }
                net["nodes"].append(node)
                nodes_by[nid] = node
                added_nodes.append(nid)

        if not nid or nid not in nodes_by:
            skipped.append({"id": bid, "reason": f"map node missing ({map_id})"})
            continue

        node = nodes_by[nid]
        changed = False
        if corp_code and node.get("dart_corp_code") != corp_code:
            node["dart_corp_code"] = corp_code
            changed = True
        if corp_name and not node.get("name_ko"):
            node["name_ko"] = corp_name
            changed = True
        # Rename note for 다올→케펠
        if bid == "b03":
            note = "조사 시드명 다올데이터센터1호피에프브이 → DART 법인 케펠데이터센터안산피에프브이"
            if note not in (node.get("description") or ""):
                node["description"] = ((node.get("description") or "") + " " + note).strip()
                changed = True

        # Attach audit source (reference only)
        doc = (br.get("document") or {})
        rcept = doc.get("rcept_no")
        if rcept:
            sid = f"dart_audit_{nid}_{rcept}"
            existing = {s.get("id") for s in net.get("sources") or []}
            if sid not in existing:
                src = {
                    "id": sid,
                    "title": doc.get("report_nm") or f"{corp_name or nid} 감사보고서",
                    "publisher": "DART",
                    "url": doc.get("url") or f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}",
                    "date": doc.get("rcept_dt"),
                    "status": "VERIFIED",
                    "notes": "OpenDART document_text 확인. 키워드 발췌만 보관 — 기관별 잔액은 수동 확정 전 엣지 미작성.",
                }
                net.setdefault("sources", []).append(src)
                added_sources.append(sid)
            sids = list(node.get("source_ids") or [])
            if sid not in sids:
                sids.append(sid)
                node["source_ids"] = sids
                changed = True
            node["dart_last_audit_rcept"] = rcept
            node["dart_verification_date"] = date.today().isoformat()
            changed = True

        if changed and nid not in added_nodes:
            updated_nodes.append(nid)

    meta = net.setdefault("meta", {})
    meta["opendart_borrower28"] = {
        "version": "2026-10-22",
        "investigation": "docs/opendart_borrower28_investigation.json",
        "body_hits": "docs/opendart_borrower28_body_hits.json",
        "integration": "docs/opendart_borrower28_integration.json",
        "note": "Amounts not invented from keyword co-occurrence; arranger ≠ exposure.",
    }

    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "verification_date": date.today().isoformat(),
        "added_nodes": added_nodes,
        "updated_nodes": sorted(set(updated_nodes)),
        "added_sources": added_sources,
        "skipped": skipped,
        "edges_added": [],
        "edges_updated": [],
        "policy": [
            "No lender edges from snippet co-occurrence",
            "No equal-split of syndicate totals",
            "Unknown balances stay unknown",
            "하양에너지발전 excluded as non-DC",
            "신영식사 lookalike excluded",
        ],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "added_nodes": added_nodes,
        "updated_nodes": len(set(updated_nodes)),
        "added_sources": len(added_sources),
        "skipped": len(skipped),
        "nodes": len(net["nodes"]),
        "edges": len(net["edges"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
