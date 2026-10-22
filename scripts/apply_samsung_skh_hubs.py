"""
Samsung Electronics + SK hynix hub expansion (evidence-first).
As of 2026-10-20. Adds only disclosure-backed entities/edges; updates dossiers.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "backend" / "data"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save(name: str, obj: dict) -> None:
    (DATA / name).write_text(
        json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def rel(
    id_: str,
    source: str,
    target: str,
    relationship_type: str,
    impact_channel: str,
    label: str,
    source_status: str,
    source_ids: list[str],
    explanation: str,
    amount_note: str = "금액 미공시 / 해당 없음",
    amount_usd_m: float | None = None,
    roles: list[str] | None = None,
) -> dict:
    return {
        "id": id_,
        "source": source,
        "target": target,
        "relationship_type": relationship_type,
        "impact_channel": impact_channel,
        "label": label,
        "impact_label": label,
        "source_status": source_status,
        "source_ids": source_ids,
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": amount_usd_m,
        "amount_note": amount_note,
        "roles": roles or [],
        "explanation": explanation,
    }


NEW_SOURCES = [
    {
        "id": "S_SMSN_BR_FY25",
        "title": "삼성전자 제57기 사업보고서 (FY2025) — 주요 매출처·원재료·Tesla 파운드리 수주",
        "publisher": "DART / KIND / Samsung IR",
        "date": "2026-03-10",
        "url": "https://kind.krx.co.kr/external/2026/03/10/001404/20260310003123/11011.htm",
        "used_for": "Alphabet·Apple top-5 customers; Qualcomm AP supplier; Tesla foundry $16.544B; DS/DX financials; cash/debt",
        "kind": "dart",
    },
    {
        "id": "S_SMSN_IR_FY25_EN",
        "title": "Samsung Electronics 2025 Business Report (English IR PDF)",
        "publisher": "Samsung IR",
        "date": "2026-03",
        "url": "https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_4Q_Interim_Report.pdf",
        "used_for": "English confirmation of FY2025 major customers and DS division overview",
        "kind": "ir",
    },
    {
        "id": "S_NVDA_SMSN_AIF",
        "title": "NVIDIA and Samsung Build AI Factory to Transform Global Intelligent Manufacturing",
        "publisher": "NVIDIA Investor Relations",
        "date": "2025-10-31",
        "url": "https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-and-Samsung-Build-AI-Factory-to-Transform-Global-Intelligent-Manufacturing/default.aspx",
        "used_for": "NVIDIA–Samsung AI Factory / HBM3E·HBM4 supply collaboration announcement",
        "kind": "press",
    },
    {
        "id": "S_SKH_ASML_EUV",
        "title": "SK하이닉스 ASML EUV 장비 취득 결정 (약 11.9496조 원, ~2027.12)",
        "publisher": "DART / Asia Business Daily 요약",
        "date": "2026-03-24",
        "url": "https://www.asiae.co.kr/en/article/2026032413552957143",
        "used_for": "SK hynix disclosed EUV procurement from ASML (~KRW 11.95T through Dec 2027)",
        "kind": "dart",
    },
    {
        "id": "S_SKH_CFS_FY25",
        "title": "SK hynix Inc. Consolidated Financial Statements FY2025",
        "publisher": "SK hynix IR",
        "date": "2026-01",
        "url": "https://mis-prod-koce-homepage-cdn-01-blob-ep.azureedge.net/web/attach/121822586381465204.pdf",
        "used_for": "SK hynix FY2025 cash, borrowings, PPE acquisitions (CapEx)",
        "kind": "ir",
    },
    {
        "id": "S_SKH_NVDA_2026",
        "title": "Nvidia, SK hynix sign multiyear deal for AI factories",
        "publisher": "The Korea Herald (company statements)",
        "date": "2026-06-08",
        "url": "https://www.koreaherald.com/article/10765670",
        "used_for": "Multi-year NVIDIA–SK hynix technology partnership for AI memory (not a disclosed fixed-price HBM offtake)",
        "kind": "press",
    },
    {
        "id": "S_HANMI_DART_SKH_2025",
        "title": "한미반도체 단일판매ㆍ공급계약체결 — SK하이닉스 HBM TC 본더 (2025.05)",
        "publisher": "DART",
        "date": "2025-05-16",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20250516800084",
        "used_for": "Hanmi → SK hynix HBM TC bonder ~KRW 42.8B (2025-05)",
        "kind": "dart",
    },
    {
        "id": "S_JUSUNG_DART_SKH",
        "title": "주성엔지니어링–SK하이닉스 반도체 제조장비 공급계약 (2024.07, KRW 194억) 및 사업보고서 기재",
        "publisher": "DART / KIND 사업보고서",
        "date": "2024-07-10",
        "url": "https://kind.krx.co.kr/external/2026/03/18/000306/20260318001621/11011.htm",
        "used_for": "Jusung Engineering equipment supply to SK hynix (DART + FY2025 business report history)",
        "kind": "dart",
    },
]

NEW_ENTITIES = [
    {
        "id": "qualcomm",
        "name": "Qualcomm",
        "name_ko": "퀄컴",
        "group": "semiconductor",
        "sector": "반도체 · 모바일 AP / 모뎀",
        "entity_type": "company",
        "role": "Samsung DX 모바일 AP 주요 매입처 (사업보고서)",
        "description": "삼성전자 FY2025 사업보고서 DX 부문 모바일AP 솔루션 주요 매입처로 Qualcomm·MediaTek을 명시.",
        "listed": True,
        "ticker": "QCOM",
        "exchange": "Nasdaq",
        "quote_currency": "USD",
        "listing_note": None,
        "display_size": 7,
        "source_status": "VERIFIED",
        "source_ids": ["S_SMSN_BR_FY25"],
        "key_drivers": ["스마트폰 AP 수요", "삼성·OEM 조달"],
    },
    {
        "id": "tesla",
        "name": "Tesla",
        "name_ko": "테슬라",
        "group": "customer",
        "sector": "자동차 · AI/자율주행 반도체 수요",
        "entity_type": "company",
        "role": "Samsung Foundry 위탁생산 발주처 (수주 공시)",
        "description": "삼성전자 FY2025 사업보고서 수주: DS Foundry–Tesla 반도체 위탁생산 계약(2025.07.26–2033.12.31) 총액 USD 16,544 million.",
        "listed": True,
        "ticker": "TSLA",
        "exchange": "Nasdaq",
        "quote_currency": "USD",
        "listing_note": None,
        "display_size": 7,
        "source_status": "VERIFIED",
        "source_ids": ["S_SMSN_BR_FY25"],
        "key_drivers": ["자동차 반도체 수요", "파운드리 장기 계약"],
    },
    {
        "id": "jusung_eng",
        "name": "Jusung Engineering",
        "name_ko": "주성엔지니어링",
        "group": "semiconductor",
        "sector": "반도체 장비 · ALD/CVD",
        "entity_type": "company",
        "role": "SK하이닉스 반도체 제조장비 공급사 (DART)",
        "description": "KOSDAQ 상장 반도체 장비사. FY2025 사업보고서에 SK하이닉스 공급계약 이력(2024.07 KRW 194억 등)을 기재.",
        "listed": True,
        "ticker": "036930",
        "exchange": "KOSDAQ",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 5,
        "source_status": "VERIFIED",
        "source_ids": ["S_JUSUNG_DART_SKH"],
        "key_drivers": ["메모리 장비 CAPEX", "SK하이닉스 투자 사이클"],
    },
]

NEW_RELS = [
    # --- Samsung hub ---
    rel(
        "c_apple_samsung",
        "apple",
        "samsung",
        "CUSTOMER",
        "customer",
        "Apple — Samsung top-5 customer (FY2025 BR)",
        "VERIFIED",
        ["S_SMSN_BR_FY25", "S_SMSN_IR_FY25_EN"],
        "삼성전자 제57기 사업보고서: 2025년 주요 매출처에 Apple 포함(5대 합계 매출 비중 약 15%). 제품별 금액·품목 세부 미공시.",
        roles=["Major customer"],
    ),
    rel(
        "c_alphabet_samsung",
        "alphabet",
        "samsung",
        "CUSTOMER",
        "customer",
        "Alphabet — Samsung top-5 customer (FY2025 BR)",
        "VERIFIED",
        ["S_SMSN_BR_FY25", "S_SMSN_IR_FY25_EN"],
        "삼성전자 제57기 사업보고서: 2025년 주요 매출처에 Alphabet 포함(알파벳순 열거). HBM/메모리 공급 세부 금액은 미공시.",
        roles=["Major customer"],
    ),
    rel(
        "s_samsung_qualcomm",
        "samsung",
        "qualcomm",
        "SUPPLIER",
        "supply_chain",
        "Samsung DX buys mobile AP from Qualcomm",
        "VERIFIED",
        ["S_SMSN_BR_FY25"],
        "삼성전자 FY2025 사업보고서 DX 원재료: 모바일AP 솔루션 주요 매입처 Qualcomm, MediaTek. 2025년 해당 품목 매입액 13조 8,272억 원(DX 원재료의 18.5%). Qualcomm 단독 금액은 미분리.",
        amount_note="DX 모바일AP 품목 합계 KRW 13.8272조 (Qualcomm+MediaTek)",
        roles=["AP supplier"],
    ),
    rel(
        "c_tesla_samsung",
        "tesla",
        "samsung",
        "CUSTOMER",
        "customer",
        "Tesla foundry offtake at Samsung DS (disclosed backlog)",
        "VERIFIED",
        ["S_SMSN_BR_FY25"],
        "삼성전자 FY2025 사업보고서 수주상황: DS Foundry–Tesla, Inc. 반도체 위탁생산. 계약 2025.07.26–2033.12.31, 수주총액 USD 16,544 million. 수량·기납품액은 영업비밀로 생략.",
        amount_usd_m=16544.0,
        amount_note="수주총액 USD 16,544M (계약기간 수요에 따라 변동 가능)",
        roles=["Foundry customer"],
    ),
    rel(
        "sp_nvidia_samsung_aif",
        "nvidia",
        "samsung",
        "STRATEGIC_PARTNERSHIP",
        "supply_chain",
        "NVIDIA–Samsung AI Factory / HBM collaboration",
        "VERIFIED",
        ["S_NVDA_SMSN_AIF", "S_NVDA_10K_FY26_MFG"],
        "NVIDIA IR(2025.10.31): Samsung과 AI Factory(5만+ GPU) 및 HBM3E·HBM4 공급 협력 발표. 기존 10-K상 foundry+memory 공급과 별개의 전략 협력 공지. 고정 단가·물량 계약액은 미공시.",
        roles=["Strategic collaborator"],
    ),
    # --- SK hynix hub ---
    rel(
        "s_skh_asml",
        "sk_hynix",
        "asml",
        "SUPPLIER",
        "supply_chain",
        "SK hynix EUV tools from ASML (~KRW 11.95T)",
        "VERIFIED",
        ["S_SKH_ASML_EUV"],
        "SK하이닉스 2026.03.24 공시: ASML EUV 노광장비 취득 약 11.9496조 원(2024말 자산총액 대비 약 9.97%), 이행 기한 ~2027.12. HBM·선단 DRAM(1c) 생산용. 설치·개조비 포함.",
        amount_note="약 KRW 11.9496조 (EUV 취득·설치, ~2027.12)",
        roles=["EUV equipment supplier"],
    ),
    rel(
        "s_skh_jusung",
        "sk_hynix",
        "jusung_eng",
        "SUPPLIER",
        "supply_chain",
        "SK hynix buys process tools from Jusung Engineering",
        "VERIFIED",
        ["S_JUSUNG_DART_SKH"],
        "주성엔지니어링 FY2025 사업보고서 및 2024.07 DART: SK하이닉스에 반도체 제조장비 공급(2024.07 계약 약 KRW 194억 등 다건). 지속적 장비 공급 관계로 확인.",
        amount_note="예시: 2024.07 계약 KRW 194.3억 (최근 매출 대비 6.82%)",
        roles=["ALD/CVD equipment supplier"],
    ),
    rel(
        "sp_nvidia_skh_tech",
        "nvidia",
        "sk_hynix",
        "STRATEGIC_PARTNERSHIP",
        "supply_chain",
        "NVIDIA–SK hynix multi-year AI memory tech partnership",
        "VERIFIED",
        ["S_SKH_NVDA_2026", "S_NVDA_10K_FY26_MFG"],
        "2026.06: NVIDIA·SK하이닉스가 AI 팩토리용 차세대 메모리 기술 로드맵을 위한 다년 기술 파트너십을 발표(회사 발언·보도). NVIDIA 10-K상 메모리 구매처 명시와 병행. 고정 HBM 물량·단가 계약액은 미공시 — 예상 점유율 보도는 제외.",
        roles=["Strategic memory partner"],
    ),
    rel(
        "sp_skh_tsmc",
        "sk_hynix",
        "tsmc",
        "STRATEGIC_PARTNERSHIP",
        "supply_chain",
        "SK hynix–TSMC HBM4 base-die / CoWoS alignment (inferred)",
        "INFERRED",
        ["S_NVDA_10K_FY26_MFG"],
        "HBM4부터 로직 베이스다이에 선단 파운드리 공정이 필요하며, 업계·경영진 발언상 SK하이닉스는 TSMC 공정을 활용하고 TSMC CoWoS가 NVIDIA GPU와 HBM을 통합. 양사 간 금액이 공시된 직접 공급계약은 확인되지 않아 INFERRED. NVIDIA↔TSMC·NVIDIA↔SKH 직접 에지는 별도 VERIFIED.",
        roles=["HBM base-die / packaging collaborator"],
    ),
]


def upsert_sources(src: dict) -> int:
    by_id = {s["id"]: s for s in src["sources"]}
    n = 0
    for s in NEW_SOURCES:
        if s["id"] not in by_id:
            src["sources"].append(s)
            n += 1
        else:
            by_id[s["id"]].update(s)
    return n


def upsert_entities(ent: dict) -> int:
    by_id = {e["id"]: e for e in ent["entities"]}
    n = 0
    for e in NEW_ENTITIES:
        if e["id"] not in by_id:
            ent["entities"].append(e)
            n += 1
        else:
            by_id[e["id"]].update(e)
    # Hub role / size upgrades
    for oid, patch in {
        "samsung": {
            "role": "글로벌 메모리·파운드리 허브 · NVIDIA/하이퍼스케일러 공급",
            "description": "FY2025 매출 333.6조 원. DS(메모리·Foundry·System LSI) + DX. NVIDIA 10-K상 파운드리·메모리 공급사; 사업보고서상 Apple·Alphabet 등 5대 매출처; Tesla 파운드리 장기 수주.",
            "display_size": 11,
            "source_ids": [
                "S_SMSN_BR_FY25",
                "S_SMSN_FY25",
                "S_NVDA_10K_FY26_MFG",
                "S_NVDA_SMSN_AIF",
            ],
            "key_drivers": [
                "HBM·DRAM 공급",
                "Foundry 수주",
                "하이퍼스케일러 메모리 수요",
                "설비투자(EUV)",
            ],
        },
        "sk_hynix": {
            "role": "HBM·AI 메모리 허브 · NVIDIA 핵심 공급 · 장비 생태계",
            "description": "FY2025 매출 97.15조·영업이익 47.21조 원. NVIDIA 메모리 공급(10-K) 및 다년 기술 파트너십. ASML EUV·한미반도체 TC본더·주성엔지니어링 등 장비 조달. CoreWeave와 직접 계약 미확인.",
            "display_size": 11,
            "source_ids": [
                "S_SKH_FY25",
                "S_SKH_CFS_FY25",
                "S_NVDA_10K_FY26_MFG",
                "S_SKH_ASML_EUV",
                "S_HANMI_DART_SKH_2025",
            ],
            "key_drivers": [
                "HBM 공급·수율",
                "NVIDIA·AI 수요",
                "EUV·후공정 장비",
                "설비투자",
            ],
        },
        "asml": {
            "description": "EUV 노광 사실상 독점. TSMC 외 SK하이닉스가 FY2026 공시로 ~11.95조 원 EUV 취득을 명시. Samsung도 EUV 핵심 수요처이나 개별 계약액은 미공시.",
            "source_ids": ["S_ASML_TSMC", "S_SKH_ASML_EUV"],
        },
        "hanmi_semi": {
            "description": "HBM TC 본더 선도. DART상 SK하이닉스·Micron 공급 확인(2025.05 SKH TC본더 ~428억 원 등). Samsung 확정 계약 공시는 미확인(논의 보도만).",
            "source_ids": [
                "S_HANMI_DART_SKH",
                "S_HANMI_DART_SKH_2025",
                "S_HANMI_DART_MICRON",
            ],
        },
    }.items():
        if oid in by_id:
            by_id[oid].update(patch)
    return n


def upsert_rels(relj: dict) -> int:
    by_id = {r["id"]: i for i, r in enumerate(relj["relationships"])}
    n = 0
    for r in NEW_RELS:
        if r["id"] in by_id:
            relj["relationships"][by_id[r["id"]]] = r
        else:
            relj["relationships"].append(r)
            n += 1
    # Enrich existing Samsung/SKH edges' explanations/sources
    for r in relj["relationships"]:
        if r["id"] == "sc_samsung_nv":
            r["label"] = "NVIDIA foundry + memory at Samsung (10-K named)"
            r["impact_label"] = r["label"]
            r["explanation"] = (
                "NVIDIA FY2026 10-K Manufacturing: uses Samsung as a wafer foundry and purchases memory from Samsung "
                "(with SK hynix and Micron). Distinct from the Oct 2025 AI Factory strategic announcement."
            )
            for sid in ("S_NVDA_10K_FY26_MFG", "S_SMSN_BR_FY25"):
                if sid not in r["source_ids"]:
                    r["source_ids"].append(sid)
        if r["id"] == "s_nvidia_skh":
            r["label"] = "NVIDIA purchases memory from SK hynix (10-K named)"
            r["impact_label"] = r["label"]
            r["explanation"] = (
                "NVIDIA FY2026 10-K: purchases memory from SK Hynix Inc., Micron, and Samsung. "
                "Separate from the 2026 multi-year technology partnership edge."
            )
            for sid in ("S_NVDA_10K_FY26_MFG", "S_SKH_FY25"):
                if sid not in r["source_ids"]:
                    r["source_ids"].append(sid)
        if r["id"] == "s_hanmi_skh":
            r["label"] = "SK hynix buys HBM TC bonders from Hanmi Semiconductor"
            r["impact_label"] = r["label"]
            r["explanation"] = (
                "한미반도체 DART 단일판매ㆍ공급계약: SK하이닉스향 HBM 제조용 TC 본더·장비 "
                "(예: 2025.05 약 KRW 428억, 2025.01·2025.11 추가 건). 지속 공급 관계."
            )
            for sid in ("S_HANMI_DART_SKH_2025",):
                if sid not in r["source_ids"]:
                    r["source_ids"].append(sid)
            r["amount_note"] = "예: 2025.05 계약 약 KRW 428억 (매출 대비 7.66%)"
    return n


def metric(
    id_: str,
    label: str,
    display: str,
    period: str,
    status: str,
    source_ids: list[str],
    currency: str = "KRW",
    value_native=None,
    note: str | None = None,
) -> dict:
    m = {
        "id": id_,
        "label": label,
        "value_usd_m": None,
        "currency": currency,
        "display": display,
        "period": period,
        "status": status,
        "source_ids": source_ids,
    }
    if value_native is not None:
        m["value_native"] = value_native
    if note:
        m["note"] = note
    return m


def update_profiles(prof: dict) -> None:
    bucket = prof.setdefault("profiles", {})
    bucket["samsung"] = {
        "as_of": "2025-12-31",
        "period_label": "FY2025 (K-IFRS consolidated)",
        "currency": "KRW",
        "reporting_currency": "KRW",
        "listing_currency": "KRW",
        "unit": "billion KRW",
        "overview": (
            "삼성전자(005930). DX·DS·SDC·Harman. FY2025 연결 매출 333.6조·영업이익 약 43.6조 원. "
            "DS 매출 130.1조·영업이익 24.9조. 5대 매출처(Alphabet, Apple 등) 합계 ~15%. "
            "NVIDIA 파운드리·메모리 공급; Tesla Foundry 수주 USD 16.5B; DX는 Qualcomm AP 매입."
        ),
        "metrics": [
            metric(
                "revenue",
                "매출액",
                "333.6조 원",
                "FY2025",
                "VERIFIED",
                ["S_SMSN_BR_FY25", "S_SMSN_FY25"],
                value_native=333606,
                note="KRW 333조 6,059억",
            ),
            metric(
                "operating_income",
                "영업이익",
                "43.6조 원",
                "FY2025",
                "VERIFIED",
                ["S_SMSN_FY25", "S_SMSN_SOI_FY25"],
                value_native=43600,
                note="연결; 부문 합계 DX 12.85 + DS 24.86 + SDC 4.12 + Harman 1.53조 원",
            ),
            metric(
                "ds_revenue",
                "DS 부문 매출",
                "130.1조 원",
                "FY2025",
                "VERIFIED",
                ["S_SMSN_BR_FY25"],
                value_native=130128,
                note="내부거래 포함 부문 매출",
            ),
            metric(
                "ds_operating_income",
                "DS 부문 영업이익",
                "24.9조 원",
                "FY2025",
                "VERIFIED",
                ["S_SMSN_BR_FY25"],
                value_native=24858,
            ),
            metric(
                "capex_facility",
                "시설투자",
                "52.7조 원",
                "FY2025",
                "VERIFIED",
                ["S_SMSN_BR_FY25"],
                value_native=52700,
                note="DS·SDC 등 첨단공정·인프라 중심",
            ),
            metric(
                "cash",
                "현금및현금성자산",
                "57.86조 원",
                "2025-12-31",
                "VERIFIED",
                ["S_SMSN_BR_FY25"],
                value_native=57856,
                note="연결 재무상태표",
            ),
            metric(
                "total_debt",
                "차입금(단·장기+사채)",
                "24.06조 원",
                "2025-12-31",
                "VERIFIED",
                ["S_SMSN_BR_FY25"],
                value_native=24062,
                note="단기차입 17.575 + 장기차입 6.480 + 사채 0.007조 원",
            ),
            metric(
                "ppe_acquisitions_cfs",
                "유형자산 취득(CFS)",
                "47.5조 원",
                "FY2025",
                "VERIFIED",
                ["S_SMSN_BR_FY25"],
                value_native=47522,
                note="현금흐름표 유형자산의 취득",
            ),
            metric(
                "top5_customer_share",
                "5대 매출처 매출 비중",
                "약 15%",
                "FY2025",
                "VERIFIED",
                ["S_SMSN_BR_FY25", "S_SMSN_IR_FY25_EN"],
                note="Alphabet, Apple, Deutsche Telekom, Hong Kong Techtronics, Supreme Electronics",
            ),
            metric(
                "tesla_foundry_backlog",
                "Tesla Foundry 수주총액",
                "USD 16.54B",
                "2025-07 ~ 2033-12",
                "VERIFIED",
                ["S_SMSN_BR_FY25"],
                currency="USD",
                note="사업보고서 수주상황; 수요에 따라 변동 가능",
            ),
            metric(
                "rd_spend",
                "연구개발비 / 매출",
                "11.3%",
                "FY2025",
                "VERIFIED",
                ["S_SMSN_BR_FY25"],
            ),
        ],
        "financing_notes": [
            "원화(KRW) 보고. USD 환산 미적용.",
            "이자율 위험: 예금·변동금리 차입 중심이나 내부자금 공유로 외부차입 최소화(사업보고서 재무위험관리).",
            "신용등급: Moody's Aa2, S&P AA- (사업보고서).",
        ],
        "risk_factors": [
            "메모리·파운드리 사이클",
            "고객 집중(5대 ~15%)",
            "EUV·선단 CAPEX",
            "환율(USD/EUR)",
            "지정학·수출규제",
        ],
        "missing": [
            "5대 매출처 개별 매출액",
            "NVIDIA HBM 계약 단가·물량",
            "ASML EUV 개별 계약 금액(삼성 측 미공시)",
        ],
        "source_ids": [
            "S_SMSN_BR_FY25",
            "S_SMSN_IR_FY25_EN",
            "S_SMSN_FY25",
            "S_SMSN_SOI_FY25",
            "S_NVDA_10K_FY26_MFG",
            "S_NVDA_SMSN_AIF",
        ],
    }

    bucket["sk_hynix"] = {
        "as_of": "2025-12-31",
        "period_label": "FY2025 (K-IFRS consolidated)",
        "currency": "KRW",
        "reporting_currency": "KRW",
        "listing_currency": "KRW",
        "unit": "billion KRW",
        "overview": (
            "SK하이닉스(000660). DRAM·NAND·HBM. FY2025 매출 97.15조·영업이익 47.21조(영업이익률 49%). "
            "NVIDIA 10-K 메모리 공급사 + 2026 다년 기술 파트너십. ASML EUV ~11.95조 취득 공시. "
            "한미반도체 TC본더·주성엔지니어링 공정장비 구매(DART)."
        ),
        "metrics": [
            metric(
                "revenue",
                "매출액",
                "97.15조 원",
                "FY2025",
                "VERIFIED",
                ["S_SKH_FY25", "S_SKH_CFS_FY25"],
                value_native=971467,
                note="KRW 97,146.7 billion",
            ),
            metric(
                "operating_income",
                "영업이익",
                "47.21조 원",
                "FY2025",
                "VERIFIED",
                ["S_SKH_FY25", "S_SKH_CFS_FY25"],
                value_native=472063,
            ),
            metric(
                "operating_margin",
                "영업이익률",
                "49%",
                "FY2025",
                "VERIFIED",
                ["S_SKH_FY25"],
            ),
            metric(
                "net_income",
                "당기순이익",
                "42.95조 원",
                "FY2025",
                "VERIFIED",
                ["S_SKH_FY25", "S_SKH_CFS_FY25"],
                value_native=429479,
            ),
            metric(
                "cash",
                "현금및현금성자산",
                "14.92조 원",
                "2025-12-31",
                "VERIFIED",
                ["S_SKH_CFS_FY25"],
                value_native=14924,
                note="KRW 14,923,766 million",
            ),
            metric(
                "total_debt",
                "차입금 합계",
                "22.25조 원",
                "2025-12-31",
                "VERIFIED",
                ["S_SKH_CFS_FY25"],
                value_native=22248,
                note="유동+비유동 borrowings KRW 22,247,905 million",
            ),
            metric(
                "capex_ppe",
                "유형자산 취득(CFS)",
                "27.52조 원",
                "FY2025",
                "VERIFIED",
                ["S_SKH_CFS_FY25"],
                value_native=27519,
                note="Acquisitions of PPE KRW 27,518,924 million",
            ),
            metric(
                "asml_euv_commitment",
                "ASML EUV 취득 약정",
                "11.95조 원",
                "~2027-12",
                "VERIFIED",
                ["S_SKH_ASML_EUV"],
                value_native=11950,
                note="2026.03.24 공시; 설치·개조 포함",
            ),
            metric(
                "customer_a",
                "단일 고객 A (>10%)",
                "23.26조 원 (상호 미공시)",
                "FY2025",
                "VERIFIED",
                ["S_SKH_FY25"],
                note="사업보고서 고객 집중 공시; NVIDIA로 특정하지 않음",
            ),
            metric(
                "debt_equity_ratio",
                "부채비율",
                "45.95%",
                "2025-12-31",
                "VERIFIED",
                ["S_SKH_CFS_FY25"],
                note="Total liabilities / equity",
            ),
        ],
        "financing_notes": [
            "원화(KRW) 보고. USD 환산 미적용.",
            "주요 차입 계약상 부채비율·LTV 준수 조항; 2025.12.31 기준 준수(CFS 주석).",
            "순차입비율은 2025말 현금성자산 확대로 음수(미공시).",
        ],
        "risk_factors": [
            "HBM CAPEX·수율",
            "고객 집중(Customer A)",
            "EUV 장비 납기·환율",
            "후공정(TC 본더) 공급망",
            "메모리 가격 사이클",
        ],
        "missing": [
            "Customer A 상호(공시상 미기재)",
            "NVIDIA HBM 고정 물량·단가",
            "TSMC 베이스다이 계약 금액(양자 공시 없음)",
        ],
        "source_ids": [
            "S_SKH_FY25",
            "S_SKH_CFS_FY25",
            "S_SKH_ASML_EUV",
            "S_NVDA_10K_FY26_MFG",
            "S_SKH_NVDA_2026",
            "S_HANMI_DART_SKH_2025",
            "S_JUSUNG_DART_SKH",
        ],
    }

    # Light dossiers for new entities
    bucket["qualcomm"] = {
        "as_of": "2025-12-31",
        "period_label": "Counterparty dossier (Samsung BR)",
        "currency": "USD",
        "reporting_currency": "USD",
        "listing_currency": "USD",
        "unit": "USD",
        "overview": "삼성전자 DX 부문 모바일AP 주요 매입처로 사업보고서에 명시. Contagion Map에서는 Samsung 공급망 허브의 1차 연결로 수록.",
        "metrics": [
            metric(
                "role_at_samsung",
                "Samsung DX 원재료 역할",
                "모바일AP 주요 매입처",
                "FY2025",
                "VERIFIED",
                ["S_SMSN_BR_FY25"],
                currency="USD",
                note="품목 합계(Qualcomm+MediaTek) KRW 13.8272조",
            )
        ],
        "financing_notes": ["Samsung 사업보고서 기준 역할 확인. Qualcomm 자사 10-K 재무는 후속 보강 대상."],
        "risk_factors": ["스마트폰 사이클", "삼성 조달 비중"],
        "missing": ["Qualcomm FY2025 상세 재무 메트릭"],
        "source_ids": ["S_SMSN_BR_FY25"],
    }
    bucket["tesla"] = {
        "as_of": "2025-12-31",
        "period_label": "Counterparty dossier (Samsung BR backlog)",
        "currency": "USD",
        "reporting_currency": "USD",
        "listing_currency": "USD",
        "unit": "USD million",
        "overview": "삼성전자 DS Foundry 수주 공시의 발주처. 위탁생산 계약 총액 USD 16,544M (2025.07–2033.12).",
        "metrics": [
            metric(
                "samsung_foundry_backlog",
                "Samsung Foundry 수주총액",
                "USD 16,544M",
                "2025-07 ~ 2033-12",
                "VERIFIED",
                ["S_SMSN_BR_FY25"],
                currency="USD",
            )
        ],
        "financing_notes": ["금액은 삼성 사업보고서 수주총액이며 Tesla 측 대응 공시와 대조 필요."],
        "risk_factors": ["자동차 반도체 수요", "장기 계약 변동 조항"],
        "missing": ["Tesla 10-K상 Samsung 명시 여부 교차검증"],
        "source_ids": ["S_SMSN_BR_FY25"],
    }
    bucket["jusung_eng"] = {
        "as_of": "2025-12-31",
        "period_label": "FY2025 (K-IFRS) — equipment supplier dossier",
        "currency": "KRW",
        "reporting_currency": "KRW",
        "listing_currency": "KRW",
        "unit": "billion KRW",
        "overview": "주성엔지니어링(036930). SK하이닉스 반도체 제조장비 공급(DART·사업보고서). FY2025 연결 매출 약 3,107억 원.",
        "metrics": [
            metric(
                "revenue",
                "매출액",
                "3,107억 원",
                "FY2025",
                "VERIFIED",
                ["S_JUSUNG_DART_SKH"],
                value_native=311,
                note="사업보고서 개요(약)",
            ),
            metric(
                "skh_contract_202407",
                "SK하이닉스 공급계약(예)",
                "194억 원",
                "2024-07",
                "VERIFIED",
                ["S_JUSUNG_DART_SKH"],
                value_native=19.4,
            ),
        ],
        "financing_notes": ["원화 보고. SK하이닉스 투자 사이클에 매출 민감."],
        "risk_factors": ["메모리 CAPEX 사이클", "고객 집중"],
        "missing": ["상세 차입·현금 주석"],
        "source_ids": ["S_JUSUNG_DART_SKH"],
    }


def main() -> None:
    ent = load("entities.json")
    relj = load("relationships.json")
    src = load("sources.json")
    prof = load("profiles.json")

    n_src = upsert_sources(src)
    n_ent = upsert_entities(ent)
    n_rel = upsert_rels(relj)
    update_profiles(prof)

    save("sources.json", src)
    save("entities.json", ent)
    save("relationships.json", relj)
    save("profiles.json", prof)

    # Summary
    ids = {e["id"] for e in ent["entities"]}
    edges = relj["relationships"]
    def deg(oid: str) -> int:
        return sum(1 for r in edges if r["source"] == oid or r["target"] == oid)

    print(f"sources_added={n_src} entities_added={n_ent} relationships_added={n_rel}")
    print(f"totals: entities={len(ent['entities'])} relationships={len(edges)}")
    for oid in ("samsung", "sk_hynix", "qualcomm", "tesla", "jusung_eng", "asml", "hanmi_semi"):
        print(f"  degree[{oid}]={deg(oid)}")
    missing = [r for r in edges if r["source"] not in ids or r["target"] not in ids]
    print(f"integrity_missing_endpoints={len(missing)}")


if __name__ == "__main__":
    main()
