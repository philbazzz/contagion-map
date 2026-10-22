#!/usr/bin/env python3
"""
AI DC PF finance-first expansion (news-evidence only).

- Enrich existing financial edges with amount_type / financing_stage /
  evidence_status / project_id / Korean labels / article URLs.
- Add Magna 덕이 PFV + named lenders (no invented per-lender splits).
- Add Camsquare 제1차 SPC money path (ABSTB + Samsung credit support).
- Add Casequare Mountain Rich ← Yuanta purchase-commitment path.
- Add Magna equity sponsors (GS / K1 Premier REIT via Korealand Trust / Hana Sec).
- Add Fine DC Hyundai Motor Securities arranger (Herald reporting).
- Add Yongin operator Lotte Innovate (Dealsite).
- Never assign syndicate totals to every lender; never store Unknown as 0.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PF = ROOT / "frontend" / "public" / "data" / "pf"
TODAY = date.today().isoformat()

# Approximate FX for display-only USD conversion when article gives KRW only.
# Null amount_usd_m preferred when amount is institution-specific KRW.
KRW_PER_USD = 1300.0

SRC = {
    "casequare_dealsite": {
        "id": "S_CASEQUARE_DEALSITE_121975",
        "title": "LF 가산동 데이터센터, 본PF 자금조달 '순항'",
        "publisher": "딜사이트",
        "date": "2024-07-02",
        "url": "https://dealsite.co.kr/articles/121975",
        "used_for": "Casequare Gasan PF lender list and amounts",
        "kind": "news",
    },
    "casequare_kiwoom": {
        "id": "S_CASEQUARE_KIWOOM_REFIN",
        "title": "키움증권, '케이스퀘어데이터센터' 3800억 PF 리파이낸싱",
        "publisher": "뉴스핌",
        "date": "2025-02-24",
        "url": "https://www.newspim.com/news/view/20250224000607",
        "used_for": "Casequare refinancing underwrite",
        "kind": "news",
    },
    "camsquare_dealsitetv": {
        "id": "S_CAMSQUARE_DEALSITETV_128941",
        "title": "안산 성곡동 데이터센터, 8340억 본PF 조달 성공",
        "publisher": "딜사이트경제TV",
        "date": "2024-12-27",
        "url": "https://dealsitetv.com/articles/128941",
        "used_for": "Camsquare Ansan PF tranches, ABSTB SPC, Samsung credit support",
        "kind": "news",
    },
    "camsquare_asiae": {
        "id": "S_CAMSQUARE_ASIAE_ADMIN",
        "title": "행정공제회, 1300억 '뭉칫돈'…기관 '새 먹거리'로 떠오르는 데이터센터",
        "publisher": "아시아경제",
        "date": "2024-11-19",
        "url": "https://www.asiae.co.kr/article/2024111916400635620",
        "used_for": "Admin mutual aid equity KRW 130bn Camsquare Ansan",
        "kind": "news",
    },
    "camsquare_ibt": {
        "id": "S_CAMSQUARE_IBTOMATO",
        "title": "안산 데이터센터 개발사업 본PF 전환 성공…현대건설 책임준공 확약",
        "publisher": "IB토마토",
        "date": "2025-01-02",
        "url": "https://www.newstomato.com/ReadNews.aspx?no=1249683",
        "used_for": "Camsquare equity/structuring participants",
        "kind": "news",
    },
    "magna_thebell": {
        "id": "S_MAGNA_THEBELL_REFIN",
        "title": "[PF Radar] 마그나PFV, 고양 데이터센터 '금리 인하' 리파이낸싱",
        "publisher": "더벨",
        "date": "2025-09-05",
        "url": "https://www.thebell.co.kr/front/newsview.asp?key=202509051616197120107988",
        "used_for": "Magna Deogi PF lenders, facility KRW 273bn, equity sponsors",
        "kind": "news",
    },
    "yongin_dealsite": {
        "id": "S_YONGIN_DEALSITE_157007",
        "title": "한국대체투자운용, 용인 데이터센터 브릿지론 600억 조달",
        "publisher": "딜사이트",
        "date": "2026-02-19",
        "url": "https://dealsite.co.kr/articles/157007",
        "used_for": "Yongin Camsquare bridge senior/mezz + operator",
        "kind": "news",
    },
    "bucheon_edaily": {
        "id": "S_BUCHEON_EDAILY",
        "title": "부천에 'AI 두뇌 공장' 짓는다…동양, PF 1590억 조달 완료",
        "publisher": "이데일리 마켓in",
        "date": "2026-05-20",
        "url": "https://www.edaily.co.kr/News/Read?mediaCodeNo=257&newsId=05005286645450888",
        "used_for": "Bucheon PF syndicate lenders (no per-lender amounts)",
        "kind": "news",
    },
    "fine_digitaltoday": {
        "id": "S_FINE_DIGITALTODAY",
        "title": "대우건설, 파인디씨피에프브이 채무보증 결정",
        "publisher": "디지털투데이",
        "date": "2025-12-15",
        "url": "https://www.digitaltoday.co.kr/news/articleView.html?idxno=612777",
        "used_for": "Fine DC completion undertaking / lenders named without split",
        "kind": "news",
    },
    "fine_dealbook": {
        "id": "S_FINE_DEALBOOK",
        "title": "광주첨단 파인 데이터센터, 2959억 PF약정...KB발해인프라 100억 참여",
        "publisher": "딜북뉴스",
        "date": "2025-12-19",
        "url": "https://www.dealbook.co.kr/gwangjuceomdan-pain-deiteosenteo-2959eog-pfyagjeong-kbbalhaeinpeura-100eog-camyeo/",
        "used_for": "KB Balhae KRW 10bn Fine DC participation",
        "kind": "news",
    },
    "fine_herald": {
        "id": "S_FINE_HERALD",
        "title": "데이터센터 금융PF 새 시장 발굴 박차",
        "publisher": "헤럴드경제",
        "date": "2026-01-01",
        "url": "https://biz.heraldcorp.com/article/10900785",
        "used_for": "Hyundai Motor Securities Fine DC PF arrange / underwrite then sell-down",
        "kind": "news",
    },
}


def eok_to_usd_m(eok: float | None) -> float | None:
    if eok is None:
        return None
    return round((eok * 100_000_000) / KRW_PER_USD / 1_000_000, 1)


def node(
    nid: str,
    name_ko: str,
    name_en: str,
    *,
    group: str,
    entity_type: str,
    role: str,
    roles: list[str],
    description: str,
    pf_exposure_class: str = "confirmed_aidc_project",
    listed: bool = False,
    ticker: str | None = None,
    exchange: str | None = None,
) -> dict:
    return {
        "id": nid,
        "name": name_ko,
        "name_ko": name_ko,
        "name_en": name_en,
        "group": group,
        "sector": "AI Data Center PF",
        "entity_type": entity_type,
        "role": role,
        "roles": roles,
        "description": description,
        "listed": listed,
        "ticker": ticker,
        "exchange": exchange if listed else None,
        "quote_currency": "KRW" if listed else None,
        "listing_note": None if listed else "비상장",
        "display_size": 5 if entity_type == "spv" else 6,
        "source_status": "VERIFIED",
        "source_ids": ["S_PF_FINANCE_V5"],
        "key_drivers": roles[:3],
        "region": "KR",
        "country": "KR",
        "pf_exposure_class": pf_exposure_class,
        "pf_exposure_class_num": {
            "confirmed_aidc_project": 1,
            "confirmed_dc_finance": 2,
            "general_pf": 3,
            "sector_sensitivity": 4,
            "research_candidate": 5,
        }.get(pf_exposure_class, 5),
        "connection_status": "기사상 참여 확인",
        "is_company": True,
    }


def edge(
    eid: str,
    src: str,
    tgt: str,
    rel: str,
    label: str,
    *,
    project_id: str,
    project_name: str,
    financing_stage: str,
    amount_type: str,
    evidence_status: str,
    participation_path: str,
    amount_note: str,
    amount_krw_eok: float | None = None,
    facility_total_krw_eok: float | None = None,
    seniority: str | None = None,
    roles: list[str] | None = None,
    exposure_kind: str = "funded_or_committed",
    relationship_status: str = "current",
    source_url: str = "",
    source_title: str = "",
    source_date: str = "",
    source_ids: list[str] | None = None,
    evidence_summary: str = "",
    channel: str = "financial",
    contingent: bool = False,
    amount_as_of: str | None = None,
    transaction_date: str | None = None,
    maturity: str | None = None,
) -> dict:
    note = amount_note
    if amount_krw_eok is None and "금액 미공개" not in note and amount_type != "facility_total_context":
        if "미공개" not in note and "미공시" not in note and "미확인" not in note:
            note = f"{note} — 금액 미공개" if note else "금액 미공개"
    if "현재 잔액 미확인" not in note and amount_type in (
        "institution_commitment",
        "facility_total_context",
        "underwrite_commitment",
        "credit_support_limit",
        "guarantee_limit",
    ):
        note = f"{note} — 현재 잔액 미확인"

    return {
        "id": eid,
        "source": src,
        "target": tgt,
        "relationship_type": rel,
        "impact_channel": channel,
        "label": label,
        "impact_label": label,
        "source_status": "VERIFIED",
        "source_ids": source_ids or ["S_PF_FINANCE_V5"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": eok_to_usd_m(amount_krw_eok) if amount_krw_eok is not None else None,
        "amount_note": note,
        "amount_krw_eok": amount_krw_eok,
        "amount_type": amount_type,
        "facility_total_krw_eok": facility_total_krw_eok,
        "seniority": seniority,
        "financing_stage": financing_stage,
        "evidence_status": evidence_status,
        "participation_path": participation_path,
        "participation_directness": "indirect" if "간접" in participation_path or "→" in participation_path and participation_path.count("→") >= 2 else "direct",
        "contingent_obligation": contingent,
        "roles": roles or [],
        "transmission_class": "direct_contract",
        "evidence_level": 2,
        "project_id": project_id,
        "project_name": project_name,
        "stress_direction": "차주 스트레스 → 대주·투자자 회수 리스크(정성)" if not contingent else "조건부 의무 — 확약 조건 충족 시에만",
        "obligation_trigger": evidence_summary or "",
        "exposure_kind": exposure_kind,
        "relationship_status": relationship_status,
        "source_url": source_url,
        "source_title": source_title,
        "source_date": source_date,
        "verification_date": TODAY,
        "verification_gap": "",
        "amount_as_of": amount_as_of,
        "transaction_date": transaction_date,
        "maturity": maturity,
        "explanation": evidence_summary,
    }


def upsert_node(by: dict, n: dict, added: list) -> None:
    if n["id"] in by:
        cur = by[n["id"]]
        for k, v in n.items():
            if k == "id":
                continue
            if k == "roles":
                cur["roles"] = sorted(set((cur.get("roles") or []) + (v or [])))
            elif k in ("description", "role") and cur.get(k):
                continue
            else:
                cur[k] = v
        cur["connection_status"] = "기사상 참여 확인"
        if cur.get("pf_exposure_class") in (None, "research_candidate", "sector_sensitivity"):
            cur["pf_exposure_class"] = n.get("pf_exposure_class", "confirmed_aidc_project")
    else:
        by[n["id"]] = n
        added.append(n["id"])


def upsert_edge(edges: list, e: dict, added: list, updated: list) -> None:
    idx = next((i for i, x in enumerate(edges) if x["id"] == e["id"]), None)
    if idx is None:
        # also match source-target-rel if id differs
        idx = next(
            (
                i
                for i, x in enumerate(edges)
                if x["source"] == e["source"]
                and x["target"] == e["target"]
                and x.get("relationship_type") == e["relationship_type"]
                and x.get("project_id") in (None, e["project_id"])
            ),
            None,
        )
        if idx is not None:
            # keep existing id, merge fields
            old = edges[idx]
            merged = {**old, **{k: v for k, v in e.items() if k != "id"}}
            merged["id"] = old["id"]
            edges[idx] = merged
            updated.append(old["id"])
            return
        edges.append(e)
        added.append(e["id"])
    else:
        old = edges[idx]
        merged = {**old, **e}
        edges[idx] = merged
        updated.append(e["id"])


def patch_existing(e: dict, **fields) -> None:
    e.update({k: v for k, v in fields.items() if v is not None})


def main() -> None:
    net = json.loads((PF / "network.json").read_text(encoding="utf-8"))
    proj = json.loads((PF / "projects.json").read_text(encoding="utf-8"))
    by = {n["id"]: n for n in net["nodes"]}
    edges = net["edges"]
    sources = {s["id"]: s for s in net.get("sources", [])}
    for s in SRC.values():
        sources[s["id"]] = s

    added_nodes: list[str] = []
    added_edges: list[str] = []
    updated_edges: list[str] = []
    corrections: list[str] = []
    gaps: list[str] = []

    # ---------- ensure Magna / ABS / REIT / operator nodes ----------
    upsert_node(
        by,
        node(
            "magna_pfv",
            "마그나피에프브이",
            "Magna PFV",
            group="project_finance",
            entity_type="spv",
            role="고양 덕이 DC 차주 PFV",
            roles=["borrower", "developer_vehicle", "spv"],
            description="GS건설 자회사 PFV. 고양 덕이동 데이터센터 차주. 더벨: 본PF/리파이낸싱 2,730억.",
        ),
        added_nodes,
    )
    upsert_node(
        by,
        node(
            "camsquare_first_spc",
            "캄스퀘어제일차",
            "Camsquare No.1 SPC",
            group="project_finance",
            entity_type="spv",
            role="안산 DC ABSTB 발행 SPC",
            roles=["securitization_spc", "senior_lender"],
            description="캄스퀘어안산데이터센터PFV에 대출하기 위해 설립된 SPC. ABSTB 6,800억 한도 발행(딜사이트경제TV).",
        ),
        added_nodes,
    )
    upsert_node(
        by,
        node(
            "k1_premier_reit",
            "케이원프리미어리츠",
            "K1 Premier REIT",
            group="kr_am",
            entity_type="reit",
            role="마그나PFV 지분 투자 리츠",
            roles=["equity_investor", "reit"],
            description="더벨: 마그나PFV 지분 41.67%. 한국토지신탁 관련 위탁관리리츠로 보도.",
        ),
        added_nodes,
    )
    upsert_node(
        by,
        node(
            "korealand_trust",
            "한국토지신탁",
            "Korea Land & Trust",
            group="kr_trust",
            entity_type="trust",
            role="케이원프리미어리츠 관련 신탁",
            roles=["trust", "reit_sponsor"],
            description="더벨: 케이원프리미어위탁관리부동산투자회사(마그나PFV 지분) 관련.",
            listed=True,
            ticker="034890",
            exchange="KOSDAQ",
        ),
        added_nodes,
    )
    upsert_node(
        by,
        node(
            "lotte_innovate",
            "롯데이노베이트",
            "Lotte Innovate",
            group="kr_operator",
            entity_type="operator",
            role="용인 캄스퀘어 위탁운영",
            roles=["operator"],
            description="딜사이트: 캄스퀘어용인데이터센터PFV와 위탁운영 계약(약 695억, 2030~2035).",
            listed=True,
            ticker="286940",
            exchange="KOSPI",
        ),
        added_nodes,
    )

    # Ensure mountain_rich typed as securitization SPC
    if "mountain_rich" in by:
        by["mountain_rich"]["entity_type"] = "spv"
        by["mountain_rich"]["roles"] = sorted(
            set((by["mountain_rich"].get("roles") or []) + ["securitization_spc", "senior_lender"])
        )
        by["mountain_rich"]["connection_status"] = "기사상 참여 확인"

    # ---------- Casequare lender enrichment (Dealsite 121975) ----------
    case_lenders = [
        ("pf_hyundai_cap_casequare", "hyundai_capital", 30, "senior", "현대캐피탈"),
        ("pf_woori_cap_casequare", "woori_fin_capital", 20, "senior", "우리금융캐피탈"),
        ("pf_tongyang_casequare", "tongyang_life", 70, "senior", "동양생명"),
        ("pf_thek_casequare", "thek_savings", 10, "senior", "더케이저축은행"),
        ("pf_shinhan_cap_casequare", "shinhan_capital", 10, "senior", "신한캐피탈"),
        ("pf_mountain_casequare", "mountain_rich", 25, "senior", "마운틴리치제일차"),
        ("pf_woori_ib_casequare", "woori_ib", 20, "senior", "우리종합금융"),
        ("pf_kb_cap_casequare", "kb_capital", 30, "senior", "KB캐피탈"),
        ("pf_nh_casequare", "nh_bank", 40, "senior", "농협은행"),
        ("pf_hyundai_com_casequare", "hyundai_commercial", 20, "senior", "현대커머셜"),
        ("pf_kis_junior_casequare", "korea_inv_sec", 70, "junior", "한국투자증권"),
    ]
    case_src = SRC["casequare_dealsite"]
    for eid, nid, eok, sen, ko in case_lenders:
        existing = next((x for x in edges if x["id"] == eid), None)
        path = (
            "유동화 SPC → 케이스퀘어PFV 선순위 대출 (ABS 자금)"
            if nid == "mountain_rich"
            else f"{ko} → 케이스퀘어PFV {'후순위' if sen == 'junior' else '선순위'} 대출"
        )
        e = edge(
            eid,
            nid,
            "casequare_pfv",
            "PROJECT_LOAN",
            f"{ko} → 케이스퀘어 가산 {'후순위' if sen == 'junior' else '선순위'} {eok}억",
            project_id="casequare_gasan",
            project_name="케이스퀘어 가산 데이터센터",
            financing_stage="main_pf",
            amount_type="institution_commitment",
            evidence_status="기사상 참여 확인",
            participation_path=path,
            amount_note=f"기사상 약정/투자금액 {eok}억 원",
            amount_krw_eok=float(eok),
            facility_total_krw_eok=345.0,
            seniority=sen,
            roles=["lender", "junior_lender" if sen == "junior" else "senior_lender"],
            exposure_kind="loan_commitment",
            source_url=case_src["url"],
            source_title=case_src["title"],
            source_date=case_src["date"],
            source_ids=[case_src["id"]],
            evidence_summary=f"딜사이트: 3450억 본PF 중 {ko} {eok}억 ({'트렌치B' if sen == 'junior' else '트렌치A'}).",
            transaction_date="2024-02",
        )
        upsert_edge(edges, e, added_edges, updated_edges)
        if nid in by:
            by[nid]["connection_status"] = "기사상 참여 확인"
            by[nid]["pf_exposure_class"] = "confirmed_aidc_project"

    # Yuanta purchase commitment → Mountain Rich (credit support, not lender to PFV)
    upsert_edge(
        edges,
        edge(
            "pf_yuanta_mountain_casequare",
            "yuanta_sec",
            "mountain_rich",
            "CREDIT_ENHANCEMENT",
            "유안타증권 → 마운틴리치제일차 사모사채 인수확약",
            project_id="casequare_gasan",
            project_name="케이스퀘어 가산 데이터센터",
            financing_stage="main_pf",
            amount_type="credit_support_limit",
            evidence_status="기사상 참여 확인",
            participation_path="유안타증권 → 인수확약 → 마운틴리치제일차 → 케이스퀘어PFV",
            amount_note="기사상 인수확약(신용보강) — 개별 확약한도 미공개",
            amount_krw_eok=None,
            facility_total_krw_eok=25.0,
            seniority="senior",
            roles=["credit_support", "underwriter"],
            exposure_kind="purchase_commitment",
            contingent=True,
            source_url=case_src["url"],
            source_title=case_src["title"],
            source_date=case_src["date"],
            source_ids=[case_src["id"]],
            evidence_summary="딜사이트: 마운틴리치제일차 유동화증권 250억; 유안타증권이 사모사채 인수확약으로 신용보강.",
        ),
        added_edges,
        updated_edges,
    )

    # Kiwoom refinancing — underwrite, not funded retained loan of 3800
    kiw = SRC["casequare_kiwoom"]
    upsert_edge(
        edges,
        edge(
            "pf_kiwoom_refin",
            "kiwoom_sec",
            "casequare_pfv",
            "REFINANCING_UNDERWRITE",
            "키움증권 → 케이스퀘어 리파이낸싱 총액인수(맥락 3,800억)",
            project_id="casequare_gasan",
            project_name="케이스퀘어 가산 데이터센터",
            financing_stage="operating_refinancing",
            amount_type="underwrite_commitment",
            evidence_status="기사상 참여 확인",
            participation_path="키움증권 → 총액인수(리파이낸싱) → 케이스퀘어PFV",
            amount_note="기사상 리파이낸싱 총액인수 맥락 3,800억 — 보유·셀다운 잔액 미확인",
            amount_krw_eok=3800.0,
            facility_total_krw_eok=3800.0,
            roles=["underwriter", "arranger"],
            exposure_kind="underwrite_commitment",
            contingent=True,
            source_url=kiw["url"],
            source_title=kiw["title"],
            source_date=kiw["date"],
            source_ids=[kiw["id"]],
            evidence_summary="뉴스핌(2025-02-24): 키움증권이 3800억 PF 리파이낸싱 총액인수 참여 발표. 인수≠장기 보유.",
            transaction_date="2025-02",
        ),
        added_edges,
        updated_edges,
    )
    corrections.append(
        "pf_kiwoom_refin: amount_type=underwrite_commitment (not funded loan); contingent=true"
    )

    # LF equity / collateral already exist — enrich
    for eid, fields in [
        (
            "pf_lf_casequare",
            dict(
                project_id="casequare_gasan",
                project_name="케이스퀘어 가산 데이터센터",
                financing_stage="equity",
                amount_type="equity_investment",
                evidence_status="기사상 참여 확인",
                participation_path="LF → 케이스퀘어PFV 지분(약 66.9%) + 주식담보 제공",
                amount_note="기사상 지분담보 설정금액 970억 — 현재 잔액 미확인",
                amount_krw_eok=97.0,
                source_url=case_src["url"],
                source_title=case_src["title"],
                source_date=case_src["date"],
                roles=["sponsor", "equity", "collateral_provider"],
            ),
        ),
    ]:
        ex = next((x for x in edges if x["id"] == eid), None)
        if ex:
            patch_existing(ex, **fields)
            updated_edges.append(eid)

    # ---------- Camsquare Ansan money path ----------
    cam_tv = SRC["camsquare_dealsitetv"]
    cam_as = SRC["camsquare_asiae"]
    cam_ib = SRC["camsquare_ibt"]

    # Samsung arranger — facility context, not full retained exposure
    upsert_edge(
        edges,
        edge(
            "pf_samsung_sec_camsquare",
            "samsung_sec",
            "camsquare_pfv",
            "ARRANGER",
            "삼성증권 → 캄스퀘어안산 본PF 주관(시설 8,340억)",
            project_id="camsquare_ansan",
            project_name="캄스퀘어 안산 데이터센터",
            financing_stage="main_pf",
            amount_type="facility_total_context",
            evidence_status="기사상 참여 확인",
            participation_path="삼성증권 → 주관/구조화 → 캄스퀘어안산PFV (주관≠전액 대주)",
            amount_note="기사상 시설 총액 8,340억(주관 규모) — 기관 보유액과 동일시하지 않음",
            amount_krw_eok=None,
            facility_total_krw_eok=8340.0,
            roles=["arranger"],
            exposure_kind="arranger_role",
            source_url=cam_tv["url"],
            source_title=cam_tv["title"],
            source_date=cam_tv["date"],
            source_ids=[cam_tv["id"]],
            evidence_summary="딜사이트경제TV: 삼성증권 주관으로 선/중/후순위 8340억 대출약정.",
            transaction_date="2024-12",
        ),
        added_edges,
        updated_edges,
    )
    corrections.append(
        "pf_samsung_sec_camsquare: amount_type=facility_total_context; arranger size ≠ retained exposure"
    )

    # Samsung credit support → Camsquare First SPC (ABSTB)
    upsert_edge(
        edges,
        edge(
            "pf_samsung_camsquare_abstb_support",
            "samsung_sec",
            "camsquare_first_spc",
            "CREDIT_ENHANCEMENT",
            "삼성증권 → 캄스퀘어제일차 ABSTB 신용보강(한도 6,800억)",
            project_id="camsquare_ansan",
            project_name="캄스퀘어 안산 데이터센터",
            financing_stage="securitization",
            amount_type="credit_support_limit",
            evidence_status="기사상 참여 확인",
            participation_path="삼성증권 → 매입·인수·자금보충 → 캄스퀘어제일차 ABSTB → PFV 선순위대출",
            amount_note="기사상 ABSTB 한도 6,800억 신용보강 — 현재 발행잔액·보유분 미확인",
            amount_krw_eok=6800.0,
            facility_total_krw_eok=6800.0,
            seniority="senior",
            roles=["credit_support", "underwriter"],
            exposure_kind="purchase_commitment",
            contingent=True,
            source_url=cam_tv["url"],
            source_title=cam_tv["title"],
            source_date=cam_tv["date"],
            source_ids=[cam_tv["id"]],
            evidence_summary="딜사이트경제TV: 선순위 대주 캄스퀘어제일차 ABSTB 6800억 한도에 삼성증권이 대출채권 매입·사모사채 인수·자금보충의무 제공.",
            maturity="2028-06-26",
            transaction_date="2024-12",
        ),
        added_edges,
        updated_edges,
    )

    upsert_edge(
        edges,
        edge(
            "pf_camsquare_first_to_pfv",
            "camsquare_first_spc",
            "camsquare_pfv",
            "PROJECT_LOAN",
            "캄스퀘어제일차 → 안산PFV 선순위 대출(ABSTB 기초)",
            project_id="camsquare_ansan",
            project_name="캄스퀘어 안산 데이터센터",
            financing_stage="securitization",
            amount_type="facility_total_context",
            evidence_status="기사상 참여 확인",
            participation_path="캄스퀘어제일차 → 선순위 대출 → 캄스퀘어안산PFV",
            amount_note="기사상 선순위 트렌치A 맥락 7,100억 중 ABSTB 경로 — SPC 개별 잔액 미확인",
            amount_krw_eok=None,
            facility_total_krw_eok=7100.0,
            seniority="senior",
            roles=["senior_lender", "securitization_spc"],
            exposure_kind="securitization_loan",
            source_url=cam_tv["url"],
            source_title=cam_tv["title"],
            source_date=cam_tv["date"],
            source_ids=[cam_tv["id"]],
            evidence_summary="딜사이트경제TV: 캄스퀘어제일차는 PFV에 대출하기 위해 설립된 SPC이며 ABSTB를 발행.",
        ),
        added_edges,
        updated_edges,
    )

    # Admin mutual equity
    upsert_edge(
        edges,
        edge(
            "pf_admin_camsquare_co",
            "admin_mutual",
            "camsquare_pfv",
            "EQUITY_INVESTMENT",
            "행정공제회 → 캄스퀘어안산PFV 출자 1,300억",
            project_id="camsquare_ansan",
            project_name="캄스퀘어 안산 데이터센터",
            financing_stage="equity",
            amount_type="equity_investment",
            evidence_status="기사상 참여 확인",
            participation_path="행정공제회 → (투자 경로 일부 미공개) → 캄스퀘어안산PFV 에쿼티",
            amount_note="기사상 약정/투자금액 1,300억 — 현재 잔액 미확인",
            amount_krw_eok=1300.0,
            roles=["equity_investor", "mutual_aid"],
            exposure_kind="equity",
            source_url=cam_as["url"],
            source_title=cam_as["title"],
            source_date=cam_as["date"],
            source_ids=[cam_as["id"], cam_ib["id"]],
            evidence_summary="아시아경제·IB토마토: 행정공제회 안산 데이터센터 프로젝트 투자 1300억(첫 DC 투자).",
            transaction_date="2024-11",
        ),
        added_edges,
        updated_edges,
    )
    gaps.append(
        "Camsquare Ansan: 트렌치A/B/C 중 캄스퀘어제일차·삼성 경로 외 개별 대주명·배분 미공개"
    )
    gaps.append(
        "Camsquare Ansan: 행정공제회 1300억의 펀드/직접 출자 세부 경로 기사상 일부만 확인(투자 경로 미공개 표기)"
    )

    # Enrich other camsquare edges with project_id
    for eid in (
        "pf_hyundai_camsquare_epc_co",
        "pf_hyundai_camsquare_eq",
        "pf_eugene_camsquare",
        "pf_korea_alt_camsquare",
        "pf_kakao_ent_lease_co",
    ):
        ex = next((x for x in edges if x["id"] == eid), None)
        if not ex:
            continue
        patch_existing(
            ex,
            project_id="camsquare_ansan",
            project_name="캄스퀘어 안산 데이터센터",
            evidence_status="기사상 참여 확인",
            source_url=ex.get("source_url") or cam_ib["url"],
            source_title=ex.get("source_title") or cam_ib["title"],
            source_date=ex.get("source_date") or cam_ib["date"],
        )
        if eid == "pf_hyundai_camsquare_epc_co":
            patch_existing(
                ex,
                financing_stage="construction",
                amount_type="construction_contract_value",
                amount_krw_eok=5735.0,
                amount_note="기사상 공사금액 5,735억(VAT별도) — 미수공사비와 동일시하지 않음",
                roles=["epc", "completion_undertaking"],
                contingent_obligation=True,
                exposure_kind="epc_contract",
                participation_path="현대건설 → EPC·책임준공 → 캄스퀘어안산PFV",
            )
        if eid == "pf_hyundai_camsquare_eq":
            patch_existing(
                ex,
                financing_stage="equity",
                amount_type="equity_investment",
                amount_krw_eok=50.0,
                amount_note="기사상 장부가 50억(지분 13.2% 보도) — 현재 잔액 미확인",
                participation_path="현대건설 → 지분 → 캄스퀘어안산PFV",
            )
        updated_edges.append(eid)

    # Samsung equity mention (named but amount undisclosed in DealsiteTV)
    upsert_edge(
        edges,
        edge(
            "pf_samsung_sec_camsquare_equity",
            "samsung_sec",
            "camsquare_pfv",
            "EQUITY_INVESTMENT",
            "삼성증권 → 캄스퀘어안산PFV 에쿼티 참여",
            project_id="camsquare_ansan",
            project_name="캄스퀘어 안산 데이터센터",
            financing_stage="equity",
            amount_type="equity_investment",
            evidence_status="기사상 참여 확인",
            participation_path="삼성증권 → 에쿼티 → 캄스퀘어안산PFV",
            amount_note="기사상 참여 확인 — 금액 미공개 — 현재 잔액 미확인",
            amount_krw_eok=None,
            roles=["equity_investor"],
            exposure_kind="equity",
            source_url=cam_tv["url"],
            source_title=cam_tv["title"],
            source_date=cam_tv["date"],
            source_ids=[cam_tv["id"], cam_ib["id"]],
            evidence_summary="딜사이트경제TV·IB토마토: 삼성증권 등이 PFV 에쿼티 투자에 참여.",
        ),
        added_edges,
        updated_edges,
    )

    # ---------- Magna Deogi (thebell) — named lenders, no per-lender amounts ----------
    magna_src = SRC["magna_thebell"]
    magna_lenders = [
        ("ibk", "IBK기업은행", "kr_bank", "bank"),
        ("hana_bank", "하나은행", "kr_bank", "bank"),
        ("nh_bank", "농협은행", "kr_bank", "bank"),
        ("kb_bank", "KB국민은행", "kr_bank", "bank"),
        ("shinhan_bank", "신한은행", "kr_bank", "bank"),
        ("hyundai_capital", "현대캐피탈", "kr_bank", "capital"),
        ("shinhan_capital", "신한캐피탈", "kr_bank", "capital"),
        ("hanwha_life", "한화생명", "kr_insurance", "insurer"),
    ]
    for nid, ko, _g, et in magna_lenders:
        if nid not in by:
            continue
        by[nid]["connection_status"] = "기사상 참여 확인"
        by[nid]["pf_exposure_class"] = "confirmed_aidc_project"
        upsert_edge(
            edges,
            edge(
                f"pf_magna_lender_{nid}",
                nid,
                "magna_pfv",
                "PROJECT_LOAN",
                f"{ko} → 마그나PFV 본PF 대주단 참여",
                project_id="magna_deogi",
                project_name="마그나 고양 덕이 데이터센터",
                financing_stage="main_pf",
                amount_type="institution_commitment",
                evidence_status="기사상 참여 확인",
                participation_path=f"{ko} → 본PF 대주단 → 마그나PFV",
                amount_note="기사상 참여 확인 — 금액 미공개 — 현재 잔액 미확인",
                amount_krw_eok=None,
                facility_total_krw_eok=2730.0,
                seniority="pari_passu_single_tranche",
                roles=["lender", et],
                exposure_kind="loan_commitment",
                source_url=magna_src["url"],
                source_title=magna_src["title"],
                source_date=magna_src["date"],
                source_ids=[magna_src["id"]],
                evidence_summary="더벨: 2024.9 본PF 대주단에 참여. 2025.9 리파이낸싱도 동일 총액 2730억 단일 트랜치. 개별 배분 미기재.",
                transaction_date="2024-09",
            ),
            added_edges,
            updated_edges,
        )
    gaps.append("Magna Deogi: 대주 8개사 명단 확인, 기관별 약정액 미공개(총 2,730억만 보도)")

    upsert_edge(
        edges,
        edge(
            "pf_hana_sec_magna_arranger",
            "hana_sec",
            "magna_pfv",
            "ARRANGER",
            "하나증권 → 마그나 덕이 본PF·리파이낸싱 주관",
            project_id="magna_deogi",
            project_name="마그나 고양 덕이 데이터센터",
            financing_stage="operating_refinancing",
            amount_type="facility_total_context",
            evidence_status="기사상 참여 확인",
            participation_path="하나증권 → 주관 → 마그나PFV (주관≠전액 대주)",
            amount_note="기사상 시설 총액 2,730억(주관) — 보유액과 동일시하지 않음",
            amount_krw_eok=None,
            facility_total_krw_eok=2730.0,
            roles=["arranger"],
            exposure_kind="arranger_role",
            source_url=magna_src["url"],
            source_title=magna_src["title"],
            source_date=magna_src["date"],
            source_ids=[magna_src["id"]],
            evidence_summary="더벨: 하나증권 주관으로 금리인하 리파이낸싱 기표(연 5.06%, 2730억).",
            transaction_date="2025-09",
        ),
        added_edges,
        updated_edges,
    )

    upsert_edge(
        edges,
        edge(
            "pf_gs_magna_parent",
            "gs_enc",
            "magna_pfv",
            "EQUITY_SPONSOR",
            "GS건설 → 마그나PFV 최대주주·시공·책임준공",
            project_id="magna_deogi",
            project_name="마그나 고양 덕이 데이터센터",
            financing_stage="equity",
            amount_type="equity_investment",
            evidence_status="기사상 참여 확인",
            participation_path="GS건설 → 지분 51.39% + EPC·책임준공 → 마그나PFV",
            amount_note="기사상 지분율 51.39% — 출자액 미공개 — 현재 잔액 미확인",
            amount_krw_eok=None,
            roles=["sponsor", "epc", "completion_undertaking"],
            exposure_kind="equity_and_completion",
            contingent=True,
            source_url=magna_src["url"],
            source_title=magna_src["title"],
            source_date=magna_src["date"],
            source_ids=[magna_src["id"]],
            evidence_summary="더벨: GS건설 지분 51.39% 최대주주, 시공·책임준공.",
        ),
        added_edges,
        updated_edges,
    )
    upsert_edge(
        edges,
        edge(
            "pf_gs_magna_epc",
            "gs_enc",
            "magna_pfv",
            "EPC_CONTRACT",
            "GS건설 → 마그나 덕이 EPC",
            project_id="magna_deogi",
            project_name="마그나 고양 덕이 데이터센터",
            financing_stage="construction",
            amount_type="construction_contract_value",
            evidence_status="기사상 참여 확인",
            participation_path="GS건설 → 시공 → 마그나PFV",
            amount_note="기사상 시공 수행 확인 — 도급액 미공개(연합 총공사비 추산 1,500억은 별도)",
            amount_krw_eok=None,
            roles=["epc"],
            exposure_kind="epc_contract",
            source_url=magna_src["url"],
            source_title=magna_src["title"],
            source_date=magna_src["date"],
            source_ids=[magna_src["id"]],
            evidence_summary="더벨: GS건설이 시공 직접 수행.",
            channel="contract",
        ),
        added_edges,
        updated_edges,
    )
    upsert_edge(
        edges,
        edge(
            "pf_k1_magna_equity",
            "k1_premier_reit",
            "magna_pfv",
            "EQUITY_INVESTMENT",
            "케이원프리미어리츠 → 마그나PFV 지분 41.67%",
            project_id="magna_deogi",
            project_name="마그나 고양 덕이 데이터센터",
            financing_stage="equity",
            amount_type="equity_investment",
            evidence_status="기사상 참여 확인",
            participation_path="케이원프리미어리츠 → 지분 → 마그나PFV (운용사 재무제표에 전액 귀속하지 않음)",
            amount_note="기사상 지분율 41.67% — 출자액 미공개",
            amount_krw_eok=None,
            roles=["equity_investor", "reit"],
            exposure_kind="equity",
            source_url=magna_src["url"],
            source_title=magna_src["title"],
            source_date=magna_src["date"],
            source_ids=[magna_src["id"]],
            evidence_summary="더벨: 한국토지신탁의 케이원프리미어위탁관리부동산투자회사 지분 41.67%.",
        ),
        added_edges,
        updated_edges,
    )
    upsert_edge(
        edges,
        edge(
            "pf_klt_k1_magna",
            "korealand_trust",
            "k1_premier_reit",
            "ASSET_MANAGER",
            "한국토지신탁 → 케이원프리미어리츠 관련",
            project_id="magna_deogi",
            project_name="마그나 고양 덕이 데이터센터",
            financing_stage="equity",
            amount_type="fund_commitment",
            evidence_status="기사상 참여 확인",
            participation_path="한국토지신탁 → 케이원프리미어리츠 → 마그나PFV (간접)",
            amount_note="기사상 리츠 관련 확인 — 신탁사 대차대조표 전액 귀속 금지",
            amount_krw_eok=None,
            roles=["trust", "reit_related"],
            exposure_kind="indirect_via_reit",
            source_url=magna_src["url"],
            source_title=magna_src["title"],
            source_date=magna_src["date"],
            source_ids=[magna_src["id"]],
            evidence_summary="더벨: 케이원프리미어위탁관리부동산투자회사를 한국토지신탁 관련으로 기재.",
            channel="equity",
        ),
        added_edges,
        updated_edges,
    )
    upsert_edge(
        edges,
        edge(
            "pf_hana_sec_magna_equity",
            "hana_sec",
            "magna_pfv",
            "EQUITY_INVESTMENT",
            "하나증권 → 마그나PFV 지분 6.94%",
            project_id="magna_deogi",
            project_name="마그나 고양 덕이 데이터센터",
            financing_stage="equity",
            amount_type="equity_investment",
            evidence_status="기사상 참여 확인",
            participation_path="하나증권 → 지분 6.94% → 마그나PFV",
            amount_note="기사상 지분율 6.94% — 출자액 미공개",
            amount_krw_eok=None,
            roles=["equity_investor"],
            exposure_kind="equity",
            source_url=magna_src["url"],
            source_title=magna_src["title"],
            source_date=magna_src["date"],
            source_ids=[magna_src["id"]],
            evidence_summary="더벨: 하나증권 지분 6.94%.",
        ),
        added_edges,
        updated_edges,
    )

    # ---------- Yongin bridge enrichment + operator ----------
    yong = SRC["yongin_dealsite"]
    for eid, fields in [
        (
            "pf_hanwha_camsq_yongin_bridge",
            dict(
                financing_stage="bridge",
                amount_type="institution_commitment",
                amount_krw_eok=530.0,
                facility_total_krw_eok=600.0,
                seniority="senior",
                evidence_status="기사상 참여 확인",
                participation_path="한화투자증권 → 선순위 브릿지론 → 캄스퀘어용인PFV",
                amount_note="기사상 약정/투자금액 530억(선순위) — 현재 잔액 미확인",
                contingent_obligation=False,
                exposure_kind="bridge_loan",
                source_url=yong["url"],
                source_title=yong["title"],
                source_date=yong["date"],
                roles=["arranger", "senior_lender"],
            ),
        ),
        (
            "pf_sksec_camsq_yongin_mezz",
            dict(
                financing_stage="bridge",
                amount_type="institution_commitment",
                amount_krw_eok=70.0,
                facility_total_krw_eok=600.0,
                seniority="junior",
                evidence_status="기사상 참여 확인",
                participation_path="SK증권 → 후순위 브릿지론 → 캄스퀘어용인PFV",
                amount_note="기사상 약정/투자금액 70억(후순위) — 현재 잔액 미확인",
                exposure_kind="bridge_loan",
                source_url=yong["url"],
                source_title=yong["title"],
                source_date=yong["date"],
                roles=["mezz_lender"],
            ),
        ),
    ]:
        ex = next((x for x in edges if x["id"] == eid), None)
        if ex:
            patch_existing(ex, project_id="camsquare_yongin", project_name="용인 지곡 하이퍼스케일 데이터센터", **fields)
            updated_edges.append(eid)

    upsert_edge(
        edges,
        edge(
            "pf_lotte_innovate_yongin_ops",
            "lotte_innovate",
            "camsquare_yongin_pfv",
            "FACILITY_OPERATION",
            "롯데이노베이트 → 용인 캄스퀘어 위탁운영",
            project_id="camsquare_yongin",
            project_name="용인 지곡 하이퍼스케일 데이터센터",
            financing_stage="operations",
            amount_type="lease_contract_value",
            evidence_status="기사상 참여 확인",
            participation_path="롯데이노베이트 → 위탁운영 수수료 → 프로젝트 현금흐름(운영)",
            amount_note="기사상 위탁운영 계약 약 695억(기간 2030-05~2035-10) — PF 대여금 아님",
            amount_krw_eok=695.0,
            roles=["operator"],
            exposure_kind="ops_contract",
            source_url=yong["url"],
            source_title=yong["title"],
            source_date=yong["date"],
            source_ids=[yong["id"]],
            evidence_summary="딜사이트: 롯데이노베이트가 위탁운영 계약 공시. 준공·PF 책임은 시행법인.",
            channel="facility",
            maturity="2035-10",
        ),
        added_edges,
        updated_edges,
    )

    # ---------- Bucheon enrichment ----------
    buc = SRC["bucheon_edaily"]
    for eid in (
        "pf_hana_bucheon",
        "pf_bnk_bucheon",
        "pf_ibk_bucheon",
        "pf_hana_cap_bucheon",
        "pf_dongyang_bucheon",
        "pf_dl_bucheon_epc",
        "pf_dcplat_bucheon",
    ):
        ex = next((x for x in edges if x["id"] == eid), None)
        if not ex:
            continue
        patch_existing(
            ex,
            project_id="bucheon_samjeong_ai",
            project_name="부천 삼정 AI 허브센터",
            evidence_status="기사상 참여 확인",
            source_url=ex.get("source_url") or buc["url"],
            source_title=ex.get("source_title") or buc["title"],
            source_date=ex.get("source_date") or buc["date"],
        )
        if eid.startswith("pf_hana_bucheon") or eid.startswith("pf_bnk") or eid.startswith("pf_ibk") or eid.startswith("pf_hana_cap"):
            patch_existing(
                ex,
                financing_stage="main_pf",
                amount_type="institution_commitment",
                amount_krw_eok=None,
                facility_total_krw_eok=1590.0,
                amount_note="기사상 참여 확인 — 금액 미공개 — 현재 잔액 미확인 (시설 총액 1,590억)",
                participation_path=f"{by.get(ex['source'], {}).get('name_ko', ex['source'])} → 본PF 대주단 → 디씨아이티와이부천PFV",
                seniority="undisclosed",
            )
        if eid == "pf_dongyang_bucheon":
            patch_existing(
                ex,
                financing_stage="equity",
                amount_type="equity_investment",
                contingent_obligation=True,
                exposure_kind="equity_and_share_pledge",
                participation_path="동양 → 지분·주식근질권 → 부천PFV 대주단",
                amount_note="기사상 출자·근질권(담보설정 약 495.5억) — PF 1590억을 동양 현금투자로 보지 않음",
            )
        if eid == "pf_dl_bucheon_epc":
            patch_existing(
                ex,
                financing_stage="construction",
                amount_type="construction_contract_value",
                amount_krw_eok=1268.0,
                amount_note="기사상 공사비 1,268억 — 미수공사비와 동일시하지 않음",
            )
        updated_edges.append(eid)
    gaps.append("Bucheon: 대주 4개사 명단 확인, 기관별 약정액 미공개(총 1,590억)")

    # ---------- Fine DC: Hyundai Motor Sec arranger + enrich ----------
    fine_h = SRC["fine_herald"]
    fine_d = SRC["fine_digitaltoday"]
    upsert_edge(
        edges,
        edge(
            "pf_hyundai_motor_sec_fine_arranger",
            "hyundai_motor_sec",
            "fine_dc_pfv",
            "ARRANGER",
            "현대차증권 → 파인디씨 PF 주선(맥락 2,959억+우선주)",
            project_id="gwangju_fine_dc",
            project_name="광주첨단(장성) 파인데이터센터",
            financing_stage="main_pf",
            amount_type="facility_total_context",
            evidence_status="기사상 참여 확인",
            participation_path="현대차증권 → 주선·일부 총액인수 후 셀다운 → 파인디씨PFV",
            amount_note="기사상 PF 2,959억+우선주 700억 주선 — 보유잔액은 셀다운 후 미확인",
            amount_krw_eok=None,
            facility_total_krw_eok=2959.0,
            roles=["arranger", "underwriter"],
            exposure_kind="arranger_role",
            contingent=True,
            source_url=fine_h["url"],
            source_title=fine_h["title"],
            source_date=fine_h["date"],
            source_ids=[fine_h["id"]],
            evidence_summary="헤럴드경제: 현대차증권이 PF 2959억·우선주 700억 주선, 선순위 319·중순위 150 총액인수 후 매각.",
        ),
        added_edges,
        updated_edges,
    )
    upsert_edge(
        edges,
        edge(
            "pf_hyundai_motor_sec_fine_underwrite",
            "hyundai_motor_sec",
            "fine_dc_pfv",
            "REFINANCING_UNDERWRITE",
            "현대차증권 → 파인디씨 선·중순위 총액인수 후 셀다운",
            project_id="gwangju_fine_dc",
            project_name="광주첨단(장성) 파인데이터센터",
            financing_stage="main_pf",
            amount_type="underwrite_commitment",
            evidence_status="기사상 참여 확인",
            participation_path="현대차증권 → 총액인수(선 319+중 150) → 셀다운 → 최종투자자",
            amount_note="기사상 총액인수 469억(선 319+중 150) 후 매각 — 현재 잔액 미확인",
            amount_krw_eok=469.0,
            facility_total_krw_eok=2959.0,
            roles=["underwriter"],
            exposure_kind="underwrite_then_selldown",
            contingent=True,
            relationship_status="historical",
            source_url=fine_h["url"],
            source_title=fine_h["title"],
            source_date=fine_h["date"],
            source_ids=[fine_h["id"]],
            evidence_summary="헤럴드경제: 선순위 319억·중순위 150억 총액인수 후 다른 투자자에게 매각.",
        ),
        added_edges,
        updated_edges,
    )
    for eid in ("pf_kb_balhae_fine", "pf_hana_fine_lender", "pf_kb_fine_lender", "pf_daewoo_fine_guar", "pf_daewoo_fine_epc"):
        ex = next((x for x in edges if x["id"] == eid), None)
        if not ex:
            continue
        patch_existing(
            ex,
            project_id="gwangju_fine_dc",
            project_name="광주첨단(장성) 파인데이터센터",
            evidence_status="기사상 참여 확인",
            financing_stage=ex.get("financing_stage")
            or ("construction" if "epc" in eid or "guar" in eid else "main_pf"),
        )
        if "guar" in eid:
            patch_existing(
                ex,
                amount_type="guarantee_limit",
                amount_krw_eok=2959.0,
                contingent_obligation=True,
                exposure_kind="completion_debt_assumption",
                participation_path="대우건설 → 책임준공 미이행 시 채무인수 → 하나·KB 등 대주",
                amount_note="기사상 채무보증 한도 2,959억(책임준공 미이행 시) — 확정 현금투자 아님",
                source_url=fine_d["url"],
                source_title=fine_d["title"],
                source_date=fine_d["date"],
            )
        updated_edges.append(eid)
    gaps.append("Fine DC: 공시 '하나은행, KB은행 등' — 기타 대주 이름·배분 미공개")

    # ---------- projects.json: magna_deogi ----------
    if not any(p["id"] == "magna_deogi" for p in proj["projects"]):
        proj["projects"].append(
            {
                "id": "magna_deogi",
                "name": "Magna Goyang Deogi Data Center",
                "name_ko": "마그나 고양 덕이 데이터센터",
                "name_en": "Magna Goyang Deogi IDC",
                "location": "경기 고양시 일산서구 덕이동 309-56",
                "address": "덕이동 309-56번지 일원",
                "country": "KR",
                "region": "KR",
                "developer": "gs_enc",
                "owner": "magna_pfv",
                "operator": None,
                "spv": "magna_pfv",
                "tenant": None,
                "construction_company": "gs_enc",
                "trust_company": "korealand_trust",
                "construction_stage": "under_construction",
                "financing_disclosed": True,
                "shock_role": "kr_pf_borrower",
                "note": "더벨: 본PF/리파이낸싱 2,730억 단일 트랜치. 대주 개별금액 미공개.",
                "target_completion": "2025",
                "critical_it_load_mw": 20,
                "capacity_note": "수전 20MW (더벨)",
                "capex_native_krw_b": 273.0,
                "other_financing_note": "Facility KRW 2730bn main PF (equal amount refinanced Sep 2025). Per-lender amounts undisclosed.",
                "source_ids": [magna_src["id"]],
                "verification_date": TODAY,
                "missing": ["per_lender_amounts", "tenant_name", "current_outstanding"],
                "korean_link_class": "direct_contract",
                "sources": [
                    {
                        "title": magna_src["title"],
                        "url": magna_src["url"],
                        "date": magna_src["date"],
                    }
                ],
            }
        )

    # Mark financed KR projects
    for pid in (
        "casequare_gasan",
        "camsquare_ansan",
        "camsquare_yongin",
        "bucheon_samjeong_ai",
        "gwangju_fine_dc",
        "magna_deogi",
    ):
        pr = next((p for p in proj["projects"] if p["id"] == pid), None)
        if pr:
            pr["financing_disclosed"] = True

    # Rebuild node list
    net["nodes"] = list(by.values())
    net["edges"] = edges
    net["sources"] = list(sources.values())
    net["meta"]["as_of"] = TODAY
    net["meta"]["disclaimer"] = (
        (net["meta"].get("disclaimer") or "")
        + " Finance exposures use reliable news only; amounts typed (commitment/outstanding/guarantee). "
        "Syndicate totals are not assigned to each lender. Unknown is never stored as zero."
    )

    report = {
        "as_of": TODAY,
        "added_nodes": sorted(set(added_nodes)),
        "added_edges": sorted(set(added_edges)),
        "updated_edges": sorted(set(updated_edges)),
        "corrections": corrections,
        "gaps": gaps,
        "counts": {
            "nodes": len(net["nodes"]),
            "edges": len(net["edges"]),
            "financial_edges": sum(
                1
                for e in edges
                if e.get("impact_channel") == "financial"
                or e.get("relationship_type")
                in (
                    "PROJECT_LOAN",
                    "CREDIT_ENHANCEMENT",
                    "ARRANGER",
                    "EQUITY_INVESTMENT",
                    "EQUITY_SPONSOR",
                    "REFINANCING_UNDERWRITE",
                )
            ),
            "projects_with_finance": sum(1 for p in proj["projects"] if p.get("financing_disclosed")),
        },
    }

    (PF / "network.json").write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PF / "projects.json").write_text(json.dumps(proj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PF / "_finance_expansion_v5_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["counts"], ensure_ascii=False, indent=2))
    print("added_nodes", len(report["added_nodes"]), report["added_nodes"])
    print("added_edges", len(report["added_edges"]))
    print("updated_edges", len(report["updated_edges"]))


if __name__ == "__main__":
    main()
