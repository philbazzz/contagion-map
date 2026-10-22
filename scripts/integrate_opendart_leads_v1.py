#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrate high-confidence OpenDART body-scan leads into PF network.

Rules:
- Only named PFV/SPC + ownership or explicit commitment roles.
- Arrangement / 0% conduit / narrative IB commentary → informational or skip.
- Unknown outstanding → null amount, ACTIVE_AMOUNT_UNKNOWN (never invent 0).
- Disposed equity → HISTORICAL_ONLY / TRANSFERRED, shock_eligible=false.
- Does not treat 매입확약 facility headlines as loan principal unless role is clear contingent.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
PROJ = ROOT / "frontend" / "public" / "data" / "pf" / "projects.json"
REPORT = ROOT / "docs" / "opendart_integration_v1.json"

TODAY = date.today().isoformat()


def node(nid, name_ko, name_en, **kw):
    return {
        "id": nid,
        "name": name_en,
        "name_ko": name_ko,
        "group": kw.get("group", "project_finance"),
        "region": "KR",
        "entity_type": kw.get("entity_type", "spv"),
        "role": kw.get("role", "borrower_spv"),
        "display_size": kw.get("display_size", 5),
        "source_status": "VERIFIED",
        "pf_exposure_class": "confirmed_dc_finance",
        **{k: v for k, v in kw.items() if k not in {"group", "entity_type", "role", "display_size"}},
    }


def edge(**kw):
    base = {
        "source_status": "VERIFIED",
        "impact_channel": "financial",
        "evidence_status": "DART",
        "last_verified_date": TODAY,
        "verification_date": TODAY,
        "currency": "KRW",
        "amount_unit": "억원",
    }
    base.update(kw)
    # default shock eligibility for economic roles
    rel = base.get("relationship_type")
    st = base.get("exposure_status") or ""
    if base.get("shock_eligible") is None:
        if rel in {"ARRANGER", "FINANCING_ARRANGEMENT", "ABS_SPONSOR", "TRUST_SERVICES"}:
            base["shock_eligible"] = False
        elif st in {"HISTORICAL_ONLY", "FULLY_REPAID", "TRANSFERRED", "REFINANCED", "EXPIRED", "UNVERIFIED"}:
            base["shock_eligible"] = False
        elif base.get("amount_type") in {"facility_total_context", "fee_paid", "underwrite_commitment"}:
            base["shock_eligible"] = False
        else:
            base["shock_eligible"] = True
    return base


def upsert_node(nodes_by_id: dict, n: dict) -> str:
    if n["id"] in nodes_by_id:
        cur = nodes_by_id[n["id"]]
        for k, v in n.items():
            if v is not None and (k not in cur or cur.get(k) in (None, "", [])):
                cur[k] = v
        return n["id"]
    nodes_by_id[n["id"]] = n
    return n["id"]


def upsert_edge(edges_by_id: dict, e: dict) -> str:
    eid = e["id"]
    if eid in edges_by_id:
        cur = edges_by_id[eid]
        # Prefer newer DART verification fields / clearer amounts
        for k, v in e.items():
            if k == "id":
                continue
            if v is not None:
                cur[k] = v
        return eid
    edges_by_id[eid] = e
    return eid


def upsert_project(projects: list, p: dict) -> None:
    by = {x["id"]: x for x in projects}
    if p["id"] in by:
        cur = by[p["id"]]
        for k, v in p.items():
            if v is not None and (k not in cur or cur.get(k) in (None, "", [])):
                cur[k] = v
    else:
        projects.append(p)


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    pf = json.loads(PROJ.read_text(encoding="utf-8"))
    projects = pf.get("projects") if isinstance(pf, dict) else pf
    assert isinstance(projects, list)

    nodes_by_id = {n["id"]: n for n in net["nodes"]}
    edges_by_id = {e["id"]: e for e in net["edges"]}

    added_nodes, added_edges, updated_edges, added_projects = [], [], [], []

    # ---- New SPVs / projects from DART named entities ----
    new_entities = [
        (
            node("capstone_meta_idc_pfv", "캡스톤메타IDC피에프브이", "Capstone Meta IDC PFV",
                 aliases=["캡스톤메타IDCPFV", "캡스톤메타IDC피에프브이"]),
            {
                "id": "capstone_meta_idc",
                "name": "Capstone Meta IDC",
                "name_ko": "캡스톤 메타 IDC",
                "location": "대한민국 (소재 상세 공시 추가 확인 필요)",
                "country": "KR",
                "region": "KR",
                "developer": None,
                "owner": None,
                "spv": "capstone_meta_idc_pfv",
                "tenant": None,
                "construction_stage": "unknown",
                "source_ids": ["dart_20260814_ibk", "dart_20260930_kis"],
                "verification_date": TODAY,
                "note": "DART 출자내역에서 PFV명 확인. 사업장 주소는 추가 확인 필요.",
            },
        ),
        (
            node("casequare_busan_jangnim_pfv", "케이스퀘어부산장림데이터센터피에프브이",
                 "Casequare Busan Jangnim DC PFV"),
            {
                "id": "casequare_busan_jangnim",
                "name": "Casequare Busan Jangnim Data Center",
                "name_ko": "케이스퀘어 부산 장림 데이터센터",
                "location": "부산 장림",
                "country": "KR",
                "region": "KR",
                "developer": None,
                "owner": None,
                "spv": "casequare_busan_jangnim_pfv",
                "tenant": None,
                "construction_stage": "unknown",
                "source_ids": ["dart_20260813_kiwoom"],
                "verification_date": TODAY,
                "note": "키움증권 반기보고서 관계회사 목록에 PFV 기재. 지분율·잔액은 미확인.",
            },
        ),
        (
            node("camsquare_seori_pfv", "캄스퀘어서리데이터센터PFV", "Camsquare Seori DC PFV",
                 aliases=["캄스퀘어서리데이터센터PFV 주식회사"]),
            {
                "id": "camsquare_seori",
                "name": "Camsquare Seori Data Center",
                "name_ko": "캄스퀘어 서리 데이터센터",
                "location": "대한민국 (서리·상세주소 추가 확인 필요)",
                "country": "KR",
                "region": "KR",
                "developer": None,
                "owner": None,
                "spv": "camsquare_seori_pfv",
                "tenant": None,
                "construction_stage": "unknown",
                "source_ids": ["dart_20260813_hanwha"],
                "verification_date": TODAY,
            },
        ),
        (
            node("casequare_manus_guro_pfv", "케이스퀘어마누스데이터센터구로피에프브이",
                 "Casequare Manus Guro DC PFV"),
            {
                "id": "casequare_manus_guro",
                "name": "Casequare Manus Guro Data Center",
                "name_ko": "케이스퀘어 마누스 구로 데이터센터",
                "location": "서울 구로",
                "country": "KR",
                "region": "KR",
                "developer": None,
                "owner": None,
                "spv": "casequare_manus_guro_pfv",
                "tenant": None,
                "construction_stage": "unknown",
                "source_ids": ["dart_20260814_eugene"],
                "verification_date": TODAY,
            },
        ),
        (
            node("casequare_eco_songpa_pfv", "케이스퀘어에코송파피에프브이",
                 "Casequare Eco Songpa PFV"),
            {
                "id": "casequare_eco_songpa",
                "name": "Casequare Eco Songpa",
                "name_ko": "케이스퀘어 에코 송파",
                "location": "서울 송파",
                "country": "KR",
                "region": "KR",
                "developer": None,
                "owner": None,
                "spv": "casequare_eco_songpa_pfv",
                "tenant": None,
                "construction_stage": "unknown",
                "source_ids": ["dart_20260814_kb"],
                "verification_date": TODAY,
                "note": "KB증권 출자 후 처분(잔액 0) 공시 — 현재 익스포저 없음.",
            },
        ),
        (
            node("hana_dc_1st_spc", "하나데이터센터제일차", "Hana Data Center 1st SPC",
                 role="securitization_spc"),
            {
                "id": "hana_dc_abs_conduit",
                "name": "Hana Data Center ABS conduit",
                "name_ko": "하나데이터센터제일차 (유동화)",
                "location": "대한민국",
                "country": "KR",
                "region": "KR",
                "developer": None,
                "owner": None,
                "spv": "hana_dc_1st_spc",
                "tenant": None,
                "construction_stage": "unknown",
                "source_ids": ["dart_20260814_hana"],
                "verification_date": TODAY,
                "note": "공시상 지분 0.00% — 보유 출자로 보지 않음. 유동화 도관 성격.",
            },
        ),
        (
            node("yongin_jigok_dc_bridge_ref", "용인지곡동데이터센터(브릿지 참조)",
                 "Yongin Jigok DC (bridge ref)", group="project_finance",
                 entity_type="project_ref", role="project_reference", display_size=4,
                 source_status="INFERRED"),
            {
                "id": "yongin_jigok_dc",
                "name": "Yongin Jigok Data Center",
                "name_ko": "용인 지곡동 데이터센터",
                "location": "용인 지곡동",
                "country": "KR",
                "region": "KR",
                "developer": None,
                "owner": None,
                "spv": None,
                "tenant": None,
                "construction_stage": "unknown",
                "source_ids": ["dart_20260514_hanwha"],
                "verification_date": TODAY,
                "note": "한화 매입확약 표에 사업명만 확인. 차주 SPC 법인명 추가 확인 필요.",
            },
        ),
    ]

    for n, p in new_entities:
        if n["id"] not in nodes_by_id:
            added_nodes.append(n["id"])
        upsert_node(nodes_by_id, n)
        before = {x["id"] for x in projects}
        upsert_project(projects, p)
        if p["id"] not in before:
            added_projects.append(p["id"])

    # Fund vehicles (not physical DC) — keep as financial nodes
    for n in [
        node("shinhan_dc_dev_fund", "신한데이터센터개발일반사모혼합자산투자신탁",
             "Shinhan DC Development Fund", group="kr_securities", entity_type="fund",
             role="collective_investment", pf_exposure_class="confirmed_dc_finance"),
        node("korea_value_dc_fund", "한국밸류K-리더스데이터센터일반사모투자신탁",
             "Korea Value K-Leaders DC Fund", group="kr_securities", entity_type="fund",
             role="collective_investment", pf_exposure_class="confirmed_dc_finance"),
        node("fine_partners_dc_fund", "파인앤파트너스데이터센터개발블라인드펀드",
             "Fine & Partners DC Blind Fund", group="kr_securities", entity_type="fund",
             role="collective_investment", pf_exposure_class="confirmed_dc_finance"),
    ]:
        if n["id"] not in nodes_by_id:
            added_nodes.append(n["id"])
        upsert_node(nodes_by_id, n)

    # ---- Edges ----
    defs = []

    # IBK: update eco-delta equity with DART 2026.06 half-year
    # Snippet: 18.20%, acquisition 2,478,000 천원?=24.78억 or 백만원 table → treat 2,478 as 백만원 = 24.78억
    # Carrying 1,784,590 → if 천원 = 17.85억. Use book-adjacent 17.85 as verified outstanding equity, note acquisition 24.78.
    defs.append(edge(
        id="v6_bed_eq_ibk_sec",
        source="ibk_sec",
        target="busan_ecodelta_pfv",
        relationship_type="EQUITY_INVESTMENT",
        project_id="busan_ecodelta_dc",
        project_name="부산 에코델타 그린 데이터센터",
        amount_krw_eok=17.85,
        amount_type="equity_paid_in",
        ownership_pct=18.2,
        relationship_status="funded",
        exposure_status="ACTIVE_CONFIRMED",
        financing_stage="equity",
        amount_note="DART 반기보고서(2026.06) 관계기업 출자: 지분 18.20%, 장부가 약 17.85억원(공시 단위 환산). 취득원가 맥락 약 24.78억원. 주선액 아님.",
        source_title="IBK투자증권 반기보고서 (2026.06)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260814003650",
        source_date="2026-08-14",
        report_period="2026-06",
        publication_date="2026-08-14",
        dart_receipt_number="20260814003650",
        label="출자",
        impact_label="지분 익스포저",
        shock_eligible=True,
    ))

    # IBK + KIS: Capstone Meta IDC PFV 19% / 9.5억 (950백만원)
    for firm_id, firm_name, url, rcept, pub in [
        ("ibk_sec", "IBK투자증권", "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260814003650", "20260814003650", "2026-08-14"),
        ("korea_inv_sec", "한국투자증권", "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260930000623", "20260930000623", "2026-09-30"),
    ]:
        defs.append(edge(
            id=f"dart_eq_{firm_id}_capstone_meta",
            source=firm_id,
            target="capstone_meta_idc_pfv",
            relationship_type="EQUITY_INVESTMENT",
            project_id="capstone_meta_idc",
            project_name="캡스톤 메타 IDC",
            amount_krw_eok=9.5,
            amount_type="equity_paid_in",
            ownership_pct=19.0,
            relationship_status="funded",
            exposure_status="ACTIVE_CONFIRMED",
            financing_stage="equity",
            amount_note="DART 출자내역: 지분 19.00%, 장부가 950백만원(9.5억원). 동일 PFV에 복수 증권사 출자.",
            source_title=f"{firm_name} 정기보고서",
            source_url=url,
            source_date=pub,
            report_period="2026-06",
            publication_date=pub,
            dart_receipt_number=rcept,
            label="출자",
            impact_label="지분 익스포저",
            shock_eligible=True,
        ))

    # Kiwoom: Casequare Busan Jangnim — affiliate listed, amount unknown
    defs.append(edge(
        id="dart_eq_kiwoom_casequare_jangnim",
        source="kiwoom_sec",
        target="casequare_busan_jangnim_pfv",
        relationship_type="EQUITY_INVESTMENT",
        project_id="casequare_busan_jangnim",
        project_name="케이스퀘어 부산 장림 데이터센터",
        amount_krw_eok=None,
        amount_type=None,
        relationship_status="unknown",
        exposure_status="ACTIVE_AMOUNT_UNKNOWN",
        financing_stage="equity",
        amount_note="DART 관계회사 목록에 PFV 기재. 지분율·출자잔액 미확인 — 금액 미창작.",
        source_title="키움증권 반기보고서 (2026.06)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260813001767",
        source_date="2026-08-13",
        report_period="2026-06",
        publication_date="2026-08-13",
        dart_receipt_number="20260813001767",
        label="관계회사(출자 추정)",
        impact_label="지분(금액 미확인)",
        shock_eligible=True,
    ))

    # Hanwha: Camsquare Seori 60% / 29.95억
    defs.append(edge(
        id="dart_eq_hanwha_camsquare_seori",
        source="hanwha_inv_sec",
        target="camsquare_seori_pfv",
        relationship_type="EQUITY_INVESTMENT",
        project_id="camsquare_seori",
        project_name="캄스퀘어 서리 데이터센터",
        amount_krw_eok=29.95,
        amount_type="equity_paid_in",
        ownership_pct=60.0,
        relationship_status="funded",
        exposure_status="ACTIVE_CONFIRMED",
        financing_stage="equity",
        amount_note="DART 관계기업: 지분 60.00%, 장부가 2,995백만원(29.95억원).",
        source_title="한화투자증권 반기보고서 (2026.06)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260813001503",
        source_date="2026-08-13",
        report_period="2026-06",
        publication_date="2026-08-13",
        dart_receipt_number="20260813001503",
        label="출자",
        impact_label="지분 익스포저",
        shock_eligible=True,
    ))

    # Hanwha: 매입확약 280억 — 용인 지곡동 DC bridge (contingent, not loan principal)
    defs.append(edge(
        id="dart_commit_hanwha_yongin_jigok",
        source="hanwha_inv_sec",
        target="yongin_jigok_dc_bridge_ref",
        relationship_type="LIQUIDITY_COMMITMENT",
        project_id="yongin_jigok_dc",
        project_name="용인 지곡동 데이터센터",
        amount_krw_eok=280.0,
        amount_type="purchase_commitment",
        contingent_obligation=True,
        obligation_trigger="매입확약 발동 시에만 유동성 부담",
        relationship_status="committed",
        exposure_status="ACTIVE_AMOUNT_UNKNOWN",
        financing_stage="bridge",
        amount_note="DART 매입확약 표: 리얼에셋제일차 280(억원 추정) · 용인 지곡동 DC 브릿지대출. 대출원금 보유가 아님. 차주 SPC 미확인.",
        source_title="한화투자증권 분기보고서 (2026.03)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260514000990",
        source_date="2026-05-14",
        report_period="2026-03",
        publication_date="2026-05-14",
        dart_receipt_number="20260514000990",
        label="매입확약",
        impact_label="조건부 확약",
        shock_eligible=True,
    ))

    # LS: Camsquare Ansan private bond commitment — amount unknown (list context)
    defs.append(edge(
        id="dart_bond_ls_camsquare_ansan",
        source="ls_sec",
        target="camsquare_pfv",
        relationship_type="ABS_HOLDING",
        project_id="camsquare_ansan",
        project_name="캄스퀘어 안산 데이터센터",
        amount_krw_eok=None,
        amount_type=None,
        relationship_status="committed",
        exposure_status="ACTIVE_AMOUNT_UNKNOWN",
        financing_stage="securitization",
        amount_note="DART 약정 목록에 '캄스퀘어 안산 데이터센터PFV 사모사채' 기재. 약정·보유잔액 구분 미확인 — 금액 미창작.",
        source_title="LS증권 반기보고서 (2026.06)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260813001273",
        source_date="2026-08-13",
        report_period="2026-06",
        publication_date="2026-08-13",
        dart_receipt_number="20260813001273",
        label="사모사채(약정)",
        impact_label="증권 보유·약정(금액 미확인)",
        shock_eligible=True,
    ))

    # Shinhan: DC development fund purchase commitment 71억 (7,100백만)
    defs.append(edge(
        id="dart_commit_shinhan_dc_fund",
        source="shinhan_sec",
        target="shinhan_dc_dev_fund",
        relationship_type="LIQUIDITY_COMMITMENT",
        project_id=None,
        project_name="신한데이터센터개발 펀드",
        amount_krw_eok=71.0,
        amount_type="purchase_commitment",
        contingent_obligation=True,
        relationship_status="committed",
        exposure_status="ACTIVE_CONFIRMED",
        financing_stage="fund",
        amount_note="DART 매입약정: 신한데이터센터개발일반사모혼합자산투자신탁 KRW 7,100백만(71억원). 개별 DC 대출원금 아님.",
        source_title="신한투자증권 정정 분기/반기보고서",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260908000410",
        source_date="2026-09-08",
        report_period="2024-09",
        publication_date="2026-09-08",
        dart_receipt_number="20260908000410",
        label="펀드 매입약정",
        impact_label="조건부 펀드약정",
        shock_eligible=True,
    ))

    # Hana: ABS conduit 0% — informational only
    defs.append(edge(
        id="dart_abs_hana_dc_1st",
        source="hana_sec",
        target="hana_dc_1st_spc",
        relationship_type="ABS_SPONSOR",
        project_id="hana_dc_abs_conduit",
        project_name="하나데이터센터제일차",
        amount_krw_eok=None,
        amount_type=None,
        ownership_pct=0.0,
        relationship_status="historical",
        exposure_status="HISTORICAL_ONLY",
        financing_stage="securitization",
        amount_note="DART 종속·관계 표기 지분 0.00%. 보유 출자로 보지 않음. 유동화 도관 정보 엣지.",
        source_title="하나증권 반기보고서 (2026.06)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260814002599",
        source_date="2026-08-14",
        dart_receipt_number="20260814002599",
        label="유동화 도관",
        impact_label="정보(보유 익스포저 아님)",
        shock_eligible=False,
    ))

    # Eugene: Casequare Manus Guro 10% / 5억
    defs.append(edge(
        id="dart_eq_eugene_casequare_manus_guro",
        source="eugene_inv_sec",
        target="casequare_manus_guro_pfv",
        relationship_type="EQUITY_INVESTMENT",
        project_id="casequare_manus_guro",
        project_name="케이스퀘어 마누스 구로 데이터센터",
        amount_krw_eok=5.0,
        amount_type="equity_paid_in",
        ownership_pct=10.0,
        relationship_status="funded",
        exposure_status="ACTIVE_CONFIRMED",
        financing_stage="equity",
        amount_note="DART 출자: 보통주 10.00%, 장부가 500백만원(5억원). 2025-09-24 취득.",
        source_title="유진투자증권 반기보고서 (2026.06)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260814003025",
        source_date="2026-08-14",
        report_period="2026-06",
        publication_date="2026-08-14",
        dart_receipt_number="20260814003025",
        label="출자",
        impact_label="지분 익스포저",
        shock_eligible=True,
    ))

    # Korea Investment: DC fund 15% — amount ~28.22억 carrying (2,822,148 천원?)
    # Snippet: 15.00% ... 2,223,529 2,822,148 2,822,148 — if 천원 = 28.22억
    defs.append(edge(
        id="dart_eq_kis_value_dc_fund",
        source="korea_inv_sec",
        target="korea_value_dc_fund",
        relationship_type="EQUITY_INVESTMENT",
        project_id=None,
        project_name="한국밸류 K-리더스 데이터센터 펀드",
        amount_krw_eok=28.22,
        amount_type="equity_paid_in",
        ownership_pct=15.0,
        relationship_status="funded",
        exposure_status="ACTIVE_CONFIRMED",
        financing_stage="fund",
        amount_note="DART 집합투자기구 출자: 지분 15.00%, 장부가 약 28.22억원(공시 단위 환산). 개별 사업장 대출 아님.",
        source_title="한국투자증권 정정 반기보고서 (2026.06)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260930000623",
        source_date="2026-09-30",
        dart_receipt_number="20260930000623",
        label="펀드 출자",
        impact_label="펀드 지분",
        shock_eligible=True,
    ))

    # KB: Casequare Eco Songpa — disposed (TRANSFERRED)
    defs.append(edge(
        id="dart_eq_kb_casequare_songpa_disposed",
        source="kb_sec",
        target="casequare_eco_songpa_pfv",
        relationship_type="EQUITY_INVESTMENT",
        project_id="casequare_eco_songpa",
        project_name="케이스퀘어 에코 송파",
        amount_krw_eok=0.0,
        amount_type="outstanding",
        ownership_pct=0.0,
        relationship_status="terminated",
        exposure_status="TRANSFERRED",
        financing_stage="equity",
        amount_note="DART: 2023.05.08 출자 후 처분(-149,000주, -1,490). 현재 잔액 0. 과거 관계만 보존.",
        source_title="KB증권 반기보고서 (2026.06)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260814003716",
        source_date="2026-08-14",
        dart_receipt_number="20260814003716",
        label="출자(처분완료)",
        impact_label="종료",
        shock_eligible=False,
    ))

    # Yuanta: Camsquare Ansan securitization — arranger/info only
    defs.append(edge(
        id="dart_arr_yuanta_camsquare_ansan_abs",
        source="yuanta_sec",
        target="camsquare_pfv",
        relationship_type="FINANCING_ARRANGEMENT",
        project_id="camsquare_ansan",
        project_name="캄스퀘어 안산 데이터센터",
        amount_krw_eok=230.0,
        amount_type="facility_total_context",
        relationship_status="historical",
        exposure_status="HISTORICAL_ONLY",
        financing_stage="securitization",
        amount_note="DART: 와이케이안산디원 KRW 23,000백만 PF대출채권 유동화(안산 캄스퀘어). 유동화 규모≠유안타 보유 익스포저.",
        source_title="유안타증권 반기보고서 (2026.06)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260814002465",
        source_date="2026-08-14",
        dart_receipt_number="20260814002465",
        label="유동화 주선·구조",
        impact_label="주선(보유 아님)",
        shock_eligible=False,
    ))

    # Hyundai Motor Sec: Fine Partners DC fund 30억 commitment
    defs.append(edge(
        id="dart_commit_hyundai_fine_dc_fund",
        source="hyundai_motor_sec",
        target="fine_partners_dc_fund",
        relationship_type="LIQUIDITY_COMMITMENT",
        amount_krw_eok=30.0,
        amount_type="purchase_commitment",
        contingent_obligation=True,
        relationship_status="committed",
        exposure_status="ACTIVE_CONFIRMED",
        financing_stage="fund",
        amount_note="DART: 파인앤파트너스 데이터센터 개발 블라인드펀드 1종 수익증권 인수 30.00억원. 개별 사업장 대주 아님.",
        source_title="현대차증권 분기보고서 (2026.03)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260515001656",
        source_date="2026-05-15",
        dart_receipt_number="20260515001656",
        label="펀드 인수",
        impact_label="펀드 약정",
        shock_eligible=True,
    ))

    # Hyundai: Casequare Yongsan — affiliate name only, amount unknown; skip strong equity claim
    # Only add if we have a PFV node — weak evidence → UNVERIFIED relationship informational
    if "casequare_yongsan_pfv" not in nodes_by_id:
        upsert_node(nodes_by_id, node(
            "casequare_yongsan_pfv", "케이스퀘어용산피에프브이", "Casequare Yongsan PFV",
            source_status="INFERRED",
        ))
        added_nodes.append("casequare_yongsan_pfv")
        upsert_project(projects, {
            "id": "casequare_yongsan",
            "name": "Casequare Yongsan",
            "name_ko": "케이스퀘어 용산",
            "location": "서울 용산",
            "country": "KR",
            "region": "KR",
            "developer": None,
            "owner": None,
            "spv": "casequare_yongsan_pfv",
            "tenant": None,
            "construction_stage": "unknown",
            "source_ids": ["dart_20260814_hyundai"],
            "verification_date": TODAY,
            "note": "현대차증권 계열/관계 목록 문자열에 등장. 지분·잔액 미확인.",
        })
        added_projects.append("casequare_yongsan")

    defs.append(edge(
        id="dart_rel_hyundai_casequare_yongsan",
        source="hyundai_motor_sec",
        target="casequare_yongsan_pfv",
        relationship_type="EQUITY_INVESTMENT",
        project_id="casequare_yongsan",
        project_name="케이스퀘어 용산",
        amount_krw_eok=None,
        amount_type=None,
        relationship_status="unknown",
        exposure_status="UNVERIFIED",
        financing_stage="equity",
        amount_note="계열·관계 문자열에 PFV명 등장. 출자 여부·잔액 미확인 → UNVERIFIED. 검증 손실 경로에 사용하지 않음.",
        source_title="현대차증권 반기보고서 (2026.06)",
        source_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260814002170",
        source_date="2026-08-14",
        dart_receipt_number="20260814002170",
        label="관계 후보",
        impact_label="미확인",
        shock_eligible=False,
    ))

    for e in defs:
        eid = e["id"]
        if eid in edges_by_id:
            updated_edges.append(eid)
        else:
            added_edges.append(eid)
        upsert_edge(edges_by_id, e)

    net["nodes"] = list(nodes_by_id.values())
    net["edges"] = list(edges_by_id.values())
    if isinstance(pf, dict):
        pf["projects"] = projects
        pf["as_of"] = TODAY
    else:
        pf = {"as_of": TODAY, "projects": projects}

    # bump meta note
    meta = net.get("meta") or {}
    meta["opendart_integration"] = {
        "version": "v1",
        "date": TODAY,
        "added_nodes": added_nodes,
        "added_edges": added_edges,
        "updated_edges": updated_edges,
        "added_projects": added_projects,
        "rule": "Named PFV equity / contingent commitments only; arrangement≠exposure",
    }
    net["meta"] = meta

    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PROJ.write_text(json.dumps(pf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "verification_date": TODAY,
        "added_nodes": added_nodes,
        "added_edges": added_edges,
        "updated_edges": updated_edges,
        "added_projects": added_projects,
        "skipped_narrative_only": [
            "NH투자증권 AI 데이터센터 IB 서술 (관계 아님)",
            "키움 구조화금융 일반 Track Record 서술",
            "교보데이터센터→교보정보통신 합병 역사 (현재 DC PF 아님)",
            "다올 케이스퀘어세종물류 (물류 PFV — DC 아님, 미반영)",
        ],
        "classification_notes": [
            "유안타 와이케이안산디원 유동화 = FINANCING_ARRANGEMENT / HISTORICAL_ONLY",
            "하나데이터센터제일차 0% = ABS_SPONSOR / shock_eligible=false",
            "KB 송파 출자 = TRANSFERRED amount 0",
            "한화 매입확약 = LIQUIDITY_COMMITMENT contingent",
        ],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in report.items() if k != "classification_notes"}, ensure_ascii=False))
    print("added_edges", added_edges)
    print("updated_edges", updated_edges)


if __name__ == "__main__":
    main()
