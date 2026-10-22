#!/usr/bin/env python3
"""Investigate 28 named Korean DC PF borrowers via OpenDART (optimized).

Loads corp_codes_index once. Disclosure API only for resolved corps.
Writes docs/opendart_borrower28_investigation.json — does not invent edges/amounts.
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

OUT = ROOT / "docs" / "opendart_borrower28_investigation.json"
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
INDEX = ROOT / "backend" / "data" / "opendart_cache" / "corp_codes_index.json"

BORROWERS: list[dict] = [
    {"id": "b01", "label": "가야피에프브이(주)", "queries": ["가야피에프브이", "가야PFV"]},
    {"id": "b02", "label": "가산디씨에스엘원(주)", "queries": ["가산디씨에스엘원", "가산디씨에스엘원주식회사"]},
    {"id": "b03", "label": "다올데이터센터1호피에프브이(주)", "queries": ["다올데이터센터1호피에프브이", "다올데이터센터1호", "다올데이터센터제1호"]},
    {"id": "b04", "label": "더엣지영등포피에프브이(주)", "queries": ["더엣지영등포피에프브이", "더엣지영등포"]},
    {"id": "b05", "label": "디씨아이티와이부천피에프브이(주)", "queries": ["디씨아이티와이부천피에프브이", "디씨아이티와이부천"]},
    {"id": "b06", "label": "디토피에프브이(주)", "queries": ["디토피에프브이"]},
    {"id": "b07", "label": "마그나피에프브이(주)", "queries": ["마그나피에프브이"]},
    {"id": "b08", "label": "북항아이디씨피에프브이(주)", "queries": ["북항아이디씨피에프브이", "북항아이디씨"]},
    {"id": "b09", "label": "부산에코델타그린데이터센터PFV", "queries": ["부산에코델타그린데이터센터", "에코델타그린데이터센터"]},
    {"id": "b10", "label": "신영문봉PFV", "queries": ["신영문봉피에프브이", "신영문봉PFV", "신영문봉"]},
    {"id": "b11", "label": "신영식사피에프브이(주)", "queries": ["신영식사피에프브이", "신영식사"]},
    {"id": "b12", "label": "아이비케이부산에이아이데이터센터(주)", "queries": ["아이비케이부산에이아이데이터센터", "IBK부산에이아이데이터센터"]},
    {"id": "b13", "label": "안산그린에너지피에프브이(주)", "queries": ["안산그린에너지피에프브이", "안산그린에너지"]},
    {"id": "b14", "label": "에이아이팩토리포항피에프브이(주)", "queries": ["에이아이팩토리포항피에프브이", "에이아이팩토리포항"]},
    {"id": "b15", "label": "에포크피에프브이(주)", "queries": ["에포크피에프브이"]},
    {"id": "b16", "label": "엣지코어피에프브이(주)", "queries": ["엣지코어피에프브이"]},
    {"id": "b17", "label": "용인덕성데이터센터피에프브이(주)", "queries": ["용인덕성데이터센터피에프브이", "용인덕성데이터센터"]},
    {"id": "b18", "label": "청라아이디씨피에프브이(주)", "queries": ["청라아이디씨피에프브이", "청라아이디씨"]},
    {"id": "b19", "label": "케이인더스트리피에프브이(주)", "queries": ["케이인더스트리피에프브이"]},
    {"id": "b20", "label": "케이스퀘어데이터센터피에프브이(주)", "queries": ["케이스퀘어데이터센터피에프브이", "케이스퀘어데이터센터PFV", "케이스퀘어데이터센터"]},
    {"id": "b21", "label": "케이스퀘어부산장림데이터센터피에프브이(주)", "queries": ["케이스퀘어부산장림데이터센터피에프브이", "케이스퀘어부산장림"]},
    {"id": "b22", "label": "코람코시화데이터센터피에프브이(주)", "queries": ["코람코시화데이터센터피에프브이", "코람코시화데이터센터"]},
    {"id": "b23", "label": "캄스퀘어안산데이터센터피에프브이(주)", "queries": ["캄스퀘어안산데이터센터피에프브이", "캄스퀘어안산", "캠스퀘어안산"]},
    {"id": "b24", "label": "캄스퀘어용인데이터센터피에프브이(주)", "queries": ["캄스퀘어용인데이터센터피에프브이", "캄스퀘어용인", "캠스퀘어용인"]},
    {"id": "b25", "label": "파인디씨피에프브이(주)", "queries": ["파인디씨피에프브이"]},
    {"id": "b26", "label": "퍼시픽피치피에프브이(주)", "queries": ["퍼시픽피치피에프브이"]},
    {"id": "b27", "label": "하남엣지센터피에프브이(주)", "queries": ["하남엣지센터피에프브이", "하남엣지센터"]},
    {"id": "b28", "label": "하양에너지발전(주)", "queries": ["하양에너지발전", "하양에너지발전주식회사"]},
]

COUNTERPARTIES = [
    "KB증권", "한국투자증권", "메리츠증권", "NH투자증권", "미래에셋증권",
    "삼성증권", "신한투자증권", "하나증권", "키움증권", "한화투자증권",
    "IBK투자증권", "현대차증권", "유안타증권", "신영증권", "다올투자증권",
]

DC_HINTS = re.compile(r"데이터\s*센터|IDC|전산센터|AI\s*데이터|클라우드", re.I)
FIN_HINTS = re.compile(r"차입|대여|대출|PF|파이낸싱|보증|출자|투자|브릿지|본PF|담보|약정|유동화|ABCP", re.I)
# Exclude obvious non-DC when name alone is ambiguous (e.g. 하양에너지발전 may be power plant)
POWER_ONLY = re.compile(r"에너지발전|태양광|풍력|연료전지")


def norm(s: str) -> str:
    return re.sub(r"[\s()（）㈜株式会社주식회사]", "", s or "")


def log(msg: str) -> None:
    print(msg, flush=True)


def load_index() -> list[dict]:
    if not INDEX.exists():
        from app.opendart.client import OpenDartClient
        client = OpenDartClient()
        log("syncing corp codes…")
        client.sync_corp_codes()
    rows = json.loads(INDEX.read_text(encoding="utf-8"))
    log(f"corp index loaded: {len(rows)}")
    return rows


def find_corps(index: list[dict], queries: list[str]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for q in queries:
        qn = norm(q)
        if len(qn) < 3:
            continue
        for r in index:
            cn = norm(r.get("corp_name") or "")
            if qn not in cn:
                continue
            code = r.get("corp_code")
            if not code or code in seen:
                continue
            # Avoid very loose matches: require substantial overlap
            if len(qn) >= 6 and qn[:6] not in cn and qn not in cn:
                continue
            seen.add(code)
            out.append({
                "query": q,
                "corp_code": code,
                "corp_name": r.get("corp_name"),
                "stock_code": (r.get("stock_code") or "").strip() or None,
                "modify_date": r.get("modify_date"),
            })
    return out


def pick_counterparty(index: list[dict], firm: str) -> dict | None:
    fn = norm(firm)
    exact = [r for r in index if norm(r.get("corp_name") or "") == fn]
    if not exact:
        exact = [r for r in index if norm(r.get("corp_name") or "").startswith(fn)]
    listed = [r for r in exact if (r.get("stock_code") or "").strip()]
    row = (listed or exact or [None])[0]
    if not row:
        return None
    return {"query": firm, "corp_code": row.get("corp_code"), "corp_name": row.get("corp_name")}


def map_node_match(net: dict, queries: list[str]) -> list[dict]:
    hits = []
    for n in net.get("nodes") or []:
        blob = norm((n.get("name_ko") or "") + (n.get("name") or "") + n.get("id", ""))
        for q in queries:
            if norm(q) and norm(q) in blob:
                hits.append({
                    "id": n["id"],
                    "name_ko": n.get("name_ko") or n.get("name"),
                    "group": n.get("group"),
                    "entity_type": n.get("entity_type"),
                    "matched_query": q,
                })
                break
    return hits


def disclosure_scan(client, corp_code: str, *, bgn: str, end: str, max_pages: int = 3) -> dict:
    filings = []
    page_no = 1
    total_pages = 1
    status = "ok"
    while page_no <= min(total_pages, max_pages):
        disc = client.disclosure_list(
            corp_code=corp_code, bgn_de=bgn, end_de=end, page_count=100, page_no=page_no,
        )
        status = disc.get("status") or status
        if disc.get("status") == "013":
            break
        total_pages = int(disc.get("total_page") or 1)
        for row in disc.get("list") or []:
            title = row.get("report_nm") or ""
            filings.append({
                "rcept_no": row.get("rcept_no"),
                "report_nm": title,
                "rcept_dt": row.get("rcept_dt"),
                "corp_name": row.get("corp_name"),
                "dc_hint": bool(DC_HINTS.search(title)),
                "fin_hint": bool(FIN_HINTS.search(title)),
                "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={row.get('rcept_no')}" if row.get("rcept_no") else None,
            })
        page_no += 1
        time.sleep(0.15)
    return {
        "status": status,
        "filing_count": len(filings),
        "dc_title_hits": sum(1 for f in filings if f["dc_hint"]),
        "fin_title_hits": sum(1 for f in filings if f["fin_hint"]),
        "recent": filings[:20],
    }


def reverse_title_search(client, cps: list[dict], needles: list[str]) -> list[dict]:
    hits = []
    end = date.today().strftime("%Y%m%d")
    bgn = "20200101"
    needle_n = [norm(x) for x in needles if len(norm(x)) >= 5]
    if not needle_n:
        return hits
    for cp in cps:
        code = cp.get("corp_code")
        if not code:
            continue
        try:
            disc = client.disclosure_list(
                corp_code=code, bgn_de=bgn, end_de=end, page_count=100, page_no=1,
            )
        except Exception as e:  # noqa: BLE001
            continue
        for row in (disc.get("list") or [])[:50]:
            title = row.get("report_nm") or ""
            tn = norm(title)
            matched = [n for n in needle_n if n in tn]
            if matched:
                hits.append({
                    "counterparty": cp.get("corp_name"),
                    "counterparty_code": code,
                    "matched": matched,
                    "rcept_no": row.get("rcept_no"),
                    "report_nm": title,
                    "rcept_dt": row.get("rcept_dt"),
                    "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={row.get('rcept_no')}" if row.get("rcept_no") else None,
                })
        time.sleep(0.12)
    return hits


def classify(row: dict) -> str:
    corps = [c for c in row.get("corp_candidates") or [] if c.get("corp_code")]
    map_hits = row.get("map_nodes") or []
    disc = row.get("disclosures") or {}
    rev = [h for h in (row.get("reverse_hits") or []) if h.get("rcept_no")]
    name = (row.get("primary_corp") or {}).get("corp_name") or row.get("seed_name") or ""

    if POWER_ONLY.search(name) and not DC_HINTS.search(name) and not map_hits and not (disc.get("dc_title_hits") or 0):
        if corps:
            return "동명이인·사업 불일치 등으로 반영 제외(에너지발전 등 DC 미확인)"
    if not corps and not map_hits and not rev:
        return "검색했으나 관련 공시 미확인"
    if corps and (disc.get("filing_count") or 0) == 0 and not rev:
        return "법인 후보 확인 · 최근 공시 목록 없음"
    if corps and (disc.get("dc_title_hits") or 0) > 0:
        return "법인 및 데이터센터 관련 공시 제목 확인"
    if map_hits and corps:
        return "법인·맵 노드 확인 · 공시 본문 잔액은 추가 검증"
    if map_hits and not corps:
        return "맵 노드 존재 · DART 법인코드 미확정"
    if rev:
        return "상대방 공시 제목 역검색 히트 · 본문 검증 필요"
    if corps and (disc.get("fin_title_hits") or 0) > 0:
        return "일부 확인, 추가 정보 부족(금융 공시 제목만)"
    if corps:
        return "일부 확인, 추가 정보 부족"
    return "일부 확인, 추가 정보 부족"


def main() -> None:
    from app.opendart.client import OpenDartClient

    client = OpenDartClient()
    if not client.configured:
        OUT.write_text(json.dumps({
            "verification_date": date.today().isoformat(),
            "status": "skipped",
            "reason": "OPEN_DART_API_KEY not configured",
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        log("SKIP: no API key")
        return

    index = load_index()
    net = json.loads(NET.read_text(encoding="utf-8")) if NET.exists() else {"nodes": []}

    cps = []
    for firm in COUNTERPARTIES:
        row = pick_counterparty(index, firm)
        if row:
            cps.append(row)
    log(f"counterparties: {len(cps)}")

    end = date.today().strftime("%Y%m%d")
    bgn = "20180101"
    results = []

    for b in BORROWERS:
        log(f"scan {b['id']} {b['label']}")
        corps = find_corps(index, b["queries"])
        map_nodes = map_node_match(net, b["queries"])
        primary = corps[0] if corps else None
        disclosures: dict = {"status": "skipped", "filing_count": 0, "recent": []}
        if primary:
            try:
                disclosures = disclosure_scan(client, primary["corp_code"], bgn=bgn, end=end)
            except Exception as e:  # noqa: BLE001
                disclosures = {"status": "error", "error": str(e), "filing_count": 0, "recent": []}
        rev: list = []
        need_rev = (not primary) or ((disclosures.get("filing_count") or 0) < 2 and not map_nodes)
        if need_rev:
            try:
                rev = reverse_title_search(client, cps, b["queries"])
            except Exception as e:  # noqa: BLE001
                rev = [{"error": str(e)}]
        row = {
            "id": b["id"],
            "seed_name": b["label"],
            "queries": b["queries"],
            "corp_candidates": corps[:8],
            "primary_corp": primary,
            "map_nodes": map_nodes,
            "disclosures": disclosures,
            "reverse_hits": rev[:15],
            "classification": "",
            "notes": [],
        }
        if primary and POWER_ONLY.search(primary.get("corp_name") or ""):
            row["notes"].append("법인명에 에너지발전 포함 — DC PFV로 자동 확정하지 않음")
        row["classification"] = classify(row)
        results.append(row)

    summary = {
        "verification_date": date.today().isoformat(),
        "borrower_count": len(results),
        "by_classification": {},
        "opendart_configured": True,
        "method": [
            "corp_codes_index loaded once (local name match; lookalikes not merged)",
            "disclosure_list 2018→today title scan (dc/fin hints)",
            "reverse title search on major securities when borrower filings scarce",
            "Amounts / outstanding balances NOT invented — body verification required before edge write",
        ],
        "results": results,
    }
    for r in results:
        k = r["classification"]
        summary["by_classification"][k] = summary["by_classification"].get(k, 0) + 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"wrote {OUT}")
    for k, v in sorted(summary["by_classification"].items(), key=lambda x: -x[1]):
        log(f"  {v:2d}  {k}")


if __name__ == "__main__":
    main()
