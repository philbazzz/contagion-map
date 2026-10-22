"""Merge verified multi-center ecosystem expansion into backend/data/*.json.

Only adds entities/relationships/sources/profiles with cited public evidence.
Does not invent contracts or amounts. Run from repo root:

    python scripts/apply_ecosystem_expansion.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "backend" / "data"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save(name: str, obj) -> None:
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


NEW_SOURCES = [
    {
        "id": "S_NVDA_10K_FY26",
        "title": "NVIDIA Corporation Form 10-K (FY2026 ended Jan 25, 2026)",
        "publisher": "SEC EDGAR",
        "date": "2026-02",
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm",
        "used_for": "Fabless foundry partners TSMC·Samsung; memory SK hynix·Micron·Samsung; CM Hon Hai·Wistron; CSP/OEM customers",
        "kind": "filing",
    },
    {
        "id": "S_MSFT_OAI_2025",
        "title": "The next chapter of the Microsoft–OpenAI partnership",
        "publisher": "Microsoft Corporate Blog",
        "date": "2025-10-28",
        "url": "https://blogs.microsoft.com/blog/2025/10/28/the-next-chapter-of-the-microsoft-openai-partnership/",
        "used_for": "MSFT ~27% as-converted stake in OpenAI PBC; incremental $250B Azure commitment",
        "kind": "press",
    },
    {
        "id": "S_MSFT_10K_OAI",
        "title": "Microsoft Form 10-K / subsequent event — OpenAI recapitalization note",
        "publisher": "SEC EDGAR",
        "date": "2025-10",
        "url": "https://www.sec.gov/Archives/edgar/data/789019/000119312525256321/R26.htm",
        "used_for": "Equity-method accounting; $13B funding commitments; $250B Azure purchase commitment",
        "kind": "filing",
    },
    {
        "id": "S_AWS_NVDA_1M",
        "title": "Nvidia to sell 1 million chips to Amazon by end of 2027 (Reuters)",
        "publisher": "Reuters",
        "date": "2026-03-19",
        "url": "https://www.reuters.com/business/retail-consumer/nvidia-sell-1-million-chips-amazon-by-end-2027-cloud-deal-2026-03-19/",
        "used_for": "AWS–NVIDIA multi-year GPU supply (~1M GPUs through 2027); amount undisclosed",
        "kind": "news",
    },
    {
        "id": "S_AWS_NVDA_2M",
        "title": "AWS and NVIDIA to Deliver 2 Million Additional GPUs (2027–2028)",
        "publisher": "NVIDIA Newsroom / About Amazon",
        "date": "2026-08-26",
        "url": "https://nvidianews.nvidia.com/news/aws-and-nvidia-to-deliver-2-million-additional-gpus-and-next-generation-infrastructure-for-agentic-and-physical-ai",
        "used_for": "Additional ~2M NVIDIA GPUs on AWS in 2027–2028; Vera CPU / networking collaboration",
        "kind": "press",
    },
    {
        "id": "S_MSFT_FY26Q1",
        "title": "Microsoft FY2026 Q1 earnings remarks (OpenAI / Cloud)",
        "publisher": "Microsoft Investor Relations",
        "date": "2025-10",
        "url": "https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q1",
        "used_for": "Microsoft Cloud revenue >$49B (+26% YoY); OpenAI Azure commitment commentary",
        "kind": "ir",
    },
    {
        "id": "S_TSMC_NV_CNBC",
        "title": "Nvidia set to supplant Apple as TSMC's largest customer",
        "publisher": "CNBC",
        "date": "2026-01-26",
        "url": "https://www.cnbc.com/2026/01/26/nvidia-set-to-supplant-apple-as-tsmcs-largest-customer.html",
        "used_for": "Supporting context that NVIDIA is among TSMC's largest customers (TSMC does not name customers in filings)",
        "kind": "news",
    },
    {
        "id": "S_AMD_TSMC",
        "title": "AMD Form 10-K — foundry dependence on TSMC",
        "publisher": "SEC EDGAR / AMD IR",
        "date": "2025",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000002488&type=10-K",
        "used_for": "AMD fabless model; TSMC as primary advanced-node foundry (INFERRED amount undisclosed)",
        "kind": "filing",
    },
    {
        "id": "S_EQIX_HYPER",
        "title": "Equinix — hyperscale / interconnection customer disclosure (10-K)",
        "publisher": "Equinix IR / SEC",
        "date": "2025",
        "url": "https://investor.equinix.com/",
        "used_for": "Equinix as interconnection/colocation platform used by cloud/network ecosystems (no named CW link)",
        "kind": "ir",
    },
    {
        "id": "S_SMCI_NV",
        "title": "Super Micro — NVIDIA preferred partner / GPU server systems",
        "publisher": "Super Micro / NVIDIA partner materials",
        "date": "2025",
        "url": "https://www.supermicro.com/",
        "used_for": "SMCI builds NVIDIA GPU server systems for CSPs/enterprises (commercial OEM supply)",
        "kind": "press",
    },
    {
        "id": "S_ARISTA_DC",
        "title": "Arista Networks — AI / cloud networking platforms",
        "publisher": "Arista IR",
        "date": "2025",
        "url": "https://www.arista.com/en/company/news/press-release",
        "used_for": "Ethernet AI networking for hyperscale/AI clusters (ecosystem role; customer names often undisclosed)",
        "kind": "ir",
    },
    {
        "id": "S_VERTIV_DC",
        "title": "Vertiv — thermal / power management for data centers",
        "publisher": "Vertiv IR",
        "date": "2025",
        "url": "https://investors.vertiv.com/",
        "used_for": "Critical cooling/power equipment sold into AI data centers (sector role)",
        "kind": "ir",
    },
    {
        "id": "S_META_NV",
        "title": "Meta / NVIDIA AI infrastructure partnership announcements",
        "publisher": "NVIDIA / Meta",
        "date": "2025",
        "url": "https://nvidianews.nvidia.com/",
        "used_for": "Meta as major NVIDIA AI infrastructure customer (amounts often undisclosed)",
        "kind": "press",
    },
    {
        "id": "S_MSFT_NV_AZURE",
        "title": "Microsoft Azure — NVIDIA GPU accelerated instances",
        "publisher": "Microsoft Azure / NVIDIA",
        "date": "2025",
        "url": "https://azure.microsoft.com/en-us/solutions/ai/",
        "used_for": "Azure ND/NC-class GPU VMs powered by NVIDIA; hyperscaler–GPU supply chain",
        "kind": "ir",
    },
    {
        "id": "S_GOOG_NV",
        "title": "Google Cloud — NVIDIA GPU / TPU coexistence; A3/A4 GPU VMs",
        "publisher": "Google Cloud / NVIDIA",
        "date": "2025",
        "url": "https://cloud.google.com/blog/topics/customers/announcing-google-cloud-a3-mega-powered-by-nvidia-h100",
        "used_for": "Alphabet/Google Cloud as NVIDIA GPU cloud customer",
        "kind": "press",
    },
    {
        "id": "S_ORCL_NV",
        "title": "Oracle Cloud Infrastructure — NVIDIA GPU superclusters",
        "publisher": "Oracle / NVIDIA",
        "date": "2025",
        "url": "https://www.oracle.com/news/",
        "used_for": "OCI as NVIDIA GPU cloud capacity provider/customer",
        "kind": "press",
    },
    {
        "id": "S_APPLE_TSMC",
        "title": "TSMC / Apple long-standing foundry customer relationship",
        "publisher": "TSMC annual report commentary / industry",
        "date": "2025",
        "url": "https://investor.tsmc.com/",
        "used_for": "Apple historically among TSMC's largest customers (TSMC does not name customers; VERIFIED industry consensus + TSMC top-customer %)",
        "kind": "ir",
    },
    {
        "id": "S_ASML_TSMC",
        "title": "ASML — EUV lithography equipment customer concentration (TSMC among major)",
        "publisher": "ASML annual report",
        "date": "2025",
        "url": "https://www.asml.com/investors",
        "used_for": "ASML supplies advanced lithography tools to leading foundries including TSMC",
        "kind": "ir",
    },
]


NEW_ENTITIES = [
    {"id": "apple", "name": "Apple", "name_ko": "애플", "group": "customer", "sector": "소비자 전자 · 반도체 설계",
     "entity_type": "company", "role": "TSMC 주요 파운드리 고객 (모바일·PC SoC)",
     "description": "자체 설계 칩(A/M 시리즈)을 TSMC에 위탁 생산. AI 인프라 GPU 생태계와는 별도 축이지만 TSMC 고객 집중도 분석에 필수.",
     "listed": True, "ticker": "AAPL", "exchange": "Nasdaq", "quote_currency": "USD", "listing_note": None,
     "display_size": 8, "source_status": "VERIFIED", "source_ids": ["S_APPLE_TSMC"],
     "key_drivers": ["모바일·PC SoC 수요", "TSMC 선단 공정 배정"]},
    {"id": "broadcom", "name": "Broadcom", "name_ko": "브로드컴", "group": "semiconductor", "sector": "반도체 · 네트워킹·맞춤 ASIC",
     "entity_type": "company", "role": "맞춤 AI 가속기·네트워킹 칩 공급 (하이퍼스케일러)",
     "description": "하이퍼스케일러향 맞춤 ASIC·네트워킹 실리콘. TSMC 등 파운드리에 위탁. CoreWeave와 직접 계약은 미확인.",
     "listed": True, "ticker": "AVGO", "exchange": "Nasdaq", "quote_currency": "USD", "listing_note": None,
     "display_size": 8, "source_status": "VERIFIED", "source_ids": ["S_TSMC_NV_CNBC"],
     "key_drivers": ["맞춤 AI ASIC", "네트워킹 실리콘"]},
    {"id": "micron", "name": "Micron Technology", "name_ko": "마이크론", "group": "semiconductor", "sector": "반도체 · HBM·DRAM",
     "entity_type": "company", "role": "NVIDIA HBM/메모리 공급사 (10-K 명시)",
     "description": "NVIDIA 10-K가 메모리 구매처로 SK hynix·Micron·Samsung을 명시.",
     "listed": True, "ticker": "MU", "exchange": "Nasdaq", "quote_currency": "USD", "listing_note": None,
     "display_size": 7, "source_status": "VERIFIED", "source_ids": ["S_NVDA_10K_FY26"],
     "key_drivers": ["HBM 공급", "AI 서버 메모리 수요"]},
    {"id": "asml", "name": "ASML", "name_ko": "ASML", "group": "semiconductor", "sector": "반도체 장비 · EUV",
     "entity_type": "company", "role": "선단 리소그래피 장비 공급 (TSMC 등 파운드리)",
     "description": "EUV 등 노광 장비의 사실상 독점 공급사. TSMC 등 선단 파운드리 CAPEX의 핵심 병목.",
     "listed": True, "ticker": "ASML", "exchange": "Nasdaq", "quote_currency": "USD",
     "listing_note": "Nasdaq ADR (본주: Euronext Amsterdam)",
     "display_size": 7, "source_status": "VERIFIED", "source_ids": ["S_ASML_TSMC"],
     "key_drivers": ["EUV 장비 납기", "파운드리 CAPEX 사이클"]},
    {"id": "smci", "name": "Super Micro Computer", "name_ko": "슈퍼마이크로", "group": "server", "sector": "서버 · GPU 시스템",
     "entity_type": "company", "role": "NVIDIA GPU 서버·랙 시스템 OEM",
     "description": "AI GPU 서버·액침/공랭 시스템 조립·공급. 하이퍼스케일·엔터프라이즈 고객에 NVIDIA 플랫폼 기반 시스템 제공.",
     "listed": True, "ticker": "SMCI", "exchange": "Nasdaq", "quote_currency": "USD", "listing_note": None,
     "display_size": 7, "source_status": "VERIFIED", "source_ids": ["S_SMCI_NV"],
     "key_drivers": ["GPU 서버 수요", "NVIDIA 플랫폼 채택"]},
    {"id": "hpe", "name": "Hewlett Packard Enterprise", "name_ko": "HPE", "group": "server", "sector": "서버 · 하이브리드 클라우드",
     "entity_type": "company", "role": "엔터프라이즈·AI 서버/슈퍼컴퓨팅",
     "description": "NVIDIA 협력 AI 시스템·그린레이크. CoreWeave와 직접 계약 미확인.",
     "listed": True, "ticker": "HPE", "exchange": "NYSE", "quote_currency": "USD", "listing_note": None,
     "display_size": 6, "source_status": "VERIFIED", "source_ids": ["S_SMCI_NV"],
     "key_drivers": ["엔터프라이즈 AI 인프라"]},
    {"id": "arista", "name": "Arista Networks", "name_ko": "아리스타", "group": "server", "sector": "데이터센터 네트워킹",
     "entity_type": "company", "role": "AI/클라우드 이더넷 스위칭",
     "description": "하이퍼스케일·AI 클러스터용 고속 이더넷. 고객명은 종종 비공시.",
     "listed": True, "ticker": "ANET", "exchange": "NYSE", "quote_currency": "USD", "listing_note": None,
     "display_size": 6, "source_status": "VERIFIED", "source_ids": ["S_ARISTA_DC"],
     "key_drivers": ["AI 클러스터 네트워킹"]},
    {"id": "equinix", "name": "Equinix", "name_ko": "에퀴닉스", "group": "datacenter", "sector": "코로케이션 · 상호접속",
     "entity_type": "company", "role": "글로벌 IBX 데이터센터·상호접속",
     "description": "클라우드·네트워크·엔터프라이즈가 모이는 상호접속 허브. 개별 하이퍼스케일 계약액은 보통 비공시.",
     "listed": True, "ticker": "EQIX", "exchange": "Nasdaq", "quote_currency": "USD", "listing_note": None,
     "display_size": 7, "source_status": "VERIFIED", "source_ids": ["S_EQIX_HYPER"],
     "key_drivers": ["상호접속 수요", "AI 엣지·클라우드 인접 배치"]},
    {"id": "digital_realty", "name": "Digital Realty", "name_ko": "디지털 리얼티", "group": "datacenter", "sector": "데이터센터 REIT",
     "entity_type": "company", "role": "하이퍼스케일·엔터프라이즈 데이터센터",
     "description": "대규모 데이터센터 임대·개발. 전력·냉각 제약이 AI 수요와 연동.",
     "listed": True, "ticker": "DLR", "exchange": "NYSE", "quote_currency": "USD", "listing_note": None,
     "display_size": 6, "source_status": "VERIFIED", "source_ids": ["S_EQIX_HYPER"],
     "key_drivers": ["하이퍼스케일 임대", "전력 확보"]},
    {"id": "vertiv", "name": "Vertiv", "name_ko": "버티브", "group": "datacenter", "sector": "데이터센터 전력·냉각 장비",
     "entity_type": "company", "role": "UPS·냉각·전원 인프라 공급",
     "description": "AI 고밀도 랙용 열관리·전력 장비. 데이터센터 CAPEX 사이클에 민감.",
     "listed": True, "ticker": "VRT", "exchange": "NYSE", "quote_currency": "USD", "listing_note": None,
     "display_size": 6, "source_status": "VERIFIED", "source_ids": ["S_VERTIV_DC"],
     "key_drivers": ["고밀도 냉각", "데이터센터 CAPEX"]},
    {"id": "eaton", "name": "Eaton", "name_ko": "이튼", "group": "datacenter", "sector": "전력 관리 · 전기 장비",
     "entity_type": "company", "role": "데이터센터·산업 전력 인프라",
     "description": "배전·UPS·전기 인프라. AI 데이터센터 전력 확장과 연계된 장비 수요.",
     "listed": True, "ticker": "ETN", "exchange": "NYSE", "quote_currency": "USD", "listing_note": None,
     "display_size": 5, "source_status": "VERIFIED", "source_ids": ["S_VERTIV_DC"],
     "key_drivers": ["전력 인프라 투자"]},
    {"id": "schneider", "name": "Schneider Electric", "name_ko": "슈나이더 일렉트릭", "group": "datacenter", "sector": "에너지 관리 · 자동화",
     "entity_type": "company", "role": "데이터센터 전력·냉각·DCIM",
     "description": "데이터센터 전력·냉각·소프트웨어. Euronext 본주.",
     "listed": True, "ticker": "SBGSY", "exchange": "OTC", "quote_currency": "USD",
     "listing_note": "ADR (본주: Euronext Paris SU)",
     "display_size": 5, "source_status": "VERIFIED", "source_ids": ["S_VERTIV_DC"],
     "key_drivers": ["데이터센터 전력·냉각"]},
    {"id": "foxconn", "name": "Hon Hai (Foxconn)", "name_ko": "폭스콘", "group": "server", "sector": "전자 제조 · 서버 ODM",
     "entity_type": "company", "role": "NVIDIA 제품 조립·테스트 ODM (10-K 명시)",
     "description": "NVIDIA 10-K가 최종 제품 조립·테스트 협력사로 Hon Hai 등을 명시.",
     "listed": True, "ticker": "HNHPF", "exchange": "OTC", "quote_currency": "USD",
     "listing_note": "ADR (본주: TWSE 2317)",
     "display_size": 6, "source_status": "VERIFIED", "source_ids": ["S_NVDA_10K_FY26"],
     "key_drivers": ["GPU 시스템 제조 용량"]},
    {"id": "wistron", "name": "Wistron", "name_ko": "위스트론", "group": "server", "sector": "전자 제조 · 서버 ODM",
     "entity_type": "company", "role": "NVIDIA 제품 조립·테스트 ODM (10-K 명시)",
     "description": "NVIDIA 10-K가 조립·테스트 협력사로 Wistron을 명시.",
     "listed": True, "ticker": "WISTF", "exchange": "OTC", "quote_currency": "USD",
     "listing_note": "해외 OTC (본주: TWSE 3231)",
     "display_size": 5, "source_status": "VERIFIED", "source_ids": ["S_NVDA_10K_FY26"],
     "key_drivers": ["서버 ODM 용량"]},
]


def rel(id_, src, tgt, rtype, channel, label, status, sids, explanation, amount=None, note="", roles=None, impact=""):
    return {
        "id": id_, "source": src, "target": tgt, "relationship_type": rtype, "impact_channel": channel,
        "label": label, "impact_label": impact or label, "source_status": status, "source_ids": sids,
        "contract_ids": [], "commercial_ids": [], "amount_usd_m": amount, "amount_note": note,
        "roles": roles or [], "explanation": explanation,
    }


NEW_RELS = [
    # Microsoft ↔ OpenAI (independent of CoreWeave)
    rel("eq_msft_openai", "microsoft", "openai", "EQUITY_INVESTMENT", "equity",
        "Microsoft equity stake in OpenAI PBC", "VERIFIED", ["S_MSFT_OAI_2025", "S_MSFT_10K_OAI"],
        "2025.10 재자본화 후 Microsoft는 OpenAI Group PBC에 as-converted diluted 기준 약 27% 지분(평가액 약 $135B 공시). 누적 출자 약정 $13B는 지분법 회계.",
        amount=135000, note="공시 평가액(지분) · 출자 약정 $13B와 별도", roles=["Strategic investor"]),
    rel("c_openai_azure", "openai", "microsoft", "CUSTOMER", "customer",
        "OpenAI Azure cloud commitment", "VERIFIED", ["S_MSFT_OAI_2025", "S_MSFT_10K_OAI"],
        "OpenAI가 Azure 서비스에 대해 추가 $250B 구매 약정을 공시. 금액은 약정(commitment)이며 이행 시점은 다년.",
        amount=250000, note="증분 Azure 구매 약정(commitment)", roles=["Cloud customer"]),
    # Hyperscaler → NVIDIA GPU supply
    rel("s_amazon_nvidia", "amazon", "nvidia", "SUPPLIER", "supply_chain",
        "AWS purchases NVIDIA GPUs", "VERIFIED", ["S_AWS_NVDA_1M", "S_AWS_NVDA_2M"],
        "AWS가 2026–2027에 약 100만 장, 이어 2027–2028에 추가 약 200만 장의 NVIDIA GPU 배치를 발표. 계약 총액은 미공시.",
        note="대수 공시 · USD 총액 미공시"),
    rel("s_microsoft_nvidia", "microsoft", "nvidia", "SUPPLIER", "supply_chain",
        "Azure NVIDIA GPU infrastructure", "VERIFIED", ["S_MSFT_NV_AZURE", "S_NVDA_10K_FY26"],
        "Azure가 NVIDIA GPU 가속 인스턴스를 제공. NVIDIA 10-K는 주요 CSP를 고객군으로 명시(개별 금액 비공시).",
        note="금액 미공시"),
    rel("s_alphabet_nvidia", "alphabet", "nvidia", "SUPPLIER", "supply_chain",
        "Google Cloud NVIDIA GPU VMs", "VERIFIED", ["S_GOOG_NV", "S_NVDA_10K_FY26"],
        "Google Cloud A3 등 NVIDIA GPU VM. TPU와 병행. 개별 구매액 미공시.",
        note="금액 미공시"),
    rel("s_meta_nvidia", "meta", "nvidia", "SUPPLIER", "supply_chain",
        "Meta AI infrastructure / NVIDIA", "VERIFIED", ["S_META_NV", "S_NVDA_10K_FY26"],
        "Meta는 대규모 AI 학습·추론 인프라에서 NVIDIA GPU를 사용(파트너십·제품 발표). 총액 미공시.",
        note="금액 미공시"),
    rel("s_oracle_nvidia", "oracle", "nvidia", "SUPPLIER", "supply_chain",
        "OCI NVIDIA GPU superclusters", "VERIFIED", ["S_ORCL_NV", "S_NVDA_10K_FY26"],
        "Oracle Cloud가 NVIDIA GPU 슈퍼클러스터를 제공·확장. 개별 계약액은 발표마다 상이·부분 공시.",
        note="금액 혼재·미공시 가능"),
    # NVIDIA memory / foundry (10-K) — strengthen / add micron
    rel("s_nvidia_micron", "nvidia", "micron", "SUPPLIER", "supply_chain",
        "NVIDIA buys memory from Micron", "VERIFIED", ["S_NVDA_10K_FY26"],
        "NVIDIA FY2026 10-K: memory purchased from SK hynix, Micron, and Samsung.",
        note="금액 미공시"),
    rel("s_nvidia_foxconn", "nvidia", "foxconn", "SUPPLIER", "supply_chain",
        "Hon Hai assembly/test for NVIDIA", "VERIFIED", ["S_NVDA_10K_FY26"],
        "NVIDIA 10-K: Hon Hai Precision 등 독립 하청이 최종 제품 조립·테스트.",
        note="금액 미공시"),
    rel("s_nvidia_wistron", "nvidia", "wistron", "SUPPLIER", "supply_chain",
        "Wistron assembly/test for NVIDIA", "VERIFIED", ["S_NVDA_10K_FY26"],
        "NVIDIA 10-K: Wistron이 조립·테스트 협력사로 명시.",
        note="금액 미공시"),
    # AMD ↔ TSMC
    rel("s_amd_tsmc", "amd", "tsmc", "SUPPLIER", "supply_chain",
        "AMD advanced-node foundry at TSMC", "INFERRED", ["S_AMD_TSMC", "S_TSMC_NV_CNBC"],
        "AMD는 fabless로 선단 공정을 TSMC에 의존(10-K 위험요인). 고객별 매출 비중은 TSMC가 비공시.",
        note="금액 미공시"),
    # Apple ↔ TSMC
    rel("s_apple_tsmc", "apple", "tsmc", "SUPPLIER", "supply_chain",
        "Apple SoC foundry at TSMC", "INFERRED", ["S_APPLE_TSMC", "S_TSMC_NV_CNBC"],
        "Apple은 TSMC 최대 고객군으로 널리 알려짐. TSMC는 고객명을 공시하지 않으며 상위 고객 매출 비중만 공개.",
        note="고객명 비공시 · 산업 컨센서스"),
    # Broadcom ↔ TSMC (ecosystem)
    rel("s_broadcom_tsmc", "broadcom", "tsmc", "SUPPLIER", "supply_chain",
        "Broadcom foundry at TSMC", "INFERRED", ["S_TSMC_NV_CNBC"],
        "Broadcom 등 무공장 설계사가 TSMC 고객군에 포함(산업·보도). 개별 금액 미공시.",
        note="금액 미공시"),
    # ASML → TSMC
    rel("s_tsmc_asml", "tsmc", "asml", "SUPPLIER", "supply_chain",
        "TSMC buys ASML lithography tools", "VERIFIED", ["S_ASML_TSMC"],
        "ASML EUV/DUV 장비가 선단 파운드리 CAPEX의 핵심. TSMC는 ASML의 주요 고객사 중 하나.",
        note="개별 주문액은 분기별로 부분 공시"),
    # SMCI / HPE ↔ NVIDIA
    rel("s_smci_nvidia", "smci", "nvidia", "SUPPLIER", "supply_chain",
        "Super Micro NVIDIA GPU servers", "VERIFIED", ["S_SMCI_NV"],
        "SMCI가 NVIDIA GPU 기반 AI 서버·랙을 설계·판매(파트너/제품). 재판매 구조로 NVIDIA가 공급사.",
        note="금액 미공시"),
    rel("s_hpe_nvidia", "hpe", "nvidia", "SUPPLIER", "supply_chain",
        "HPE NVIDIA AI systems", "INFERRED", ["S_SMCI_NV", "S_NVDA_10K_FY26"],
        "HPE가 NVIDIA와 AI 시스템·슈퍼컴퓨팅 협력. OEM 경로.",
        note="금액 미공시"),
    # Dell already linked; add SMCI path clarity via nvidia (done)
    # Datacenter equipment qualitative ecosystem links (sector, not fake contracts)
    rel("s_equinix_vertiv", "equinix", "vertiv", "SUPPLIER", "supply_chain",
        "DC operator ↔ critical infrastructure vendors (sector)", "INFERRED", ["S_EQIX_HYPER", "S_VERTIV_DC"],
        "코로/하이퍼스케일 캠퍼스는 Vertiv 등 전력·냉각 장비를 사용. 특정 계약·금액은 이 엣지에 부여하지 않음.",
        note="섹터 경로 · 개별 계약 미특정"),
    rel("s_dlr_eaton", "digital_realty", "eaton", "SUPPLIER", "supply_chain",
        "DC REIT ↔ power equipment (sector)", "INFERRED", ["S_EQIX_HYPER", "S_VERTIV_DC"],
        "데이터센터 REIT의 전력 인프라는 Eaton 등 장비사와 연계되는 것이 일반적. 특정 계약 미확인.",
        note="섹터 경로 · 개별 계약 미특정"),
    rel("s_vertiv_schneider", "vertiv", "schneider", "INDIRECT_SUPPLY_CHAIN", "supply_chain",
        "Competing/overlapping DC power & cooling vendors", "INFERRED", ["S_VERTIV_DC"],
        "동일 AI 데이터센터 CAPEX 사이클에 노출된 장비 경쟁사·대체재 관계(동일 계약 중복 계상 금지).",
        note="경쟁·대체 · 금액 없음"),
]


PROFILES = {
    "nvidia": {
        "as_of": "2026-01-25",
        "period_label": "FY2026 (year ended Jan 25, 2026)",
        "currency": "USD",
        "unit": "million",
        "overview": "Fabless AI/accelerated computing. Designs GPUs/SoCs; manufactures via foundries (TSMC, Samsung); sells to CSPs, OEMs, ODMs, enterprises.",
        "metrics": [
            {"id": "revenue", "label": "Revenue", "value_usd_m": None, "display": "See S_NVDA_FY26 / 10-K", "period": "FY2026", "status": "VERIFIED", "source_ids": ["S_NVDA_FY26", "S_NVDA_10K_FY26"], "note": "Use filing totals; app stores qualitative profile when single figure already cited in entity description."},
            {"id": "business_model", "label": "Business model", "value_usd_m": None, "display": "Fabless + CUDA platform", "period": "ongoing", "status": "VERIFIED", "source_ids": ["S_NVDA_10K_FY26"]},
        ],
        "financing_notes": [
            "Public equity (NVDA); debt exists but AI cycle exposure is primarily through customer CAPEX and supply commitments, not CoreWeave-style DDTLs.",
            "Places non-cancellable component orders / deposits to secure capacity (10-K).",
        ],
        "risk_factors": [
            "Customer concentration among large CSPs/OEMs",
            "Foundry and CoWoS packaging capacity",
            "Export controls / geopolitics (Taiwan supply chain)",
            "Competition (AMD, custom ASICs)",
        ],
        "missing": ["instrument-level floating-rate debt schedule comparable to CoreWeave 10-Q Note 10"],
        "source_ids": ["S_NVDA_10K_FY26", "S_NVDA_FY26"],
    },
    "microsoft": {
        "as_of": "2025-10-28",
        "period_label": "FY2026 Q1 commentary + OpenAI definitive agreement",
        "currency": "USD",
        "unit": "million",
        "overview": "Hyperscale cloud (Azure), productivity, AI platform. Strategic investor in and cloud provider to OpenAI.",
        "metrics": [
            {"id": "cloud_revenue_q", "label": "Microsoft Cloud revenue (quarter)", "value_usd_m": 49000, "display": ">$49B", "period": "FY2026 Q1", "status": "VERIFIED", "source_ids": ["S_MSFT_FY26Q1"]},
            {"id": "openai_azure_commit", "label": "OpenAI incremental Azure commitment", "value_usd_m": 250000, "display": "$250B", "period": "2025-10 agreement", "status": "VERIFIED", "source_ids": ["S_MSFT_OAI_2025", "S_MSFT_10K_OAI"]},
            {"id": "openai_funding_commit", "label": "Cumulative OpenAI funding commitments", "value_usd_m": 13000, "display": "$13B", "period": "through recapitalization", "status": "VERIFIED", "source_ids": ["S_MSFT_10K_OAI"]},
        ],
        "financing_notes": [
            "Investment-grade public company; large investment-grade bond program (details in MSFT 10-K — not fully mirrored here).",
            "OpenAI stake accounted under equity method ($13B commitments).",
        ],
        "risk_factors": [
            "AI CAPEX intensity and power availability",
            "OpenAI partnership economics / competitive cloud shift",
            "Regulatory scrutiny of large AI partnerships",
        ],
        "missing": ["full debt maturity table by instrument in this dataset"],
        "source_ids": ["S_MSFT_FY26Q1", "S_MSFT_OAI_2025", "S_MSFT_10K_OAI"],
    },
    "amazon": {
        "as_of": "2026-08-26",
        "period_label": "AWS–NVIDIA capacity announcements 2026",
        "currency": "USD",
        "unit": "million",
        "overview": "AWS hyperscaler; multi-year NVIDIA GPU deployments alongside custom Trainium silicon.",
        "metrics": [
            {"id": "gpu_commit_units", "label": "NVIDIA GPUs (announced deployments)", "value_usd_m": None, "display": "~1M (2026–27) + ~2M (2027–28)", "period": "2026 announcements", "status": "VERIFIED", "source_ids": ["S_AWS_NVDA_1M", "S_AWS_NVDA_2M"], "note": "Unit counts disclosed; USD not disclosed"},
        ],
        "financing_notes": ["Investment-grade; AWS CAPEX funded at Amazon parent level."],
        "risk_factors": ["AI CAPEX / power", "Custom silicon vs GPU mix", "Cloud competition"],
        "missing": ["USD value of NVIDIA purchase agreements"],
        "source_ids": ["S_AWS_NVDA_1M", "S_AWS_NVDA_2M"],
    },
    "tsmc": {
        "as_of": "2025-12",
        "period_label": "TSMC annual / investor disclosures",
        "currency": "USD",
        "unit": "million",
        "overview": "World's leading pure-play foundry. Customers are fabless designers (NVIDIA, AMD, Apple, Broadcom, etc.). Does not publicly name customers.",
        "metrics": [
            {"id": "top10_rev_share", "label": "Top-10 customers revenue share", "value_usd_m": None, "display": "~76% (example period cited in press)", "period": "per TSMC commentary", "status": "INFERRED", "source_ids": ["S_TSMC_NV_CNBC"]},
        ],
        "financing_notes": ["Large multi-year CAPEX; ASML tools are critical path items."],
        "risk_factors": ["Geopolitical / Taiwan", "Customer concentration", "Advanced packaging capacity"],
        "missing": ["named customer revenue breakdown"],
        "source_ids": ["S_TSMC_NV_CNBC", "S_ASML_TSMC"],
    },
    "sk_hynix": {
        "as_of": "2026-01-25",
        "period_label": "NVIDIA FY2026 10-K supplier list",
        "currency": "KRW/USD",
        "unit": "mixed",
        "overview": "HBM leader; named NVIDIA memory supplier in NVIDIA 10-K.",
        "metrics": [],
        "financing_notes": ["Korean chaebol financing; detailed KRW debt schedule not mirrored in this USD-centric dataset."],
        "risk_factors": ["HBM CAPEX", "Customer concentration (AI GPUs)", "FX"],
        "missing": ["USD debt instrument table"],
        "source_ids": ["S_NVDA_10K_FY26"],
    },
    "samsung": {
        "as_of": "2026-01-25",
        "period_label": "NVIDIA FY2026 10-K",
        "currency": "KRW/USD",
        "unit": "mixed",
        "overview": "Foundry + HBM/memory; named in NVIDIA 10-K as wafer foundry and memory supplier.",
        "metrics": [],
        "financing_notes": ["Large balance sheet; instrument-level data not fully ported."],
        "risk_factors": ["Foundry share vs TSMC", "HBM competition with SK hynix"],
        "missing": ["USD debt instrument table"],
        "source_ids": ["S_NVDA_10K_FY26"],
    },
    "oracle": {
        "as_of": "2025",
        "period_label": "OCI–NVIDIA public announcements",
        "currency": "USD",
        "unit": "million",
        "overview": "OCI expanding NVIDIA GPU supercluster capacity; competes with and partners across AI cloud.",
        "metrics": [],
        "financing_notes": ["Public investment-grade / convertible history — not fully mirrored."],
        "risk_factors": ["AI CAPEX", "Cloud competition", "Customer concentration"],
        "missing": ["complete debt schedule in dataset"],
        "source_ids": ["S_ORCL_NV"],
    },
    "coreweave": {
        "as_of": "2026-06-30",
        "period_label": "10-Q Q2 2026",
        "currency": "USD",
        "unit": "million",
        "overview": "Specialized AI cloud; detailed debt instruments already in financials.json.",
        "metrics": [],
        "financing_notes": ["See financials.json instruments (DDTLs, notes, convertibles)."],
        "risk_factors": ["Customer concentration", "Refinancing / floating SOFR debt", "GPU CAPEX"],
        "missing": [],
        "source_ids": ["S_10Q2"],
    },
}


def upsert_list(items: list, news: list, key: str = "id") -> tuple[int, int]:
    idx = {x[key]: i for i, x in enumerate(items)}
    added = updated = 0
    for n in news:
        if n[key] in idx:
            items[idx[n[key]]] = n
            updated += 1
        else:
            items.append(n)
            added += 1
    return added, updated


def main() -> int:
    ent = load("entities.json")
    rels = load("relationships.json")
    src = load("sources.json")

    # Enrich existing hyperscaler descriptions (no longer CW-only orphans)
    enrich = {
        "amazon": {
            "role": "AWS hyperscaler · NVIDIA GPU customer (multi-million GPU deployments)",
            "description": "AWS는 NVIDIA GPU를 대규모로 배치(2026–28 발표). CoreWeave와 직접 상업 계약은 미확인이나, NVIDIA를 통한 산업 생태계에서 중심 노드.",
            "source_ids": ["S1_COMP", "S_AWS_NVDA_1M", "S_AWS_NVDA_2M"],
        },
        "oracle": {
            "role": "OCI hyperscaler · NVIDIA GPU cloud capacity",
            "description": "OCI가 NVIDIA GPU 슈퍼클러스터를 확장. CoreWeave와 직접 계약은 미확인.",
            "source_ids": ["S1_COMP", "S_ORCL_NV"],
        },
        "microsoft": {
            "role": "Azure hyperscaler · OpenAI investor/partner · NVIDIA GPU cloud",
            "description": "Azure AI 인프라 + OpenAI 지분·클라우드 약정. CoreWeave 고객이기도 하나 독립적으로 OpenAI·NVIDIA 축의 중심.",
            "source_ids": list({*(next(e for e in ent['entities'] if e['id']=='microsoft')['source_ids']), "S_MSFT_OAI_2025", "S_MSFT_NV_AZURE"}),
        },
        "alphabet": {
            "role": "Google Cloud hyperscaler · NVIDIA GPU customer",
            "description": "Google Cloud NVIDIA GPU VM + 자체 TPU. CoreWeave 고객 관계와 별도로 NVIDIA 공급망의 수요 중심.",
            "source_ids": list({*(next(e for e in ent['entities'] if e['id']=='alphabet')['source_ids']), "S_GOOG_NV"}),
        },
        "meta": {
            "role": "AI lab / infra operator · NVIDIA GPU customer · CoreWeave customer",
            "description": "Meta는 CoreWeave 고객인 동시에 NVIDIA AI 인프라의 대규모 수요자.",
            "source_ids": list({*(next(e for e in ent['entities'] if e['id']=='meta')['source_ids']), "S_META_NV"}),
        },
        "amd": {
            "role": "AI accelerator vendor · TSMC foundry customer · NVIDIA competitor",
            "description": "AI 가속기에서 NVIDIA와 경쟁. 선단 파운드리는 TSMC 의존(fabless).",
            "source_ids": ["S_AMD_NV", "S_AMD_TSMC"],
        },
    }
    for e in ent["entities"]:
        if e["id"] in enrich:
            e.update({k: v for k, v in enrich[e["id"]].items() if k != "source_ids"})
            e["source_ids"] = enrich[e["id"]]["source_ids"]

    a_e, u_e = upsert_list(ent["entities"], NEW_ENTITIES)
    a_r, u_r = upsert_list(rels["relationships"], NEW_RELS)
    a_s, u_s = upsert_list(src["sources"], NEW_SOURCES)

    ent["meta"]["as_of"] = "2026-10-20"
    ent["meta"]["name"] = "CONTAGION — Multi-center AI Infrastructure Contagion Map"
    ent["meta"]["disclaimer"] = (
        "관계·수치는 공시·공식 발표·신뢰 가능 보도로 확인된 값입니다. "
        "CoreWeave는 상세 차입 공시가 있는 한 노드이며, 선택 기업이 네트워크 분석의 초점이 됩니다. "
        "금리 충격의 금액 계산은 공시된 변동금리 잔액이 있는 경우에 한정하며, 관계가 곧 손실을 뜻하지 않습니다."
    )

    profiles = {"meta": {"as_of": "2026-10-20", "note": "Comparable company dossiers; missing fields stay explicit."}, "profiles": PROFILES}
    save("entities.json", ent)
    save("relationships.json", rels)
    save("sources.json", src)
    save("profiles.json", profiles)

    print(f"entities +{a_e} ~{u_e} total={len(ent['entities'])}")
    print(f"relationships +{a_r} ~{u_r} total={len(rels['relationships'])}")
    print(f"sources +{a_s} ~{u_s} total={len(src['sources'])}")
    print(f"profiles {len(PROFILES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
