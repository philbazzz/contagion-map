"""
Add verified Arista/Vertiv relationships, Korean listed entities, and currency-aware profiles.
Does not invent unnamed hyperscaler counterparties or fabricate contract USD amounts.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "backend" / "data"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save(name: str, obj: dict) -> None:
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def upsert_entity(ents: list[dict], row: dict) -> str:
    for i, e in enumerate(ents):
        if e["id"] == row["id"]:
            ents[i] = {**e, **row}
            return "updated"
    ents.append(row)
    return "added"


def upsert_rel(rels: list[dict], row: dict) -> str:
    for i, r in enumerate(rels):
        if r["id"] == row["id"]:
            rels[i] = {**r, **row}
            return "updated"
    rels.append(row)
    return "added"


def upsert_source(sources: list[dict], row: dict) -> str:
    for i, s in enumerate(sources):
        if s["id"] == row["id"]:
            sources[i] = {**s, **row}
            return "updated"
    sources.append(row)
    return "added"


NEW_SOURCES = [
    {
        "id": "S_ANET_10K_FY25",
        "title": "Arista Networks Form 10-K (year ended Dec 31, 2025)",
        "publisher": "SEC EDGAR",
        "date": "2026-02-17",
        "url": "https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm",
        "used_for": "Arista FY2025 revenue; two customers >10% (26% / 16%)",
        "kind": "10-K",
    },
    {
        "id": "S_ANET_10K_FY24",
        "title": "Arista Networks Form 10-K (year ended Dec 31, 2024)",
        "publisher": "SEC EDGAR",
        "date": "2025-02",
        "url": "https://www.sec.gov/Archives/edgar/data/1596532/000159653225000028/anet-20241231.htm",
        "used_for": "Named Microsoft and Meta as >10% Cloud/AI Titan customers",
        "kind": "10-K",
    },
    {
        "id": "S_ANET_FY25_PR",
        "title": "Arista Networks Reports Fourth Quarter and Year End 2025 Financial Results",
        "publisher": "Arista IR",
        "date": "2026-02",
        "url": "https://investors.arista.com/Communications/Press-Releases-and-Events/Press-Release-Detail/2026/Arista-Networks-Inc--Reports-Fourth-Quarter-and-Year-End-2025-Financial-Results/default.aspx",
        "used_for": "Arista FY2025 revenue $9.006B, operating income $3.856B, cash",
        "kind": "ir",
    },
    {
        "id": "S_VRT_10K_FY25",
        "title": "Vertiv Holdings Co Form 10-K (year ended Dec 31, 2025)",
        "publisher": "SEC EDGAR",
        "date": "2026-02-13",
        "url": "https://www.sec.gov/Archives/edgar/data/1674101/000167410126000008/vrt-20251231.htm",
        "used_for": "Vertiv FY2025 net sales $10.230B",
        "kind": "10-K",
    },
    {
        "id": "S_VRT_FY25_PR",
        "title": "Vertiv Reports Strong Fourth Quarter / FY2025 Results",
        "publisher": "Vertiv IR",
        "date": "2026-02",
        "url": "https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-Fourth-Quarter-with-Organic-Orders-Growth-of-252-and-Diluted-EPS-Growth-of-200-Adjusted-Diluted-EPS-37/default.aspx",
        "used_for": "Vertiv FY2025 operating profit $1.830B, interest expense",
        "kind": "ir",
    },
    {
        "id": "S_VRT_NVDA_800V",
        "title": "Vertiv collaborates with NVIDIA to advance 800 VDC platform designs",
        "publisher": "Vertiv corporate news",
        "date": "2025-10-13",
        "url": "https://www.vertiv.com/en-us/about/news-and-events/corporate-news/from-vision-to-readiness-vertiv-collaborates-with-nvidia-to-advance-800-vdc-platform-designs-to-power-the-next-generation-of-ai-factories/",
        "used_for": "Vertiv–NVIDIA 800 VDC strategic collaboration (not a disclosed supply-contract USD amount)",
        "kind": "press",
    },
    {
        "id": "S_NVDA_800V_PARTNERS",
        "title": "NVIDIA 800 VDC Architecture Will Power the Next Generation of AI Factories",
        "publisher": "NVIDIA Technical Blog",
        "date": "2025",
        "url": "https://developer.nvidia.com/blog/nvidia-800-v-hvdc-architecture-will-power-the-next-generation-of-ai-factories/",
        "used_for": "NVIDIA lists Vertiv, Eaton, Schneider among data-center power system collaborators",
        "kind": "press",
    },
    {
        "id": "S_HANMI_DART_SKH",
        "title": "한미반도체 단일판매ㆍ공급계약체결 (SK하이닉스 HBM TC 본더)",
        "publisher": "DART / 연합뉴스 요약",
        "date": "2024-03-22",
        "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20240322800090",
        "used_for": "Hanmi Semiconductor → SK hynix HBM equipment supply (DART)",
        "kind": "dart",
    },
    {
        "id": "S_HANMI_DART_MICRON",
        "title": "한미반도체–마이크론 HBM 장비 공급 공시 보도",
        "publisher": "대한경제 / DART 기반",
        "date": "2024-04-11",
        "url": "https://www.dnews.co.kr/m_home/view.jsp?idxno=202404111503480060946",
        "used_for": "Hanmi → Micron Dual TC Bonder Tiger KRW 22.6B (DART-backed report)",
        "kind": "news_dart",
    },
    {
        "id": "S_SKT_NVDA_2026",
        "title": "SK Telecom and NVIDIA Build AI Infrastructure to Power Korea’s AI Innovation",
        "publisher": "NVIDIA Newsroom",
        "date": "2026-06-07",
        "url": "https://nvidianews.nvidia.com/news/sk-telecom-and-nvidia-build-ai-infrastructure-to-power-koreas-ai-innovation",
        "used_for": "SKT NVIDIA DSX AI Cloud / Cloud Partner (strategic, not disclosed GPU purchase USD)",
        "kind": "press",
    },
    {
        "id": "S_SKT_BLACKWELL",
        "title": "SK Telecom Launches Sovereign AI Infrastructure, Powered by NVIDIA",
        "publisher": "SK telecom newsroom",
        "date": "2025-08-05",
        "url": "https://news.sktelecom.com/en/2056",
        "used_for": "SKT >1,000 NVIDIA Blackwell GPU cluster / GPUaaS; Supermicro server procurement",
        "kind": "press",
    },
    {
        "id": "S_LSE_BIGTECH_DC",
        "title": "LS ELECTRIC 단일판매ㆍ공급계약 (Big Tech Data Center 전력설비)",
        "publisher": "DART / 공시 전문",
        "date": "2026-08",
        "url": "https://dart.fss.or.kr/",
        "used_for": "LS ELECTRIC → US Big Tech DC power equipment via LS ELECTRIC AMERICA; counterparty unnamed in disclosure",
        "kind": "dart",
    },
    {
        "id": "S_NVDA_KR_SUMMIT",
        "title": "At AI Summit, South Korea Outlines Its AI Future With NVIDIA and Partners",
        "publisher": "NVIDIA Blog",
        "date": "2026",
        "url": "https://blogs.nvidia.com/blog/ai-summit-korea-partners-and-nvidia/",
        "used_for": "NAVER NVIDIA DSX AI factory expansion announcement (GPU/MW plans)",
        "kind": "press",
    },
]

NEW_ENTITIES = [
    {
        "id": "hanmi_semi",
        "name": "Hanmi Semiconductor",
        "name_ko": "한미반도체",
        "group": "semiconductor",
        "sector": "반도체 장비 · HBM TC 본더",
        "entity_type": "company",
        "role": "HBM 제조용 TC 본더 장비",
        "description": "HBM 적층용 Dual TC Bonder 장비. DART 공시상 SK하이닉스·마이크론 등 메모리 고객에 공급.",
        "listed": True,
        "ticker": "042700",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 5,
        "source_status": "VERIFIED",
        "source_ids": ["S_HANMI_DART_SKH"],
        "key_drivers": ["HBM CAPEX", "TC 본더 수주"],
    },
    {
        "id": "isu_petasys",
        "name": "Isu Petasys",
        "name_ko": "이수페타시스",
        "group": "semiconductor",
        "sector": "고다층 PCB · 서버/네트워크",
        "entity_type": "company",
        "role": "고다층 PCB (AI 서버·네트워크 보드)",
        "description": "고다층 PCB 제조. AI 서버·네트워크 보드 수요와 연동되나, NVIDIA 등 특정 하이퍼스케일과의 단일계약은 본 데이터셋에 미확인.",
        "listed": True,
        "ticker": "007660",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 4,
        "source_status": "VERIFIED",
        "source_ids": [],
        "key_drivers": ["AI 서버 PCB 수요"],
    },
    {
        "id": "ls_electric",
        "name": "LS ELECTRIC",
        "name_ko": "LS일렉트릭",
        "group": "datacenter",
        "sector": "전력기기 · 배전",
        "entity_type": "company",
        "role": "AI 데이터센터 전력·배전 설비",
        "description": "DART 공시: 자회사 LS ELECTRIC AMERICA를 통해 미국 Big Tech 데이터센터 전력설비 공급 (계약상대 상호는 미공시).",
        "listed": True,
        "ticker": "010120",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 5,
        "source_status": "VERIFIED",
        "source_ids": ["S_LSE_BIGTECH_DC"],
        "key_drivers": ["북미 AI DC 전력 수주", "배전 시스템"],
    },
    {
        "id": "hd_hyundai_electric",
        "name": "HD Hyundai Electric",
        "name_ko": "HD현대일렉트릭",
        "group": "datacenter",
        "sector": "변압기 · 전력기기",
        "entity_type": "company",
        "role": "전력기기·변압기 (데이터센터 전력망)",
        "description": "변압기·전력기기. AI/데이터센터 전력 인프라 수요 수혜 후보이나, 본 맵에는 특정 하이퍼스케일 계약 엣지를 부여하지 않음(미확인).",
        "listed": True,
        "ticker": "267260",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 4,
        "source_status": "VERIFIED",
        "source_ids": [],
        "key_drivers": ["전력기기 수주"],
    },
    {
        "id": "hyosung_heavy",
        "name": "Hyosung Heavy Industries",
        "name_ko": "효성중공업",
        "group": "datacenter",
        "sector": "중전기 · 변압기",
        "entity_type": "company",
        "role": "초고압 변압기·중전기",
        "description": "초고압 변압기 등. AI 데이터센터 전력 수요와 산업적으로 연관되나 특정 상대방 계약은 미확인으로 엣지 미생성.",
        "listed": True,
        "ticker": "298040",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 4,
        "source_status": "VERIFIED",
        "source_ids": [],
        "key_drivers": ["변압기 수주"],
    },
    {
        "id": "doosan_enerbility",
        "name": "Doosan Enerbility",
        "name_ko": "두산에너빌리티",
        "group": "datacenter",
        "sector": "발전 · 원전 · 에너지",
        "entity_type": "company",
        "role": "발전·원전 기자재 (전력 공급망)",
        "description": "발전·원전 기자재. AI 데이터센터 전력 수요와 간접 연관 가능하나 특정 데이터센터 계약 엣지는 미확인.",
        "listed": True,
        "ticker": "034020",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 4,
        "source_status": "VERIFIED",
        "source_ids": [],
        "key_drivers": ["원전·발전 CAPEX"],
    },
    {
        "id": "sk_telecom",
        "name": "SK Telecom",
        "name_ko": "SK텔레콤",
        "group": "customer",
        "sector": "통신 · AI 클라우드",
        "entity_type": "company",
        "role": "국내 AI Cloud / GPUaaS",
        "description": "NVIDIA Blackwell 기반 소버린 AI 인프라·GPUaaS. NVIDIA DSX AI Cloud 구축 계획(공식 보도).",
        "listed": True,
        "ticker": "017670",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": "ADR: SKM (NYSE) — 본 맵 시세는 KOSPI 본주 기준",
        "display_size": 6,
        "source_status": "VERIFIED",
        "source_ids": ["S_SKT_NVDA_2026", "S_SKT_BLACKWELL"],
        "key_drivers": ["GPUaaS", "NVIDIA 인프라"],
    },
    {
        "id": "naver",
        "name": "NAVER",
        "name_ko": "네이버",
        "group": "customer",
        "sector": "인터넷 · 클라우드 · AI",
        "entity_type": "company",
        "role": "국내 AI 데이터센터 · 클라우드",
        "description": "각 세종 등 AI 데이터센터. NVIDIA 보도에서 DSX AI factory 확장(GPU/전력 규모)이 언급됨. 계약 USD는 미공시.",
        "listed": True,
        "ticker": "035420",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 6,
        "source_status": "VERIFIED",
        "source_ids": ["S_NVDA_KR_SUMMIT"],
        "key_drivers": ["AI 데이터센터", "GPU 클러스터"],
    },
    {
        "id": "samsung_sds",
        "name": "Samsung SDS",
        "name_ko": "삼성SDS",
        "group": "customer",
        "sector": "IT 서비스 · 클라우드",
        "entity_type": "company",
        "role": "기업 클라우드 · GPUaaS",
        "description": "삼성 클라우드 플랫폼 GPUaaS 등. 국가 GPU 사업 운영사로 보도됨. NVIDIA와의 특정 공급계약액은 본 데이터셋에 미수록.",
        "listed": True,
        "ticker": "018260",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 5,
        "source_status": "INFERRED",
        "source_ids": [],
        "key_drivers": ["기업 AI 클라우드"],
    },
    {
        "id": "kt",
        "name": "KT",
        "name_ko": "KT",
        "group": "customer",
        "sector": "통신 · 클라우드",
        "entity_type": "company",
        "role": "국내 통신·클라우드 / GPUaaS",
        "description": "K GPUaaS 등 NVIDIA GPU 기반 서비스 보도. 특정 구매계약액·상대 공시는 본 맵에 미확인으로 엣지 제한.",
        "listed": True,
        "ticker": "030200",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 4,
        "source_status": "INFERRED",
        "source_ids": [],
        "key_drivers": ["GPUaaS"],
    },
    {
        "id": "lg_electronics",
        "name": "LG Electronics",
        "name_ko": "LG전자",
        "group": "server",
        "sector": "가전 · B2B · 전장",
        "entity_type": "company",
        "role": "B2B·전장 (AI 인프라 간접)",
        "description": "AI 인프라 핵심 공급망 외곽. NVIDIA 등과의 직접 인프라 계약은 본 데이터셋에서 확인하지 않음.",
        "listed": True,
        "ticker": "066570",
        "exchange": "KOSPI",
        "quote_currency": "KRW",
        "listing_note": None,
        "display_size": 4,
        "source_status": "VERIFIED",
        "source_ids": [],
        "key_drivers": ["B2B"],
    },
]

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
    amount_note: str = "",
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
        "amount_usd_m": None,
        "amount_note": amount_note or "금액 미공시 / 해당 없음",
        "roles": [],
        "explanation": explanation,
    }


NEW_RELS = [
    rel(
        "c_microsoft_arista", "microsoft", "arista", "CUSTOMER", "customer",
        "Microsoft · Arista significant customer", "VERIFIED",
        ["S_ANET_10K_FY24", "S_ANET_10K_FY25"],
        "Arista FY2024 10-K names Microsoft as a Cloud/AI Titan end customer >10% of revenue "
        "(20% in 2024). FY2025 10-K reports two customers at 26% and 16% without repeating names; "
        "continuity with FY2024 naming supports Microsoft as the larger share. Not a disclosed unit switch PO.",
    ),
    rel(
        "c_meta_arista", "meta", "arista", "CUSTOMER", "customer",
        "Meta · Arista significant customer", "VERIFIED",
        ["S_ANET_10K_FY24", "S_ANET_10K_FY25"],
        "Arista FY2024 10-K names Meta Platforms as >10% customer (15% in 2024). "
        "FY2025 continues two >10% customers (26%/16%). Customer relationship, not a named dollar PO.",
    ),
    rel(
        "sp_vertiv_nvidia", "vertiv", "nvidia", "STRATEGIC_PARTNERSHIP", "supply_chain",
        "Vertiv–NVIDIA 800 VDC collaboration", "VERIFIED",
        ["S_VRT_NVDA_800V", "S_NVDA_800V_PARTNERS"],
        "Official Vertiv and NVIDIA announcements: collaboration on 800 VDC platform designs for AI factories. "
        "Strategic/technology partnership — NOT a confirmed supply-contract dollar amount.",
        "기술 협력 · 공급계약액 미공시",
    ),
    rel(
        "sp_eaton_nvidia", "eaton", "nvidia", "STRATEGIC_PARTNERSHIP", "supply_chain",
        "Eaton listed in NVIDIA 800 VDC collaborator set", "VERIFIED",
        ["S_NVDA_800V_PARTNERS"],
        "NVIDIA technical blog lists Eaton among data-center power system collaborators for 800 VDC. Not a disclosed sales contract.",
        "기술 협력 · 공급계약액 미공시",
    ),
    rel(
        "sp_schneider_nvidia", "schneider", "nvidia", "STRATEGIC_PARTNERSHIP", "supply_chain",
        "Schneider listed in NVIDIA 800 VDC collaborator set", "VERIFIED",
        ["S_NVDA_800V_PARTNERS"],
        "NVIDIA technical blog lists Schneider Electric among 800 VDC power collaborators. Not a disclosed sales contract.",
        "기술 협력 · 공급계약액 미공시",
    ),
    rel(
        "s_hanmi_skh", "sk_hynix", "hanmi_semi", "SUPPLIER", "supply_chain",
        "Hanmi → SK hynix HBM TC bonders", "VERIFIED",
        ["S_HANMI_DART_SKH"],
        "DART 단일판매·공급계약: 한미반도체 → SK하이닉스 HBM용 Dual TC Bonder. 금액은 KRW 공시. USD 환산 미적용.",
        "KRW 공시 (예: 214.83억 원 건)",
    ),
    rel(
        "s_hanmi_micron", "micron", "hanmi_semi", "SUPPLIER", "supply_chain",
        "Hanmi → Micron HBM TC bonders", "VERIFIED",
        ["S_HANMI_DART_MICRON"],
        "DART 기반 보도: 한미반도체 → 마이크론 Dual TC Bonder Tiger 약 225.9억 원. 납품 지역 대만.",
        "KRW 약 225.9억 원",
    ),
    rel(
        "sp_skt_nvidia", "sk_telecom", "nvidia", "STRATEGIC_PARTNERSHIP", "customer",
        "SKT–NVIDIA AI Cloud / DSX", "VERIFIED",
        ["S_SKT_NVDA_2026", "S_SKT_BLACKWELL"],
        "NVIDIA/SKT official releases: Blackwell GPUaaS cluster and planned NVIDIA DSX AI Cloud in Korea; "
        "SKT to become NVIDIA Cloud Partner. GPU purchase USD not disclosed.",
        "전략 협력 · GPU 구매액 미공시",
    ),
    rel(
        "s_skt_smci", "sk_telecom", "smci", "SUPPLIER", "supply_chain",
        "SKT AI servers via Supermicro (press)", "VERIFIED",
        ["S_SKT_BLACKWELL"],
        "SKT newsroom: sovereign AI infrastructure prep included Supermicro for AI server procurement. Amount not disclosed.",
    ),
    rel(
        "sp_naver_nvidia", "naver", "nvidia", "STRATEGIC_PARTNERSHIP", "customer",
        "NAVER–NVIDIA AI factory (DSX) plans", "VERIFIED",
        ["S_NVDA_KR_SUMMIT"],
        "NVIDIA blog: NAVER AI factory at GAK Sejong to expand on NVIDIA DSX / Vera Rubin (MW and GPU plans cited). "
        "Not treated as a disclosed purchase-order dollar amount.",
        "전략 협력 · 구매액 미공시",
    ),
]

PROFILE_PATCHES = {
    "arista": {
        "as_of": "2025-12-31",
        "period_label": "FY2025 (year ended Dec 31, 2025)",
        "currency": "USD",
        "reporting_currency": "USD",
        "listing_currency": "USD",
        "unit": "million",
        "overview": (
            "Cloud and AI Ethernet networking. Significant customer concentration in Cloud/AI Titans "
            "(Microsoft and Meta named in FY2024 10-K; FY2025 two customers 26%/16%)."
        ),
        "metrics": [
            {"id": "revenue", "label": "Revenue", "value_usd_m": 9006, "currency": "USD", "display": "$9.01B", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_ANET_FY25_PR", "S_ANET_10K_FY25"]},
            {"id": "operating_income", "label": "Operating income", "value_usd_m": 3856, "currency": "USD", "display": "$3.86B", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_ANET_FY25_PR"]},
            {"id": "cash", "label": "Cash and cash equivalents", "value_usd_m": 1964, "currency": "USD", "display": "$1.96B", "period": "2025-12-31", "status": "VERIFIED", "source_ids": ["S_ANET_FY25_PR"]},
            {"id": "marketable_securities", "label": "Marketable securities", "value_usd_m": 8779, "currency": "USD", "display": "$8.78B", "period": "2025-12-31", "status": "VERIFIED", "source_ids": ["S_ANET_FY25_PR"]},
            {"id": "total_debt", "label": "Interest-bearing debt", "value_usd_m": 0, "currency": "USD", "display": "None material (no notes payable on FY25 BS)", "period": "2025-12-31", "status": "VERIFIED", "source_ids": ["S_ANET_FY25_PR"], "note": "Balance sheet shows no traditional long-term debt line"},
            {"id": "msft_share", "label": "Microsoft revenue share (named FY24)", "value_usd_m": None, "currency": "USD", "display": "20% of FY2024 revenue", "period": "FY2024", "status": "VERIFIED", "source_ids": ["S_ANET_10K_FY24"]},
            {"id": "meta_share", "label": "Meta revenue share (named FY24)", "value_usd_m": None, "currency": "USD", "display": "15% of FY2024 revenue", "period": "FY2024", "status": "VERIFIED", "source_ids": ["S_ANET_10K_FY24"]},
            {"id": "top2_fy25", "label": "Top-2 customers (unnamed FY25)", "value_usd_m": None, "currency": "USD", "display": "26% + 16% of FY2025 revenue", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_ANET_10K_FY25"]},
            {"id": "fcf", "label": "Free cash flow", "value_usd_m": None, "display": "Not disclosed as primary KPI here", "period": "FY2025", "status": "UNKNOWN", "source_ids": ["S_ANET_FY25_PR"]},
        ],
        "financing_notes": [
            "Investment-grade cash-rich balance sheet; rate-shock path is mainly customer CapEx timing, not floating debt.",
        ],
        "risk_factors": [
            "Customer concentration (Microsoft / Meta)",
            "Hyperscaler CapEx cycles",
            "AI networking competition",
        ],
        "missing": ["Named USD purchase orders by customer"],
        "source_ids": ["S_ANET_10K_FY25", "S_ANET_10K_FY24", "S_ANET_FY25_PR"],
    },
    "vertiv": {
        "as_of": "2025-12-31",
        "period_label": "FY2025 (year ended Dec 31, 2025)",
        "currency": "USD",
        "reporting_currency": "USD",
        "listing_currency": "USD",
        "unit": "million",
        "overview": (
            "Critical digital infrastructure (power, cooling, services) for data centers. "
            "Collaborates with NVIDIA on 800 VDC AI factory power architectures (strategic, not a disclosed supply PO)."
        ),
        "metrics": [
            {"id": "revenue", "label": "Net sales", "value_usd_m": 10230, "currency": "USD", "display": "$10.23B", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_VRT_10K_FY25", "S_VRT_FY25_PR"]},
            {"id": "operating_income", "label": "Operating profit", "value_usd_m": 1830, "currency": "USD", "display": "$1.83B", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_VRT_FY25_PR"]},
            {"id": "interest_expense", "label": "Interest expense, net", "value_usd_m": 86, "currency": "USD", "display": "$86M", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_VRT_FY25_PR"]},
            {"id": "net_income", "label": "Net income", "value_usd_m": 1333, "currency": "USD", "display": "$1.33B", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_VRT_FY25_PR"]},
            {"id": "total_debt", "label": "Total debt", "value_usd_m": None, "display": "See 10-K debt note", "period": "FY2025", "status": "UNKNOWN", "source_ids": ["S_VRT_10K_FY25"]},
            {"id": "cash", "label": "Cash and cash equivalents", "value_usd_m": None, "display": "See 10-K balance sheet", "period": "FY2025", "status": "UNKNOWN", "source_ids": ["S_VRT_10K_FY25"]},
            {"id": "fcf", "label": "Free cash flow", "value_usd_m": None, "display": "Not restated here", "period": "FY2025", "status": "UNKNOWN", "source_ids": ["S_VRT_FY25_PR"]},
        ],
        "financing_notes": [
            "Has interest-bearing debt (interest expense disclosed). Instrument schedule not fully mirrored.",
            "800 VDC NVIDIA collaboration is technology/strategic — do not treat as quantified supply revenue.",
        ],
        "risk_factors": [
            "Data-center CapEx cycles",
            "Interest expense / refinancing",
            "Supply chain for power/cooling components",
        ],
        "missing": ["Full debt maturity table in this dataset"],
        "source_ids": ["S_VRT_10K_FY25", "S_VRT_FY25_PR", "S_VRT_NVDA_800V"],
    },
    "sk_hynix": {
        "as_of": "2025-12-31",
        "period_label": "FY2025 (K-IFRS)",
        "currency": "KRW",
        "reporting_currency": "KRW",
        "listing_currency": "KRW",
        "unit": "billion KRW",
        "overview": "HBM/DRAM 선도. NVIDIA 10-K상 메모리 공급사. 한미반도체 등으로부터 HBM TC 본더 장비 구매(DART).",
        "metrics": [
            {"id": "revenue", "label": "매출액", "value_usd_m": None, "value_native": 971467, "currency": "KRW", "display": "97.15조 원", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_SKH_FY25"], "note": "KRW 97,146.7 billion"},
            {"id": "operating_income", "label": "영업이익", "value_usd_m": None, "value_native": 472063, "currency": "KRW", "display": "47.21조 원", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_SKH_FY25"]},
            {"id": "operating_margin", "label": "영업이익률", "value_usd_m": None, "currency": "KRW", "display": "49%", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_SKH_FY25"]},
            {"id": "net_income", "label": "당기순이익", "value_usd_m": None, "currency": "KRW", "display": "42.95조 원", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_SKH_FY25"]},
            {"id": "customer_a", "label": "단일 고객 A (>10%)", "value_usd_m": None, "currency": "KRW", "display": "23.26조 원 (상호 미공시)", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_SKH_FY25"]},
            {"id": "total_debt", "label": "차입금", "value_usd_m": None, "currency": "KRW", "display": "Not disclosed in this dossier", "period": "FY2025", "status": "UNKNOWN", "source_ids": ["S_SKH_FY25"]},
            {"id": "cash", "label": "현금및현금성자산", "value_usd_m": None, "currency": "KRW", "display": "Not disclosed in this dossier", "period": "FY2025", "status": "UNKNOWN", "source_ids": ["S_SKH_FY25"]},
        ],
        "financing_notes": ["원화 재무제표 기준. USD 환산은 적용하지 않음.", "차입금 만기표는 DART 사업보고서 주석 추가 수록 필요."],
        "risk_factors": ["HBM CAPEX", "고객 집중 (Customer A)", "환율", "장비 공급망 (TC 본더 등)"],
        "missing": ["차입금 상세 만기표", "Customer A 상호"],
        "source_ids": ["S_SKH_FY25", "S_NVDA_10K_FY26", "S_HANMI_DART_SKH"],
    },
    "samsung": {
        "as_of": "2025-12-31",
        "period_label": "FY2025 consolidated",
        "currency": "KRW",
        "reporting_currency": "KRW",
        "listing_currency": "KRW",
        "unit": "billion KRW",
        "overview": "DS(반도체·파운드리·HBM) + DX. NVIDIA 10-K상 파운드리·메모리 공급사.",
        "metrics": [
            {"id": "revenue", "label": "매출액", "value_usd_m": None, "currency": "KRW", "display": "333.6조 원", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_SMSN_FY25", "S_SMSN_SOI_FY25"]},
            {"id": "operating_income", "label": "영업이익", "value_usd_m": None, "currency": "KRW", "display": "43.6조 원", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_SMSN_FY25", "S_SMSN_SOI_FY25"]},
            {"id": "ds_revenue", "label": "DS 부문 매출", "value_usd_m": None, "currency": "KRW", "display": "130.1조 원", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_SMSN_FY25"]},
            {"id": "memory_revenue", "label": "메모리 매출", "value_usd_m": None, "currency": "KRW", "display": "104.1조 원", "period": "FY2025", "status": "VERIFIED", "source_ids": ["S_SMSN_FY25"]},
            {"id": "total_debt", "label": "차입금", "value_usd_m": None, "currency": "KRW", "display": "Not disclosed in this dossier", "period": "FY2025", "status": "UNKNOWN", "source_ids": ["S_SMSN_SOI_FY25"]},
            {"id": "cash", "label": "현금및현금성자산", "value_usd_m": None, "currency": "KRW", "display": "Not disclosed in this dossier", "period": "FY2025", "status": "UNKNOWN", "source_ids": ["S_SMSN_SOI_FY25"]},
        ],
        "financing_notes": ["원화 표시. IR PDF에 USD convenience translation이 있어도 본 독세는 KRW 우선."],
        "risk_factors": ["파운드리 점유율 vs TSMC", "HBM 경쟁", "DX 사이클"],
        "missing": ["차입금 상세", "파운드리/메모리 영업이익 분리"],
        "source_ids": ["S_SMSN_FY25", "S_SMSN_SOI_FY25", "S_NVDA_10K_FY26"],
    },
    "tsmc": {
        "as_of": "2025-12-31",
        "period_label": "CY2025 consolidated (TIFRS)",
        "currency": "TWD",
        "reporting_currency": "TWD",
        "listing_currency": "USD",
        "unit": "NT$ billion / USD billion",
        "overview": (
            "Pure-play foundry. Financial statements in TWD (and USD convenience). "
            "NYSE ADR (TSM) trades in USD — do not treat TSMC as a US-domiciled reporter."
        ),
        "metrics": [
            {"id": "revenue_twd", "label": "Net revenue (TWD)", "value_usd_m": None, "currency": "TWD", "display": "NT$3,809.05B", "period": "CY2025", "status": "VERIFIED", "source_ids": ["S_TSMC_FY25", "S_TSMC_6K_FY25"]},
            {"id": "revenue_usd", "label": "Net revenue (USD convenience)", "value_usd_m": 122420, "currency": "USD", "display": "US$122.42B", "period": "CY2025", "status": "VERIFIED", "source_ids": ["S_TSMC_FY25"], "note": "Company-reported USD translation"},
            {"id": "operating_income_twd", "label": "Operating income (TWD)", "value_usd_m": None, "currency": "TWD", "display": "NT$1,936.09B", "period": "CY2025", "status": "VERIFIED", "source_ids": ["S_TSMC_FY25"]},
            {"id": "operating_margin", "label": "Operating margin", "value_usd_m": None, "currency": "TWD", "display": "50.8%", "period": "CY2025", "status": "VERIFIED", "source_ids": ["S_TSMC_FY25"]},
            {"id": "capex_usd", "label": "CAPEX (USD)", "value_usd_m": 40900, "currency": "USD", "display": "US$40.9B", "period": "CY2025", "status": "VERIFIED", "source_ids": ["S_TSMC_FY25"]},
            {"id": "capex_guide", "label": "2026 CAPEX guidance", "value_usd_m": None, "currency": "USD", "display": "US$52–56B", "period": "CY2026 guide", "status": "VERIFIED", "source_ids": ["S_TSMC_FY25"]},
            {"id": "total_debt", "label": "Total debt", "value_usd_m": None, "currency": "TWD", "display": "Not disclosed in this dossier", "period": "CY2025", "status": "UNKNOWN", "source_ids": ["S_TSMC_FY25"]},
        ],
        "financing_notes": [
            "Reporting currency: TWD. Listing: Taiwan main board + NYSE ADR (USD quotes).",
            "ASML tools are critical-path equipment (existing edge).",
        ],
        "risk_factors": ["Geopolitics / Taiwan", "Customer concentration", "Advanced packaging", "CAPEX intensity"],
        "missing": ["Named customer revenue mix", "Full TWD debt schedule in this dossier"],
        "source_ids": ["S_TSMC_FY25", "S_TSMC_6K_FY25", "S_ASML_TSMC"],
    },
}


def patch_us_reporting(profiles: dict) -> None:
    for pid in ("nvidia", "microsoft", "amazon", "oracle", "meta", "equinix", "coreweave"):
        if pid in profiles:
            profiles[pid]["reporting_currency"] = "USD"
            profiles[pid]["listing_currency"] = "USD"
            profiles[pid]["currency"] = profiles[pid].get("currency") or "USD"


def main() -> None:
    ents_doc = load("entities.json")
    rels_doc = load("relationships.json")
    src_doc = load("sources.json")
    prof_doc = load("profiles.json")

    ea = ra = sa = 0
    for s in NEW_SOURCES:
        if upsert_source(src_doc["sources"], s) == "added":
            sa += 1
    for e in NEW_ENTITIES:
        if upsert_entity(ents_doc["entities"], e) == "added":
            ea += 1
    for r in NEW_RELS:
        if upsert_rel(rels_doc["relationships"], r) == "added":
            ra += 1

    # Upgrade Samsung status if still INFERRED
    for e in ents_doc["entities"]:
        if e["id"] == "samsung" and e.get("source_status") == "INFERRED":
            e["source_status"] = "VERIFIED"
            e["source_ids"] = list(dict.fromkeys([*(e.get("source_ids") or []), "S_NVDA_10K_FY26", "S_SMSN_FY25"]))

    profiles = prof_doc.setdefault("profiles", {})
    patch_us_reporting(profiles)
    for pid, body in PROFILE_PATCHES.items():
        profiles[pid] = body

    # Light profiles for new Korean majors (KRW reporting; figures only where we have DART/IR)
    profiles["hanmi_semi"] = {
        "as_of": "2024-06",
        "period_label": "DART supply contracts 2024 (not full FY P&L mirrored)",
        "currency": "KRW",
        "reporting_currency": "KRW",
        "listing_currency": "KRW",
        "overview": "HBM TC 본더 장비. SK하이닉스·마이크론 공급 공시 확인. NVIDIA 직접 공급계약은 미확인.",
        "metrics": [
            {"id": "skh_contract_example", "label": "SK하이닉스 공급계약(예시)", "currency": "KRW", "display": "214.83억 원", "period": "2024-03-22 DART", "status": "VERIFIED", "source_ids": ["S_HANMI_DART_SKH"]},
            {"id": "micron_contract", "label": "마이크론 공급계약", "currency": "KRW", "display": "225.9억 원", "period": "2024-04-11", "status": "VERIFIED", "source_ids": ["S_HANMI_DART_MICRON"]},
            {"id": "revenue", "label": "연간 매출액", "currency": "KRW", "display": "Not disclosed in this dossier", "period": "—", "status": "UNKNOWN", "source_ids": []},
        ],
        "financing_notes": ["원화 공시 우선. 전체 손익은 사업보고서에서 추가 수록 필요."],
        "risk_factors": ["HBM CAPEX 사이클", "고객 집중"],
        "missing": ["전체 손익·차입금"],
        "source_ids": ["S_HANMI_DART_SKH", "S_HANMI_DART_MICRON"],
    }
    profiles["sk_telecom"] = {
        "as_of": "2026-06-07",
        "period_label": "Partnership announcements 2025–2026",
        "currency": "KRW",
        "reporting_currency": "KRW",
        "listing_currency": "KRW",
        "overview": "국내 통신·AI Cloud. NVIDIA Blackwell GPUaaS 및 DSX AI Cloud 계획(공식 보도).",
        "metrics": [
            {"id": "gpu_cluster", "label": "Blackwell GPU cluster", "currency": "KRW", "display": ">1,000 GPUs (press)", "period": "2025-08", "status": "VERIFIED", "source_ids": ["S_SKT_BLACKWELL"]},
            {"id": "revenue", "label": "연결 매출액", "currency": "KRW", "display": "Not disclosed in this dossier", "period": "—", "status": "UNKNOWN", "source_ids": []},
            {"id": "total_debt", "label": "차입금", "currency": "KRW", "display": "Not disclosed in this dossier", "period": "—", "status": "UNKNOWN", "source_ids": []},
        ],
        "financing_notes": ["AI 인프라 투자는 CAPEX·파트너십 중심. GPU 구매 USD 미공시."],
        "risk_factors": ["AI CapEx", "GPU 공급", "통신 규제"],
        "missing": ["최근 사업보고서 손익 수치"],
        "source_ids": ["S_SKT_NVDA_2026", "S_SKT_BLACKWELL"],
    }
    profiles["naver"] = {
        "as_of": "2026",
        "period_label": "NVIDIA Korea AI Summit commentary",
        "currency": "KRW",
        "reporting_currency": "KRW",
        "listing_currency": "KRW",
        "overview": "인터넷·클라우드. NVIDIA 보도상 각 세종 DSX AI factory 확장 계획.",
        "metrics": [
            {"id": "ai_factory", "label": "AI factory expansion (press)", "currency": "KRW", "display": "Up to ~200 MW / Vera Rubin plans (NVIDIA blog)", "period": "2026", "status": "VERIFIED", "source_ids": ["S_NVDA_KR_SUMMIT"]},
            {"id": "revenue", "label": "연결 매출액", "currency": "KRW", "display": "Not disclosed in this dossier", "period": "—", "status": "UNKNOWN", "source_ids": []},
        ],
        "financing_notes": ["원화 재무제표. GPU 계약 금액 미공시."],
        "risk_factors": ["AI CapEx", "전력", "경쟁"],
        "missing": ["사업보고서 손익"],
        "source_ids": ["S_NVDA_KR_SUMMIT"],
    }
    profiles["ls_electric"] = {
        "as_of": "2026-08",
        "period_label": "DART Big Tech DC power supply disclosure",
        "currency": "KRW",
        "reporting_currency": "KRW",
        "listing_currency": "KRW",
        "overview": "전력·배전. DART: 자회사 경유 미국 Big Tech 데이터센터 전력설비 공급(상대 상호 미공시).",
        "metrics": [
            {"id": "bigtech_contract", "label": "Big Tech DC 전력설비 계약", "currency": "KRW", "display": "약 2,309억 원 (USD 165.7M @ 1,393원)", "period": "2026-08 변경계약", "status": "VERIFIED", "source_ids": ["S_LSE_BIGTECH_DC"], "note": "상대방 상호 미공시 — 하이퍼스케일 노드에 직접 엣지 연결하지 않음"},
            {"id": "revenue", "label": "연결 매출액", "currency": "KRW", "display": "Not disclosed in this dossier", "period": "—", "status": "UNKNOWN", "source_ids": []},
        ],
        "financing_notes": ["공시 환율로 USD→KRW 환산액이 함께 기재됨. 본 독세는 KRW 표시."],
        "risk_factors": ["미공시 고객 집중", "북미 납기", "환율"],
        "missing": ["상대방 상호", "전체 손익"],
        "source_ids": ["S_LSE_BIGTECH_DC"],
    }

    save("entities.json", ents_doc)
    save("relationships.json", rels_doc)
    save("sources.json", src_doc)
    save("profiles.json", prof_doc)
    print(f"entities +{ea} (total {len(ents_doc['entities'])})")
    print(f"relationships +{ra} (total {len(rels_doc['relationships'])})")
    print(f"sources +{sa} (total {len(src_doc['sources'])})")
    print(f"profiles {len(profiles)}")


if __name__ == "__main__":
    main()
