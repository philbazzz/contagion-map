#!/usr/bin/env python3
"""Full DC PFV/SPC borrowings inventory + current-period lender mapping.

Rules:
- Inventory = all project_finance / *_pfv / spv|spc entities in nodes+hidden_nodes
  union borrower28 seed list.
- Use CURRENT-PERIOD columns only (당기말/당기/당분기말/당반기말). Never treat 전기말 as current.
- Named lenders → PROJECT_LOAN edges in frontend/public/data/pf/network.json.
- Unnamed groups → facility_total_context only.
- Honest coverage statuses in docs/pfv_borrowings_coverage.json.

Never prints OPEN_DART_API_KEY.
"""
from __future__ import annotations

import html
import json
import re
import zipfile
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET_PATH = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
DOCS_ZIP = ROOT / "backend" / "data" / "opendart_cache" / "docs"
INV28 = ROOT / "docs" / "opendart_borrower28_investigation.json"
BODY = ROOT / "docs" / "opendart_borrower28_body_hits.json"
OUT_INV = ROOT / "docs" / "pfv_spv_inventory.json"
OUT_COV = ROOT / "docs" / "pfv_borrowings_coverage.json"
OUT_EXTRACT = ROOT / "docs" / "pfv_borrowings_current_extract.json"

# Legal-name fragments → node id (do not merge lookalikes).
LENDER_MAP: list[tuple[str, str]] = [
    ("주식회사 국민은행", "kb_bank"),
    ("(주)국민은행", "kb_bank"),
    ("국민은행", "kb_bank"),
    ("KB국민은행", "kb_bank"),
    ("대화은행 서울지점", "ubob_seoul"),
    ("대화은행서울지점", "ubob_seoul"),
    ("현대해상화재보험(주)", "hyundai_marine"),
    ("현대해상화재보험", "hyundai_marine"),
    ("주식회사 하나은행", "hana_bank"),
    ("(주)하나은행", "hana_bank"),
    ("하나은행", "hana_bank"),
    ("하나캐피탈(주)", "hana_capital"),
    ("하나캐피탈", "hana_capital"),
    ("신용협동조합중앙회", "shinhyup_federation"),
    ("신협중앙회", "shinhyup_federation"),
    ("농협은행", "nh_bank"),
    ("주식회사 농협은행", "nh_bank"),
    ("(주)농협은행", "nh_bank"),
    ("중소기업은행", "ibk_bank"),
    ("기업은행", "ibk_bank"),
    ("한국산업은행", "kdb"),
    ("산업은행", "kdb"),
    ("주식회사 신한은행", "shinhan_bank"),
    ("(주)신한은행", "shinhan_bank"),
    ("신한은행", "shinhan_bank"),
    ("우리은행", "woori_bank"),
    ("(주)IBK캐피탈", "ibk_capital"),
    ("IBK캐피탈", "ibk_capital"),
    ("신한캐피탈주식회사", "shinhan_capital"),
    ("신한캐피탈(주)", "shinhan_capital"),
    ("신한캐피탈㈜", "shinhan_capital"),
    ("신한캐피탈", "shinhan_capital"),
    ("신한투자증권주식회사", "shinhan_sec"),
    ("신한투자증권(주)", "shinhan_sec"),
    ("신한투자증권㈜", "shinhan_sec"),
    ("신한투자증권", "shinhan_sec"),
    ("KB손해보험", "kb_ins"),
    ("삼성화재해상보험", "samsung_fire"),
    ("삼성화재", "samsung_fire"),
    ("한화생명보험(주)", "hanwha_life"),
    ("한화생명보험", "hanwha_life"),
    ("한화생명", "hanwha_life"),
    ("현대캐피탈(주)", "hyundai_capital"),
    ("현대캐피탈", "hyundai_capital"),
    ("메리츠화재해상보험(주)", "meritz_fire"),
    ("메리츠화재", "meritz_fire"),
    ("메리츠캐피탈(주)", "meritz_capital"),
    ("메리츠캐피탈", "meritz_capital"),
    ("한국투자증권", "korea_inv_sec"),
    ("NH투자증권", "nh_inv_sec"),
    ("엔에이치투자증권", "nh_inv_sec"),
    ("수협은행", "suhyup_bank"),
    ("한국증권금융 주식회사", "korea_sec_finance"),
    ("한국증권금융", "korea_sec_finance"),
    ("주식회사 신영", "shinyoung"),
    ("(주)신영", "shinyoung"),
    ("원창아이디씨㈜", "wonchang_idc"),
    ("원창아이디씨", "wonchang_idc"),
    ("쥐피에스23제일차㈜", "gps23_spc"),
    ("쥐피에스23제일차", "gps23_spc"),
    ("㈜이도", "ido"),
    ("(주)이도", "ido"),
    ("신한캐피탈㈜", "shinhan_capital"),
    ("신한투자증권㈜", "shinhan_sec"),
    ("엠에스이디씨제일차", "msedc1_spc"),
    ("엠에스이디씨제이차", "msedc2_spc"),
    ("Tr.A_엠에스이디씨제일차", "msedc1_spc"),
    ("Tr.B_엠에스이디씨제이차", "msedc2_spc"),
    ("가온해제오차 주식회사", "gaon_haeje5_spc"),
    ("가온해제오차", "gaon_haeje5_spc"),
    ("(주)IBK캐피탈", "ibk_capital"),
    ("메리츠화재해상보험(주)", "meritz_fire"),
    ("JT저축은행(주)", "jt_savings"),
    ("(주)다올저축은행", "daol_savings"),
    ("(주)애큐온저축은행", "acuon_savings"),
    ("(주)애큐온캐피탈", "acuon_capital"),
    ("에이원브리즈(주)", "a1_breeze"),
    ("에이원리빙(주)", "a1_living"),
]

# Seed name → preferred map node (from borrower28 + known aliases)
SEED_NODE = {
    "b01": "gaya_pfv",
    "b02": "gasan_dc_sl1",
    "b03": "keppel_ansan_pfv",
    "b05": "dcity_bucheon_pfv",
    "b06": "dito_pfv",
    "b07": "magna_pfv",
    "b08": "bukhang_idc_pfv",
    "b09": "busan_ecodelta_pfv",
    "b10": "shinyoung_munbong_pfv",
    "b13": "ansan_green_energy_pfv",
    "b15": "epoch_pfv",
    "b16": "edgecore_pfv",
    "b17": "yongin_deokseong_pfv",
    "b18": "cheongna_idc_pfv",
    "b20": "casequare_pfv",
    "b21": "casequare_busan_jangnim_pfv",
    "b22": "koramco_siheung_pfv",
    "b23": "camsquare_pfv",
    "b24": "camsquare_yongin_pfv",
    "b25": "fine_dc_pfv",
    "b26": "peach_pfv",
    "b27": "hanam_edge_pfv",
}

AMOUNT_RE = re.compile(r"(\d{1,3}(?:,\d{3})+|\d+)")


def eok(krw: int) -> float:
    return round(krw / 1e8, 4)


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
    return re.sub(r"\s+", " ", html.unescape(text))


def read_zip_text(zpath: Path) -> str | None:
    try:
        with zipfile.ZipFile(zpath) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith((".xml", ".htm", ".html"))]
            if not names:
                return None
            names.sort(key=lambda n: zf.getinfo(n).file_size, reverse=True)
            return flatten_xml(zf.read(names[0]))
    except Exception:
        return None


def extract_note_chunk(text: str) -> str | None:
    patterns = [
        r"\d+\.\s*차입금\s*\(",
        r"\d+\.\s*차입금\b",
        r"\d+\.\s*장기차입금\b",
        r"\d+\.\s*단기차입금\b",
        r"장단기차입금의\s*구성내역",
        r"장기차입금의\s*내역",
        r"단기차입금의\s*내역",
        r"차입금의\s*내역",
    ]
    candidates: list[tuple[int, str]] = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            head = text[m.start() : m.start() + 80]
            if re.search(r"차입금\s*상환|차입금\s*차입|장기차입금\s+\d", head):
                continue
            rest = text[m.start() + 5 :]
            m2 = re.search(r"\s\d{1,2}\.\s+[가-힣A-Za-z(]", rest)
            end = m.start() + 5 + m2.start() if m2 else min(len(text), m.start() + 9000)
            chunk = text[m.start() : end]
            if len(chunk) < 100:
                continue
            score = 0
            if "차입처" in chunk:
                score += 5
            if "당기말" in chunk or "당기" in chunk:
                score += 2
            if "Term Loan" in chunk:
                score += 2
            if "약정한도" in chunk or "이자율" in chunk:
                score += 1
            candidates.append((score, chunk))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
    return candidates[0][1]


def detect_unit(chunk: str) -> str:
    # Prefer explicit unit near table headers
    m = re.search(r"\(단위\s*[:：]?\s*(원|천원|백만원)\)", chunk)
    if m:
        return m.group(1)
    if "단위:천원" in chunk.replace(" ", "") or "단위 : 천원" in chunk:
        return "천원"
    if "단위:백만원" in chunk.replace(" ", ""):
        return "백만원"
    return "원"


def to_krw(raw: str, unit: str) -> int:
    n = int(raw.replace(",", ""))
    if unit == "천원":
        return n * 1_000
    if unit == "백만원":
        return n * 1_000_000
    return n


def split_current_prior(chunk: str) -> tuple[str, str | None]:
    """Prefer 당기 section; keep 전기 separately.

    Do NOT split on the intro phrase '당기말 및 전기말' — that truncated gaya's
    entire Term Loan table in an earlier pass.
    """
    # Section headers only
    m_cur = re.search(r"\(당기\)|\(당기말\)|1\)\s*당기말|당기말\s*\(단위", chunk)
    m_pri = re.search(r"\(전기\)|\(전기말\)|2\)\s*전기말|전기말\s*\(단위", chunk)
    if m_cur and m_pri and m_pri.start() > m_cur.start():
        return chunk[m_cur.start() : m_pri.start()], chunk[m_pri.start() :]
    if m_cur and not m_pri:
        return chunk[m_cur.start() :], None
    # Dual-column single table (당기말 | 전기말 as columns): keep full chunk;
    # callers must not treat the rightmost column as current without checks.
    return chunk, None


def parse_lender_rows(current_chunk: str, unit: str) -> list[dict]:
    """Extract named lenders with a nearby large amount from current-period text."""
    rows = []
    seen_edges = set()
    # Sort longer names first to avoid partial overwrite
    names = sorted(LENDER_MAP, key=lambda x: len(x[0]), reverse=True)
    used_spans: list[tuple[int, int]] = []

    for name, nid in names:
        start = 0
        while True:
            pos = current_chunk.find(name, start)
            if pos < 0:
                break
            # skip if overlapping a longer prior match
            if any(a <= pos < b for a, b in used_spans):
                start = pos + len(name)
                continue
            window = current_chunk[pos : pos + 220]
            # Skip if this window is clearly in a prior-period-only clause when dual markers exist
            amounts = AMOUNT_RE.findall(window)
            # Filter tiny note refs
            big = [a for a in amounts if int(a.replace(",", "")) >= 1000]
            if not big:
                start = pos + len(name)
                continue
            # Heuristic: last large number in window often = 당기말 when columns are 한도/당기말
            # Prefer second-to-last if two big numbers (limit, outstanding)
            if len(big) >= 2:
                outstanding_raw = big[-1]
                limit_raw = big[-2]
            else:
                outstanding_raw = big[-1]
                limit_raw = None
            # Group markers: "외 N곳"
            group = bool(re.search(r"외\s*\d+\s*곳", window))
            key = (nid, outstanding_raw, name)
            if key in seen_edges:
                start = pos + len(name)
                continue
            seen_edges.add(key)
            used_spans.append((pos, pos + len(name)))
            rows.append({
                "name_in_doc": name,
                "node_id": nid,
                "outstanding_raw": outstanding_raw,
                "limit_raw": limit_raw,
                "outstanding_krw": to_krw(outstanding_raw, unit),
                "limit_krw": to_krw(limit_raw, unit) if limit_raw else None,
                "group_unnamed": group,
                "context": window[:180],
            })
            start = pos + len(name)
    return rows


def is_dc_spv(n: dict) -> bool:
    et = (n.get("entity_type") or "").lower()
    gid = n.get("group") or ""
    nid = n.get("id") or ""
    sec = n.get("sector") or ""
    if et in ("spv", "spc", "pfv"):
        return True
    if gid == "project_finance":
        return True
    if nid.endswith("_pfv") or nid.endswith("_spc"):
        return True
    if "datacenter_pf" in sec:
        return True
    roles = n.get("roles") or []
    if "borrower_spv" in roles or "spv" in roles:
        return True
    return False


def rcept_from_sources(n: dict) -> str | None:
    for sid in n.get("source_ids") or []:
        m = re.search(r"(20\d{12})$", str(sid))
        if m:
            return m.group(1)
        m = re.search(r"(20\d{12})", str(sid))
        if m:
            return m.group(1)
    return n.get("dart_last_audit_rcept")


def build_inventory(net: dict) -> list[dict]:
    items = {}
    for n in net.get("nodes") or []:
        if not is_dc_spv(n):
            continue
        items[n["id"]] = {
            "id": n["id"],
            "name": n.get("name_ko") or n.get("name"),
            "dart_corp_code": n.get("dart_corp_code"),
            "dart_last_audit_rcept": rcept_from_sources(n),
            "visibility": "visible",
            "region": n.get("region"),
            "source": "network.nodes",
        }
    for n in net.get("hidden_nodes") or []:
        if not is_dc_spv(n):
            continue
        if n["id"] in items:
            continue
        items[n["id"]] = {
            "id": n["id"],
            "name": n.get("name_ko") or n.get("name"),
            "dart_corp_code": n.get("dart_corp_code"),
            "dart_last_audit_rcept": n.get("dart_last_audit_rcept"),
            "visibility": "hidden_nodes",
            "region": n.get("region"),
            "source": "network.hidden_nodes",
        }

    # Merge borrower28 seeds
    if INV28.exists():
        inv = json.loads(INV28.read_text(encoding="utf-8"))
        rcept_by = {}
        if BODY.exists():
            for r in json.loads(BODY.read_text(encoding="utf-8")).get("results", []):
                doc = r.get("document") or {}
                if doc.get("rcept_no"):
                    rcept_by[r["id"]] = doc
        for r in inv.get("results", []):
            bid = r["id"]
            node_id = SEED_NODE.get(bid)
            primary = r.get("primary_corp") or {}
            doc = rcept_by.get(bid) or {}
            # pick latest audit from disclosures.recent
            recent = ((r.get("disclosures") or {}).get("recent") or [])
            audits = [f for f in recent if "감사보고서" in (f.get("report_nm") or "")]
            if audits and not doc.get("rcept_no"):
                doc = audits[0]
            if node_id and node_id in items:
                it = items[node_id]
                it["borrower28_id"] = bid
                it["seed_name"] = r.get("seed_name")
                if not it.get("dart_corp_code"):
                    it["dart_corp_code"] = primary.get("corp_code")
                if doc.get("rcept_no"):
                    it["dart_last_audit_rcept"] = doc.get("rcept_no")
                    it["report_nm"] = doc.get("report_nm")
                    it["rcept_dt"] = doc.get("rcept_dt")
            elif node_id:
                items[node_id] = {
                    "id": node_id,
                    "name": primary.get("corp_name") or r.get("seed_name"),
                    "dart_corp_code": primary.get("corp_code"),
                    "dart_last_audit_rcept": doc.get("rcept_no"),
                    "report_nm": doc.get("report_nm"),
                    "rcept_dt": doc.get("rcept_dt"),
                    "visibility": "missing_from_graph",
                    "borrower28_id": bid,
                    "seed_name": r.get("seed_name"),
                    "source": "borrower28_seed",
                }
            else:
                items[f"seed:{bid}"] = {
                    "id": f"seed:{bid}",
                    "name": r.get("seed_name"),
                    "dart_corp_code": primary.get("corp_code"),
                    "dart_last_audit_rcept": doc.get("rcept_no"),
                    "report_nm": doc.get("report_nm"),
                    "visibility": "no_map_node",
                    "borrower28_id": bid,
                    "seed_name": r.get("seed_name"),
                    "source": "borrower28_unresolved",
                    "skip_reason": (r.get("notes") or [None])[0] if isinstance(r.get("notes"), list) else r.get("classification"),
                }
    return sorted(items.values(), key=lambda x: x["id"])


def promote_hidden(net: dict, node_id: str) -> bool:
    ids = {n["id"] for n in net["nodes"]}
    if node_id in ids:
        return True
    hidden = net.get("hidden_nodes") or []
    for i, n in enumerate(hidden):
        if n.get("id") == node_id:
            p = deepcopy(n)
            p.pop("map_hidden", None)
            p["display_size"] = max(float(p.get("display_size") or 1), 1)
            for k in ("roles", "key_drivers", "source_ids"):
                if not isinstance(p.get(k), list):
                    p[k] = []
            net["nodes"].append(p)
            hidden.pop(i)
            net["hidden_nodes"] = hidden
            return True
    return False


def ensure_source(net: dict, src_id: str, title: str, url: str, rcept: str) -> None:
    sources = net.setdefault("sources", [])
    if any(s.get("id") == src_id for s in sources):
        return
    sources.append({
        "id": src_id,
        "title": title,
        "publisher": "DART",
        "date": f"{rcept[:4]}-{rcept[4:6]}-{rcept[6:8]}" if rcept and len(rcept) >= 8 else None,
        "url": url,
        "used_for": "차입금 주석 (당기말)",
        "kind": "filing",
        "dart_receipt_number": rcept,
    })


def make_loan_edge(borrower: str, row: dict, meta: dict) -> dict:
    krw_eok = eok(row["outstanding_krw"])
    rcept = meta["rcept"]
    src_id = f"dart_audit_{borrower}_{rcept}"
    eid = f"dart_loan_{row['node_id']}_{borrower}_{row['outstanding_raw'].replace(',', '')}"
    # shorten id
    eid = re.sub(r"[^a-zA-Z0-9_]", "_", eid)[:96]
    return {
        "id": eid,
        "source": row["node_id"],
        "target": borrower,
        "relationship_type": "PROJECT_LOAN",
        "roles": ["lender"] if not row.get("group_unnamed") else ["facility_context"],
        "source_ids": [src_id],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_krw_eok": krw_eok,
        "amount_type": "facility_total_context" if row.get("group_unnamed") else "outstanding_principal",
        "amount_unit": "억원",
        "amount_note": (
            f"{meta.get('note_label', '차입금 주석')} 당기말 {row['name_in_doc']} "
            f"{row['outstanding_krw']:,}원"
            + (" (외 N곳 그룹 — 개별 배분 미공개)" if row.get("group_unnamed") else "")
        ),
        "amount_as_of": meta.get("as_of") or "2025-12-31",
        "impact_channel": "financial",
        "source_status": "VERIFIED",
        "label": f"{row['name_in_doc']} → {borrower} · {krw_eok:g}억",
        "impact_label": f"{row['name_in_doc']} 당기말 {krw_eok:g}억",
        "explanation": row.get("context") or "",
        "transmission_class": "direct",
        "exposure_status": "ACTIVE_CONFIRMED",
        "relationship_status": "current",
        "shock_eligible": not bool(row.get("group_unnamed")),
        "layer": "fact",
        "evidence_kind": "dart_audit_note",
        "evidence_status": "DART 감사보고서 차입금 주석 당기말",
        "evidence_level": "company_filing",
        "participation_path": "직접 대출",
        "participation_directness": "direct",
        "contingent_obligation": False,
        "project_name": meta.get("borrower_name"),
        "source_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}",
        "source_title": meta.get("report_nm") or f"{meta.get('borrower_name')} 감사보고서",
        "source_date": f"{rcept[:4]}-{rcept[4:6]}-{rcept[6:8]}",
        "dart_receipt_number": rcept,
        "verification_date": "2026-10-22",
        "facility_limit_krw_eok": eok(row["limit_krw"]) if row.get("limit_krw") else None,
        "stress_direction": "차주 부실 → 대주 신용 익스포저",
        "exposure_kind": "facility_total_context" if row.get("group_unnamed") else "loan_principal_outstanding",
        "period_basis": "current_period_only",
        "verification_gap": "개별 배분 미공개" if row.get("group_unnamed") else None,
    }


def classify_status(item: dict, extract: dict | None) -> str:
    if item.get("visibility") == "no_map_node":
        return "Report unavailable" if not item.get("dart_last_audit_rcept") else "Latest report lacks sufficient detail"
    if not item.get("dart_last_audit_rcept"):
        return "Report unavailable"
    if not extract:
        return "Not yet reviewed"
    st = extract.get("status")
    if st == "zip_missing":
        return "Report unavailable"
    if st == "note_not_found":
        return "Latest report lacks sufficient detail"
    if st == "ok":
        lenders = extract.get("current_lenders") or []
        if not lenders:
            # note exists but no named mapped lenders
            if "차입처" in (extract.get("note_excerpt") or ""):
                return "Reviewed — borrowings disclosed but lenders unnamed"
            return "Reviewed — no outstanding borrowings disclosed"
        return "Reviewed and mapped"
    return "Not yet reviewed"


def main() -> None:
    net = json.loads(NET_PATH.read_text(encoding="utf-8"))
    inventory = build_inventory(net)
    OUT_INV.write_text(json.dumps({"count": len(inventory), "items": inventory}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    extracts = []
    coverage = []
    edges = net["edges"]
    by_id = {e["id"]: i for i, e in enumerate(edges)}
    added, replaced, skipped = [], [], []

    # Prefer existing curated gaya edges — do not duplicate via heuristic
    protected_prefixes = (
        "dart_loan_kb_gaya_",
        "dart_loan_ubob_gaya_",
        "dart_loan_hyundai_marine_gaya_",
        "dart_loan_shinhyup_gaya_",
        "dart_loan_hana_bank_gaya_",
        "dart_loan_hana_capital_gaya_",
        "dart_facility_gaya_",
        "dart_loan_ibk_dito_",
        "dart_loan_kdb_dito_",
        "dart_loan_ibk_capital_busan_",
        "dart_loan_kb_ins_edgecore",
        "dart_loan_hyundai_marine_edgecore",
        "dart_loan_shinhan_capital_keppel_",
        "dart_loan_shinhan_sec_keppel_",
        "dart_loan_shinhan_capital_cheongna",
        "dart_loan_shinhan_sec_cheongna",
        "dart_loan_kb_magna",
        "dart_loan_shinhan_magna",
        "dart_loan_hana_magna",
        "dart_loan_ibk_magna",
        "dart_facility_keppel_ansan_",
    )

    for item in inventory:
        bid = item["id"]
        rcept = item.get("dart_last_audit_rcept")
        cov = {
            "pfv_spc": item.get("name"),
            "node_id": bid,
            "visibility": item.get("visibility"),
            "latest_report_reviewed": None,
            "reporting_date": None,
            "filing_date": None,
            "borrowings_note_reviewed": False,
            "named_lenders_found": [],
            "relationships_mapped": [],
            "unresolved_gaps": [],
            "status": None,
        }

        if bid.startswith("seed:") or item.get("visibility") == "no_map_node":
            cov["status"] = "Report unavailable" if not rcept else "Latest report lacks sufficient detail"
            cov["unresolved_gaps"].append("맵 노드 미확정 또는 시드만 존재")
            coverage.append(cov)
            continue

        if not rcept:
            # try node field only
            cov["status"] = "Report unavailable"
            cov["unresolved_gaps"].append("DART 감사보고서 rcept 미확보")
            coverage.append(cov)
            extracts.append({"node_id": bid, "status": "no_rcept"})
            continue

        zpath = DOCS_ZIP / f"{rcept}.zip"
        cov["latest_report_reviewed"] = item.get("report_nm") or f"rcept {rcept}"
        cov["filing_date"] = item.get("rcept_dt") or rcept[:8]
        # Most FY2025 audits: reporting date 2025-12-31 unless semiannual
        rn = item.get("report_nm") or ""
        if "2025.12" in rn or "2025.12" in (item.get("report_nm") or ""):
            cov["reporting_date"] = "2025-12-31"
        elif re.search(r"\(20\d{2}\.\d{2}\)", rn):
            m = re.search(r"\((20\d{2})\.(\d{2})\)", rn)
            y, mo = m.group(1), m.group(2)
            # month-end approx
            cov["reporting_date"] = f"{y}-{mo}-{'30' if mo in ('06','09','04','11') else '31' if mo!='02' else '28'}"
        else:
            cov["reporting_date"] = "2025-12-31"  # default for 감사보고서 when period unknown — flagged
            cov["unresolved_gaps"].append("보고기간 종료일 제목에서 미확인 — 기본 2025-12-31 가정, 재확인 필요")

        if not zpath.exists():
            extracts.append({"node_id": bid, "rcept": rcept, "status": "zip_missing"})
            cov["status"] = "Report unavailable"
            cov["unresolved_gaps"].append(f"캐시 ZIP 없음: {rcept}.zip")
            coverage.append(cov)
            continue

        text = read_zip_text(zpath)
        if not text:
            extracts.append({"node_id": bid, "rcept": rcept, "status": "text_empty"})
            cov["status"] = "Latest report lacks sufficient detail"
            coverage.append(cov)
            continue

        chunk = extract_note_chunk(text)
        if not chunk:
            extracts.append({"node_id": bid, "rcept": rcept, "status": "note_not_found", "text_chars": len(text)})
            cov["status"] = "Latest report lacks sufficient detail"
            cov["unresolved_gaps"].append("차입금 주석 섹션 미검출")
            coverage.append(cov)
            continue

        cov["borrowings_note_reviewed"] = True
        unit = detect_unit(chunk)
        current, prior = split_current_prior(chunk)
        # If chunk has both 당기말 and 전기말 as columns without (당기)/(전기) sections,
        # still parse but mark dual-column risk
        dual_col = ("당기말" in chunk and "전기말" in chunk and prior is None)
        lenders = parse_lender_rows(current, unit)
        # Filter absurd tiny leftovers
        lenders = [L for L in lenders if L["outstanding_krw"] >= 100_000_000]  # >= 1억

        extract = {
            "node_id": bid,
            "rcept": rcept,
            "status": "ok",
            "unit": unit,
            "dual_column_risk": dual_col,
            "note_excerpt": chunk[:1500],
            "current_lenders": lenders,
            "prior_section_present": prior is not None,
        }
        extracts.append(extract)
        cov["named_lenders_found"] = [f"{L['name_in_doc']} ({eok(L['outstanding_krw']):g}억)" for L in lenders]

        # EXTRACT ONLY — do not auto-write edges here.
        # Window heuristics mis-assigned facility totals; verified edges come from
        # patch_gaya_borrowings / patch_verified_current_borrowings /
        # patch_casequare_peach_camsquare_loans.
        mapped = []
        if item.get("visibility") == "missing_from_graph":
            cov["status"] = "Reviewed — borrowings disclosed but lenders unnamed" if not lenders else "Latest report lacks sufficient detail"
            cov["unresolved_gaps"].append("차주 노드가 그래프에 없어 엣지 미작성")
            cov["named_lenders_found"] = [f"{L['name_in_doc']} ({eok(L['outstanding_krw']):g}억?)" for L in lenders]
            coverage.append(cov)
            continue

        existing_active = [
            e
            for e in edges
            if e.get("target") == bid
            and e.get("relationship_type") == "PROJECT_LOAN"
            and str(e.get("exposure_status", "")).startswith("ACTIVE")
        ]
        for e in existing_active:
            if e["id"] not in mapped and not any(e["id"] in m for m in mapped):
                mapped.append(e["id"] + " (existing)")

        cov["relationships_mapped"] = mapped
        if lenders or existing_active:
            cov["status"] = "Reviewed and mapped"
            if existing_active and not cov["named_lenders_found"]:
                cov["named_lenders_found"] = [
                    f"{e.get('source')} ({e.get('amount_krw_eok')}억)" for e in existing_active[:12]
                ]
        elif "차입처" in chunk:
            cov["status"] = "Reviewed — borrowings disclosed but lenders unnamed"
            cov["unresolved_gaps"].append("차입처는 있으나 알려진 기관명 매칭 실패 또는 SPC/펀드명 미해석")
        else:
            cov["status"] = "Reviewed — no outstanding borrowings disclosed"

        # Update borrower node note
        for n in net["nodes"]:
            if n["id"] == bid and lenders:
                n["connection_status"] = "관계 확인"
                n["dart_borrowings_note"] = (
                    f"주석 당기말 대주 {len(lenders)}곳 매핑 "
                    f"(as_of {cov['reporting_date']}, rcept {rcept})"
                )
                n["amount_as_of"] = cov["reporting_date"]
                n["dart_last_audit_rcept"] = rcept
                if not isinstance(n.get("source_ids"), list):
                    n["source_ids"] = []
                if src_id not in n["source_ids"]:
                    n["source_ids"].append(src_id)

        coverage.append(cov)

    net["edges"] = edges
    NET_PATH.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_EXTRACT.write_text(json.dumps({"results": extracts}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Status summary
    by_status: dict[str, int] = {}
    for c in coverage:
        by_status[c["status"] or "unknown"] = by_status.get(c["status"] or "unknown", 0) + 1

    OUT_COV.write_text(
        json.dumps({
            "verification_date": "2026-10-22",
            "inventory_count": len(inventory),
            "coverage_count": len(coverage),
            "by_status": by_status,
            "edges_added": added,
            "edges_replaced": replaced,
            "policy": [
                "current-period balances only (당기말)",
                "전기말 never written as ACTIVE_CONFIRMED by this script",
                "unnamed groups → facility_total_context, shock_eligible=false",
                "curated gaya/dito/magna/… edges preserved when present",
            ],
            "coverage": coverage,
        }, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    msg = (
        f"inventory={len(inventory)} coverage={len(coverage)} "
        f"added={len(added)} replaced={len(replaced)} statuses={by_status}"
    )
    print(msg.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
