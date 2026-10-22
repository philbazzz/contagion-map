#!/usr/bin/env python3
"""Add AI-infra stress candidates, SPVs, sources, relationships, and profiles.

Idempotent. Does not invent financial figures — only disclosed values.
Cutoff: 2026-10-20.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "backend" / "data"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save(name: str, doc: dict) -> None:
    (DATA / name).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def upsert_source(doc: dict, src: dict) -> None:
    ids = {s["id"] for s in doc["sources"]}
    if src["id"] not in ids:
        doc["sources"].append(src)


def upsert_entity(doc: dict, ent: dict, after: str | None = None) -> None:
    ids = {e["id"] for e in doc["entities"]}
    if ent["id"] in ids:
        for i, e in enumerate(doc["entities"]):
            if e["id"] == ent["id"]:
                # enrich description / role without wiping listing fields
                e.update({k: v for k, v in ent.items() if k != "id" or True})
                doc["entities"][i] = {**e, **ent}
                return
    if after:
        for i, e in enumerate(doc["entities"]):
            if e["id"] == after:
                doc["entities"].insert(i + 1, ent)
                return
    doc["entities"].append(ent)


def upsert_rel(doc: dict, rel: dict, after: str | None = None) -> None:
    ids = {r["id"] for r in doc["relationships"]}
    if rel["id"] in ids:
        for i, r in enumerate(doc["relationships"]):
            if r["id"] == rel["id"]:
                doc["relationships"][i] = rel
                return
    if after:
        for i, r in enumerate(doc["relationships"]):
            if r["id"] == after:
                doc["relationships"].insert(i + 1, rel)
                return
    doc["relationships"].append(rel)


def upsert_contract(doc: dict, c: dict) -> None:
    ids = {x["id"] for x in doc["contracts"]}
    if c["id"] in ids:
        for i, x in enumerate(doc["contracts"]):
            if x["id"] == c["id"]:
                doc["contracts"][i] = c
                return
    doc["contracts"].append(c)


SOURCES = [
    {
        "id": "S_CORZ_FINANCE_I",
        "title": "Core Scientific Announces Pricing of $3.3 Billion of Senior Secured Notes",
        "publisher": "Core Scientific IR",
        "date": "2026-04-22",
        "url": "https://investors.corescientific.com/news-events/press-releases/detail/132/core-scientific-announces-pricing-of-3-3-billion-of-senior-secured-notes",
        "used_for": "Core Scientific Finance I LLC $3.3B 7.750% senior secured notes due 2031; parent completion guarantee; parent does not guarantee notes",
        "kind": "press",
    },
    {
        "id": "S_GLXY_HELIOS_II_NOTES",
        "title": "Galaxy Helios Data Centers II LLC senior secured notes (trade / market reports citing offering)",
        "publisher": "Secondary reporting (verify against Galaxy IR / indenture)",
        "date": "2026-07",
        "url": "https://investor.galaxy.com/news-releases/news-release-details/galaxy-completes-phase-i-its-helios-data-center-campus",
        "used_for": "Helios Phase II project financing via Galaxy Helios Data Centers II LLC; CoreWeave lease as credit support; parent completion guarantee reported",
        "kind": "press",
    },
    {
        "id": "S_APLD_MACQ",
        "title": "Applied Digital and Macquarie Asset Management Execute First Funding Milestone in $5.0 Billion AI Infrastructure Partnership",
        "publisher": "Applied Digital IR",
        "date": "2025-10-07",
        "url": "https://ir.applieddigital.com/news-events/press-releases/detail/130/applied-digital-and-macquarie-asset-management-execute",
        "used_for": "MAM preferred equity facility up to $5B; Polaris Forge 1 CoreWeave lease; initial $112.5M draw",
        "kind": "press",
    },
    {
        "id": "S_CIFR_10Q1",
        "title": "Cipher Digital Inc. Form 10-Q (Q1 2026)",
        "publisher": "SEC EDGAR",
        "date": "2026-05",
        "url": "https://www.sec.gov/Archives/edgar/data/1819989/000181998926000028/cifr-20260331.htm",
        "used_for": "Cash $715.2M; HPC build-out; convertible and secured notes; Fluidstack / hyperscaler tenants",
        "kind": "filing",
    },
    {
        "id": "S_CIFR_10Q2",
        "title": "Cipher Digital Inc. Form 10-Q (Q2 2026) debt / revolver disclosures",
        "publisher": "SEC EDGAR / company 10-Q",
        "date": "2026-08",
        "url": "https://www.sec.gov/Archives/edgar/data/1819989/000181998926000041/R67.htm",
        "used_for": "Long-term borrowings / principal outstanding; $200M revolver undrawn; minimum liquidity covenant",
        "kind": "filing",
    },
    {
        "id": "S_WYFI_FY25",
        "title": "WhiteFiber, Inc. Reports Fourth Quarter and Full Year 2025 Results",
        "publisher": "WhiteFiber IR",
        "date": "2026-03-26",
        "url": "https://whitefiber.investorroom.com/2026-03-26-WhiteFiber,-Inc-Reports-Fourth-Quarter-and-Full-Year-2025-Results",
        "used_for": "Cash $114.4M YE2025; no funded debt YE2025; $230M 4.5% converts Jan 2026; Nscale colocation",
        "kind": "press",
    },
    {
        "id": "S_WYFI_NSCALE",
        "title": "WhiteFiber and Nscale Announce 10-Year, 40 MW Colocation Agreement (~$865M)",
        "publisher": "WhiteFiber IR",
        "date": "2025-12-18",
        "url": "https://whitefiber.investorroom.com/2025-12-18-WhiteFiber-and-Nscale-Announce-10-Year,-40-MW-Colocation-Agreement-Representing-Approximately-865-Million-in-Total-Contract-Value-at-NC-1-AI-Data-Center-Campus",
        "used_for": "NC-1 40MW Nscale lease ~$865M TCV",
        "kind": "press",
    },
    {
        "id": "S_WULF_10Q2",
        "title": "TeraWulf Inc. Form 10-Q (Q2 2026)",
        "publisher": "SEC EDGAR / TeraWulf IR",
        "date": "2026-08-05",
        "url": "https://investors.terawulf.com/sec-filings/all-sec-filings/content/0001083301-26-000166/wulf-20260630.htm",
        "used_for": "Cash $2,619.2M; LT debt ~$3,019M; ST converts ~$1,102M; Fluidstack / Google credit support for HPC leases",
        "kind": "filing",
    },
    {
        "id": "S_IREN_FY26",
        "title": "IREN Reports FY26 Results",
        "publisher": "SEC EDGAR / IREN",
        "date": "2026-08-27",
        "url": "https://www.sec.gov/Archives/edgar/data/1878848/000187884826000051/irenreportsfy26results.htm",
        "used_for": "AI Cloud transition; GPU financings; contracted ARR commentary",
        "kind": "press",
    },
    {
        "id": "S_NBIS_20F25",
        "title": "Nebius Group N.V. Form 20-F (FY2025)",
        "publisher": "SEC EDGAR",
        "date": "2026",
        "url": "https://www.sec.gov/Archives/edgar/data/1513845/000110465926052948/nbis-20251231x20f.htm",
        "used_for": "Capital-intensive AI infra; need for additional financing disclosed as risk",
        "kind": "filing",
    },
    {
        "id": "S_ACIS_NBIS_IREN",
        "title": "AI Infrastructure Expansion Still Depends on External Funding (H1 2026 comps)",
        "publisher": "ACIS Research",
        "date": "2026-10-18",
        "url": "https://acisresearch.com/en/research/memos/ai-infrastructure-external-funding-crwv-nbis-iren-2026-10-18",
        "used_for": "H1 2026 cash/debt/OCF/capex comparables for NBIS and IREN (research synthesis of filings)",
        "kind": "research",
    },
    {
        "id": "S_NSCALE_B",
        "title": "Nscale Raises $1.1B Series B",
        "publisher": "Nscale",
        "date": "2025-09-25",
        "url": "https://www.nscale.tech/press-releases/nscale-series-b",
        "used_for": "Private AI hyperscaler funding; NVIDIA / Blue Owl participation",
        "kind": "press",
    },
    {
        "id": "S_NSCALE_PREIPO",
        "title": "Nscale Raises $3.36 Billion in Pre-IPO Convertible Financing",
        "publisher": "Nscale",
        "date": "2026-09-25",
        "url": "https://www.nscale.com/press-releases/pre-ipo-convertible-financing",
        "used_for": "Pre-IPO convertible; NVIDIA $1B commitment tranche; private — no full public financials",
        "kind": "press",
    },
    {
        "id": "S_SLNH_10Q2",
        "title": "Soluna Holdings, Inc. Form 10-Q (Q2 2026)",
        "publisher": "SEC EDGAR",
        "date": "2026-08",
        "url": "https://www.sec.gov/Archives/edgar/data/64463/000162828026056702/slnh-20260630.htm",
        "used_for": "Cash $113.4M; current debt $30.1M; LT debt $3.0M as of 2026-06-30",
        "kind": "filing",
    },
    {
        "id": "S_HUT_10Q2",
        "title": "Hut 8 Corp. Form 10-Q (Q2 2026)",
        "publisher": "SEC EDGAR",
        "date": "2026-08",
        "url": "https://www.sec.gov/Archives/edgar/data/1964789/000110465926090025/hut-20260630x10q.htm",
        "used_for": "River Bend $3.25B / Beacon Point $4.25B project notes; Fluidstack+Google backstop; parent largely non-recourse",
        "kind": "filing",
    },
    {
        "id": "S_HUT_Q2_PR",
        "title": "Hut 8 Reports Second Quarter 2026 Results",
        "publisher": "Hut 8 / PR Newswire",
        "date": "2026-08",
        "url": "https://www.prnewswire.com/news-releases/hut-8-reports-second-quarter-2026-results-302841830.html",
        "used_for": "~$8.1B liquidity incl. BTC; IG project financing; no general recourse parent debt after Coatue conversion",
        "kind": "press",
    },
]


def entities() -> list[dict]:
    return [
        {
            "id": "cipher_digital",
            "name": "Cipher Digital",
            "name_ko": "사이퍼 디지털",
            "group": "datacenter",
            "sector": "AI·HPC 데이터센터",
            "entity_type": "company",
            "role": "HPC 호스팅 · 비트코인→AI 전환",
            "description": "구 Cipher Mining. Odessa·Black Pearl·Barber Lake 등 HPC 호스팅 개발. Fluidstack/하이퍼스케일러 임차. 대규모 선순위담보채·전환사채.",
            "listed": True,
            "ticker": "CIFR",
            "exchange": "Nasdaq",
            "quote_currency": "USD",
            "listing_note": None,
            "display_size": 5,
            "source_status": "VERIFIED",
            "source_ids": ["S_CIFR_10Q1", "S_CIFR_10Q2"],
            "key_drivers": ["project_financing", "capex_funding"],
        },
        {
            "id": "whitefiber",
            "name": "WhiteFiber",
            "name_ko": "화이트파이버",
            "group": "datacenter",
            "sector": "AI 데이터센터 · GPU 클라우드",
            "entity_type": "company",
            "role": "AI 코로케이션 · 클라우드",
            "description": "2025.8 Nasdaq IPO. NC-1에 Nscale 40MW/~$865M 계약. YE2025 무차입 후 2026.1 $230M 전환사채.",
            "listed": True,
            "ticker": "WYFI",
            "exchange": "Nasdaq",
            "quote_currency": "USD",
            "listing_note": None,
            "display_size": 4,
            "source_status": "VERIFIED",
            "source_ids": ["S_WYFI_FY25", "S_WYFI_NSCALE"],
            "key_drivers": ["construction_financing", "tenant_concentration"],
        },
        {
            "id": "terawulf",
            "name": "TeraWulf",
            "name_ko": "테라울프",
            "group": "datacenter",
            "sector": "AI·HPC 데이터센터",
            "entity_type": "company",
            "role": "HPC 리스 · Fluidstack/Google 신용보강",
            "description": "비트코인→HPC. Fluidstack 장기 리스(Google 신용보강). 2026.6.30 현금 ~$2.62B, LT debt ~$3.02B, ST converts ~$1.10B.",
            "listed": True,
            "ticker": "WULF",
            "exchange": "Nasdaq",
            "quote_currency": "USD",
            "listing_note": None,
            "display_size": 5,
            "source_status": "VERIFIED",
            "source_ids": ["S_WULF_10Q2"],
            "key_drivers": ["refinancing", "project_debt"],
        },
        {
            "id": "iren",
            "name": "IREN",
            "name_ko": "아이렌",
            "group": "ai_infra",
            "sector": "AI 클라우드 · 데이터센터",
            "entity_type": "company",
            "role": "AI Cloud · GPU 금융",
            "description": "비트코인→AI Cloud. GPU 금융·선수금에 의존하는 확장. H1'26 비교 기준 현금·부채 규모 큼(연구 합성).",
            "listed": True,
            "ticker": "IREN",
            "exchange": "Nasdaq",
            "quote_currency": "USD",
            "listing_note": None,
            "display_size": 5,
            "source_status": "VERIFIED",
            "source_ids": ["S_IREN_FY26", "S_ACIS_NBIS_IREN"],
            "key_drivers": ["gpu_financing", "external_funding"],
        },
        {
            "id": "nscale",
            "name": "Nscale",
            "name_ko": "엔스케일",
            "group": "ai_infra",
            "sector": "AI 인프라 (비상장)",
            "entity_type": "company",
            "role": "비상장 AI 하이퍼스케일러",
            "description": "유럽계 AI 인프라. Series B $1.1B·Pre-IPO convert $3.36B 공시. 공개 연결재무제표 부족 → 정량 스트레스 미검증.",
            "listed": False,
            "ticker": None,
            "exchange": None,
            "quote_currency": None,
            "listing_note": "Private Company",
            "display_size": 5,
            "source_status": "VERIFIED",
            "source_ids": ["S_NSCALE_B", "S_NSCALE_PREIPO", "S_WYFI_NSCALE"],
            "key_drivers": ["private_funding", "gpu_commitments"],
        },
        {
            "id": "nebius",
            "name": "Nebius",
            "name_ko": "네비우스",
            "group": "ai_infra",
            "sector": "AI 클라우드 · 인프라",
            "entity_type": "company",
            "role": "AI 클라우드 (구 Yandex 클라우드 계열)",
            "description": "Nasdaq NBIS. 자본집약·추가 조달 필요를 20-F에 명시. H1'26 현금·부채 비교치 큼.",
            "listed": True,
            "ticker": "NBIS",
            "exchange": "Nasdaq",
            "quote_currency": "USD",
            "listing_note": None,
            "display_size": 6,
            "source_status": "VERIFIED",
            "source_ids": ["S_NBIS_20F25", "S_ACIS_NBIS_IREN"],
            "key_drivers": ["external_funding", "capex"],
        },
        {
            "id": "soluna",
            "name": "Soluna Holdings",
            "name_ko": "솔루나",
            "group": "datacenter",
            "sector": "재생에너지 연동 데이터센터",
            "entity_type": "company",
            "role": "소규모 데이터센터 개발",
            "description": "2026.6.30 현금 $113.4M, 유동부채성 차입 $30.1M, LT debt $3.0M — 상대적 저레버리지.",
            "listed": True,
            "ticker": "SLNH",
            "exchange": "Nasdaq",
            "quote_currency": "USD",
            "listing_note": None,
            "display_size": 3,
            "source_status": "VERIFIED",
            "source_ids": ["S_SLNH_10Q2"],
            "key_drivers": ["liquidity"],
        },
        {
            "id": "hut8",
            "name": "Hut 8",
            "name_ko": "헛8",
            "group": "datacenter",
            "sector": "디지털 인프라 · AI 데이터센터",
            "entity_type": "company",
            "role": "프로젝트 파이낸스 (River Bend · Beacon Point)",
            "description": "River Bend $3.25B / Beacon Point $4.25B IG 선순위담보채(자회사). Fluidstack+Google 백스톱. 모회사 일반 소구 부채 축소.",
            "listed": True,
            "ticker": "HUT",
            "exchange": "Nasdaq",
            "quote_currency": "USD",
            "listing_note": None,
            "display_size": 5,
            "source_status": "VERIFIED",
            "source_ids": ["S_HUT_10Q2", "S_HUT_Q2_PR"],
            "key_drivers": ["project_finance", "nonrecourse"],
        },
        # SPVs
        {
            "id": "corz_finance_i",
            "name": "Core Scientific Finance I LLC",
            "name_ko": "코어사이언티픽 Finance I",
            "group": "project_finance",
            "sector": "프로젝트 파이낸스 SPV",
            "entity_type": "spv",
            "role": "CORZ HPC 자산 담보 발행체",
            "description": "$3.3B 7.750% senior secured notes due 2031. 자회사 보증. Core Scientific 모회사는 notes 미보증(완공보증만). CoreWeave 임차 자산 담보.",
            "listed": False,
            "ticker": None,
            "exchange": None,
            "quote_currency": None,
            "listing_note": "Project finance SPV (unlisted)",
            "display_size": 4,
            "source_status": "VERIFIED",
            "source_ids": ["S_CORZ_FINANCE_I", "S_CORZ"],
            "key_drivers": ["single_tenant", "secured_notes"],
        },
        {
            "id": "galaxy_helios_ii",
            "name": "Galaxy Helios Data Centers II LLC",
            "name_ko": "갤럭시 Helios II",
            "group": "project_finance",
            "sector": "프로젝트 파이낸스 SPV",
            "entity_type": "spv",
            "role": "Helios Phase II 발행체",
            "description": "Helios Phase II 단일자산 SPV. CoreWeave 15년 리스가 주요 신용지지. 모회사 완공보증 보고·notes 미보증(시장 보도).",
            "listed": False,
            "ticker": None,
            "exchange": None,
            "quote_currency": None,
            "listing_note": "Project finance SPV (unlisted)",
            "display_size": 4,
            "source_status": "INFERRED",
            "source_ids": ["S_GLXY_HELIOS_II_NOTES", "S_GLXY_10K25", "S_GLXY_HELIOS"],
            "key_drivers": ["single_tenant", "secured_notes"],
        },
    ]


def relationships() -> list[dict]:
    return [
        {
            "id": "d_corz_spv",
            "source": "core_scientific",
            "target": "corz_finance_i",
            "relationship_type": "PARENT_SPV",
            "impact_channel": "financial",
            "label": "Finance I 발행체 (완공보증 · notes 미보증)",
            "impact_label": "프로젝트 부채 · 모회사 비소구 notes",
            "source_status": "VERIFIED",
            "source_ids": ["S_CORZ_FINANCE_I"],
            "contract_ids": [],
            "amount_usd_m": 3300,
            "amount_note": "$3.3B 7.750% senior secured notes due 2031",
            "roles": [],
            "explanation": "모회사는 notes를 보증하지 않음. 완공보증만.",
            "commercial_ids": ["corz_finance_i_notes"],
        },
        {
            "id": "d_cw_corz_spv",
            "source": "coreweave",
            "target": "corz_finance_i",
            "relationship_type": "LESSOR",
            "impact_channel": "facility",
            "label": "임차 현금흐름 → SPV 담보",
            "impact_label": "임차료가 프로젝트 부채 상환 원천",
            "source_status": "VERIFIED",
            "source_ids": ["S_CORZ_FINANCE_I", "S_CORZ"],
            "contract_ids": [],
            "amount_usd_m": None,
            "amount_note": "CORZ–CW 임차 자산이 notes 담보",
            "roles": [],
            "explanation": "",
            "commercial_ids": ["corz_lease"],
        },
        {
            "id": "d_glxy_spv",
            "source": "galaxy_digital",
            "target": "galaxy_helios_ii",
            "relationship_type": "PARENT_SPV",
            "impact_channel": "financial",
            "label": "Helios II 발행체 (완공보증 보고)",
            "impact_label": "프로젝트 부채 · 모회사 비소구 notes",
            "source_status": "INFERRED",
            "source_ids": ["S_GLXY_HELIOS_II_NOTES"],
            "contract_ids": [],
            "amount_usd_m": 3500,
            "amount_note": "시장 보고 $3.5B 9.875% notes due 2031 — 인수확인은 Galaxy IR/indenture 대조",
            "roles": [],
            "explanation": "모회사 notes 미보증·완공보증만(시장 보도).",
            "commercial_ids": ["glxy_helios_ii_notes"],
        },
        {
            "id": "d_cw_glxy_spv",
            "source": "coreweave",
            "target": "galaxy_helios_ii",
            "relationship_type": "LESSOR",
            "impact_channel": "facility",
            "label": "Helios Phase II CoreWeave 리스",
            "impact_label": "임차료가 프로젝트 신용지지",
            "source_status": "INFERRED",
            "source_ids": ["S_GLXY_HELIOS_II_NOTES", "S_GLXY_10K25"],
            "contract_ids": [],
            "amount_usd_m": None,
            "amount_note": "Phase II critical IT ~260MW 보고",
            "roles": [],
            "explanation": "",
            "commercial_ids": ["glxy_helios_lease"],
        },
        {
            "id": "d_apld_macq",
            "source": "applied_digital",
            "target": "macquarie",
            "relationship_type": "INVESTOR",
            "impact_channel": "financial",
            "label": "MAM 우선주 시설 (최대 $5B)",
            "impact_label": "프로젝트 자본 파트너",
            "source_status": "VERIFIED",
            "source_ids": ["S_APLD_MACQ"],
            "contract_ids": [],
            "amount_usd_m": 5000,
            "amount_note": "시설 한도 최대 $5B · 최초 $112.5M 인출",
            "roles": [],
            "explanation": "Macquarie 엔티티가 네트워크에 없으면 관계는 보류되지 않음 — macquarie id 확인",
            "commercial_ids": [],
        },
        {
            "id": "d_wyfi_nscale",
            "source": "whitefiber",
            "target": "nscale",
            "relationship_type": "CUSTOMER",
            "impact_channel": "facility",
            "label": "NC-1 40MW 코로케이션 (~$865M)",
            "impact_label": "임차료 · 건설금융 담보",
            "source_status": "VERIFIED",
            "source_ids": ["S_WYFI_NSCALE"],
            "contract_ids": [],
            "amount_usd_m": 865,
            "amount_note": "10년 TCV ~$865M (전기 등 제외)",
            "roles": [],
            "explanation": "",
            "commercial_ids": ["wyfi_nscale_lease"],
        },
        {
            "id": "d_nscale_nvidia",
            "source": "nscale",
            "target": "nvidia",
            "relationship_type": "SUPPLIER",
            "impact_channel": "supply_chain",
            "label": "GPU · 전략 투자 (Series B / Pre-IPO)",
            "impact_label": "장비·자본 파트너",
            "source_status": "VERIFIED",
            "source_ids": ["S_NSCALE_B", "S_NSCALE_PREIPO"],
            "contract_ids": [],
            "amount_usd_m": None,
            "amount_note": "Pre-IPO convert 중 NVIDIA $1B 약정 트란치",
            "roles": [],
            "explanation": "",
            "commercial_ids": [],
        },
    ]


def contracts() -> list[dict]:
    return [
        {
            "id": "corz_finance_i_notes",
            "counterparty": "corz_finance_i",
            "kind": "lease",
            "title": "Core Scientific Finance I LLC $3.3B Senior Secured Notes due 2031",
            "signed": "2026-05-06",
            "value_usd_m": 3300,
            "value_basis": "액면 원금",
            "term_end": "2031",
            "term_note": "7.750% · 자회사 보증 · 모회사 notes 미보증 · 완공보증",
            "history": [],
            "detail": "담보: Issuer/Subsidiary Guarantor 자산 및 특정 Core Scientific 권리. CoreWeave 임차 HPC 사이트.",
            "remaining_note": "잔액 스케줄은 indenture 대조",
            "status": "VERIFIED",
            "source_ids": ["S_CORZ_FINANCE_I"],
        },
        {
            "id": "glxy_helios_ii_notes",
            "counterparty": "galaxy_helios_ii",
            "kind": "lease",
            "title": "Galaxy Helios Data Centers II LLC senior secured notes (reported)",
            "signed": "2026-07",
            "value_usd_m": 3500,
            "value_basis": "시장 보도 액면 — Galaxy IR/indenture로 확정 권장",
            "term_end": "2031",
            "term_note": "보고 쿠폰 9.875%",
            "history": [],
            "detail": "Phase II campus; CoreWeave lease credit support reported.",
            "remaining_note": "INFERRED pending primary indenture",
            "status": "INFERRED",
            "source_ids": ["S_GLXY_HELIOS_II_NOTES"],
        },
        {
            "id": "wyfi_nscale_lease",
            "counterparty": "nscale",
            "kind": "lease",
            "title": "WhiteFiber NC-1 Nscale 40MW colocation",
            "signed": "2025-12-18",
            "value_usd_m": 865,
            "value_basis": "임대인 기준 10년 TCV (전기 등 제외)",
            "term_end": None,
            "term_note": "10년 · 연 3% 에스컬레이터",
            "history": [],
            "detail": "2×20MW phases; RFS 목표 2026.4–5.",
            "remaining_note": "계약별 잔여 미공시",
            "status": "VERIFIED",
            "source_ids": ["S_WYFI_NSCALE"],
        },
    ]


def metric(mid, label, val, period, sids, note=None, status="VERIFIED"):
    m = {
        "id": mid,
        "label": label,
        "value_usd_m": val,
        "display": None if val is None else (f"${val:,.1f}M" if val < 1000 else f"${val/1000:.2f}B"),
        "period": period,
        "status": status,
        "source_ids": sids,
    }
    if note:
        m["note"] = note
    return m


def profiles() -> dict:
    return {
        "core_scientific": {
            "as_of": "2026-04-22",
            "period_label": "CW lease + Finance I notes",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": "USD",
            "unit": "USD million",
            "overview": "HDC colocation landlord to CoreWeave (~590MW / $10.2B disclosed). Finance I LLC issued $3.3B secured notes on CW-leased assets; parent provides completion guarantee but does not guarantee the notes.",
            "metrics": [
                metric("contract_backlog_cw", "CoreWeave landlord contract value", 10200, "2025-02", ["S_CORZ"]),
                metric("spv_notes", "Finance I notes principal", 3300, "2026-05", ["S_CORZ_FINANCE_I"]),
            ],
            "financing_notes": [
                "Parent does not guarantee Finance I notes — project-level stress ≠ automatic parent bankruptcy.",
                "Completion guarantee can still create contingent parent cash needs.",
            ],
            "risk_factors": ["CoreWeave tenant concentration", "Project/SPV secured debt"],
            "missing": ["Latest consolidated cash / total debt from 10-Q — enrich when filing parsed"],
            "source_ids": ["S_CORZ", "S_CORZ_FINANCE_I"],
        },
        "applied_digital": {
            "as_of": "2025-10-07",
            "period_label": "Polaris Forge / Macquarie",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": "USD",
            "unit": "USD million",
            "overview": "Ellendale Polaris Forge AI campuses leased in material part to CoreWeave. Macquarie preferred equity facility up to $5B; first draw $112.5M.",
            "metrics": [
                metric("cw_lease_expected", "CoreWeave Ellendale expected landlord revenue", 7000, "2025-06", ["S_APLD"], "Expected / not fully fixed"),
                metric("mam_facility", "Macquarie preferred facility ceiling", 5000, "2025-10", ["S_APLD_MACQ"]),
                metric("mam_first_draw", "Macquarie first draw", 112.5, "2025-10-07", ["S_APLD_MACQ"]),
            ],
            "financing_notes": [
                "Project finance + preferred equity reduce APLD equity contribution at Polaris Forge 1 (company statement).",
            ],
            "risk_factors": ["CoreWeave concentration", "Construction / project financing execution"],
            "missing": ["Latest consolidated cash and total debt"],
            "source_ids": ["S_APLD", "S_APLD_MACQ"],
        },
        "galaxy_digital": {
            "as_of": "2026-07-06",
            "period_label": "Helios / CoreWeave",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": "USD",
            "unit": "USD million",
            "overview": "Helios campus 526MW critical IT leased to CoreWeave (15y). Data Centers segment is CW-anchored. Helios II SPV financing reported separately from parent.",
            "metrics": [
                metric("helios_mw", "Helios CW critical IT MW", 526, "2026", ["S_GLXY_10K25", "S_GLXY_HELIOS"], "MW not USD"),
            ],
            "financing_notes": [
                "Parent diversified (digital assets + data centers). SPV notes reported as non-recourse to parent notes guarantee.",
            ],
            "risk_factors": ["Single-tenant Helios exposure", "Project financing coupon sensitive to tenant credit"],
            "missing": ["Primary Helios II indenture confirmation", "Consolidated cash/debt snapshot"],
            "source_ids": ["S_GLXY_10K25", "S_GLXY_HELIOS", "S_GLXY_HELIOS_II_NOTES"],
        },
        "cipher_digital": {
            "as_of": "2026-03-31",
            "period_label": "Q1 2026 10-Q (+ Q2 debt tables)",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": "USD",
            "unit": "USD million",
            "overview": "HPC hosting developer (ex-Cipher Mining). Large secured notes and convertibles funding Barber Lake / Black Pearl. Revolver $200M undrawn with liquidity covenant.",
            "metrics": [
                metric("cash", "Cash and cash equivalents", 715.2, "2026-03-31", ["S_CIFR_10Q1"]),
                metric("total_debt_principal", "Debt principal (approx., Q2 tables)", 5200, "2026-06", ["S_CIFR_10Q2"], "Order-of-magnitude from principal tables — confirm exact line", "INFERRED"),
            ],
            "financing_notes": [
                "Tenants include Fluidstack and a hyperscaler (company disclosures) — not CoreWeave-centric.",
                "Restricted cash for project builds is not unrestricted liquidity.",
            ],
            "risk_factors": ["High leverage", "Construction funding", "Sector financing conditions"],
            "missing": ["Exact consolidated interest expense / OCF for stress ratio"],
            "source_ids": ["S_CIFR_10Q1", "S_CIFR_10Q2"],
        },
        "whitefiber": {
            "as_of": "2025-12-31",
            "period_label": "FY2025 results + Jan 2026 converts",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": "USD",
            "unit": "USD million",
            "overview": "AI colo/cloud. Nscale NC-1 anchor. YE2025 no funded debt; Jan 2026 $230M 4.5% converts due 2031.",
            "metrics": [
                metric("cash", "Cash and cash equivalents", 114.4, "2025-12-31", ["S_WYFI_FY25"]),
                metric("funded_debt_ye", "Funded debt", 0, "2025-12-31", ["S_WYFI_FY25"]),
                metric("converts_2031", "4.5% converts due 2031", 230, "2026-01", ["S_WYFI_FY25"]),
                metric("nscale_tcv", "Nscale NC-1 TCV", 865, "2025-12", ["S_WYFI_NSCALE"]),
            ],
            "financing_notes": ["Construction facility for NC-1 contemplated; not assumed drawn without disclosure."],
            "risk_factors": ["Construction financing", "Tenant concentration (Nscale)"],
            "missing": ["2026 mid-year cash after convert proceeds"],
            "source_ids": ["S_WYFI_FY25", "S_WYFI_NSCALE"],
        },
        "terawulf": {
            "as_of": "2026-06-30",
            "period_label": "Q2 2026 10-Q",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": "USD",
            "unit": "USD million",
            "overview": "HPC leasing to Fluidstack with Google credit support. Large cash and convertible/secured stack.",
            "metrics": [
                metric("cash", "Cash and cash equivalents", 2619.2, "2026-06-30", ["S_WULF_10Q2"]),
                metric("long_term_debt", "Long-term debt", 3019.3, "2026-06-30", ["S_WULF_10Q2"]),
                metric("st_converts", "Short-term convertible notes", 1102.0, "2026-06-30", ["S_WULF_10Q2"]),
            ],
            "financing_notes": ["Primary disclosed HPC counterparty is Fluidstack/Google-supported — not CoreWeave."],
            "risk_factors": ["Convertible classification / dilution", "Ongoing project funding"],
            "missing": ["OCF / interest coverage detail for ratio stress"],
            "source_ids": ["S_WULF_10Q2"],
        },
        "iren": {
            "as_of": "2026-06-30",
            "period_label": "FY26 / H1 2026 comps",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": "USD",
            "unit": "USD million",
            "overview": "AI Cloud ramp with GPU financings and customer prepayments. Large cash and debt balances.",
            "metrics": [
                metric("cash", "Cash and cash equivalents", 5895.6, "2026-06-30", ["S_ACIS_NBIS_IREN"], "Research synthesis of filings"),
                metric("debt_ex_leases", "Debt carrying excl. leases", 7592.9, "2026-06-30", ["S_ACIS_NBIS_IREN"], "Research synthesis"),
                metric("ocf_h1", "Operating cash flow H1 2026", 1886.4, "H1 2026", ["S_ACIS_NBIS_IREN"]),
                metric("capex_h1", "Cash capex H1 2026", 3333.4, "H1 2026", ["S_ACIS_NBIS_IREN"]),
            ],
            "financing_notes": ["GPU financing commitments ≠ fully funded debt."],
            "risk_factors": ["External funding dependence", "Capex vs OCF gap"],
            "missing": ["Instrument-level floating share"],
            "source_ids": ["S_IREN_FY26", "S_ACIS_NBIS_IREN"],
        },
        "nebius": {
            "as_of": "2026-06-30",
            "period_label": "H1 2026 comps + 20-F risk",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": "USD",
            "unit": "USD million",
            "overview": "Capital-intensive AI infra; 20-F states growth depends on additional equity/debt. Large cash and convert stack.",
            "metrics": [
                metric("cash", "Cash and cash equivalents", 8042.1, "2026-06-30", ["S_ACIS_NBIS_IREN"], "Research synthesis"),
                metric("debt_ex_leases", "Debt carrying excl. leases", 8545.7, "2026-06-30", ["S_ACIS_NBIS_IREN"]),
                metric("ocf_h1", "Operating cash flow H1 2026", 4504.1, "H1 2026", ["S_ACIS_NBIS_IREN"]),
                metric("capex_h1", "Cash capex H1 2026", 8130.3, "H1 2026", ["S_ACIS_NBIS_IREN"]),
            ],
            "financing_notes": ["Deferred revenue / prepayments material to liquidity (research note)."],
            "risk_factors": ["External financing needed", "Capex intensity"],
            "missing": ["Instrument-level coupons / floating share"],
            "source_ids": ["S_NBIS_20F25", "S_ACIS_NBIS_IREN"],
        },
        "nscale": {
            "as_of": "2026-09-25",
            "period_label": "Private company — funding announcements only",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": None,
            "unit": "USD million",
            "overview": "Private AI infrastructure provider. Series B $1.1B and Pre-IPO convert $3.36B announced. No public consolidated financial statements suitable for quantitative distress scoring.",
            "metrics": [
                metric("series_b", "Series B raise", 1100, "2025-09", ["S_NSCALE_B"]),
                metric("preipo_convert", "Pre-IPO convertible financing", 3360, "2026-09", ["S_NSCALE_PREIPO"]),
            ],
            "financing_notes": ["Quantitative liquidity/debt service stress = unverified."],
            "risk_factors": ["Private disclosure gap", "GPU procurement commitments"],
            "missing": ["Cash", "Total debt", "OCF", "Interest expense"],
            "source_ids": ["S_NSCALE_B", "S_NSCALE_PREIPO", "S_WYFI_NSCALE"],
        },
        "soluna": {
            "as_of": "2026-06-30",
            "period_label": "Q2 2026 10-Q",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": "USD",
            "unit": "USD million",
            "overview": "Smaller renewable-linked data center developer. Relatively low leverage vs cash.",
            "metrics": [
                metric("cash", "Cash", 113.4, "2026-06-30", ["S_SLNH_10Q2"]),
                metric("current_debt", "Current portion of debt", 30.1, "2026-06-30", ["S_SLNH_10Q2"]),
                metric("long_term_debt", "Long-term debt", 3.0, "2026-06-30", ["S_SLNH_10Q2"]),
            ],
            "financing_notes": ["No CoreWeave relationship identified in project data."],
            "risk_factors": ["Scale / access to capital markets"],
            "missing": ["Major AI tenant concentration"],
            "source_ids": ["S_SLNH_10Q2"],
        },
        "hut8": {
            "as_of": "2026-06-30",
            "period_label": "Q2 2026 10-Q / earnings",
            "currency": "USD",
            "reporting_currency": "USD",
            "listing_currency": "USD",
            "unit": "USD million",
            "overview": "IG project notes at Hut 8 DC subsidiaries (River Bend / Beacon Point) leased to Fluidstack with Google financial backstop. Parent reports strong liquidity and reduced general recourse debt.",
            "metrics": [
                metric("project_notes_river_bend", "River Bend notes principal", 3250, "2026-04-30", ["S_HUT_10Q2"]),
                metric("project_notes_beacon", "Beacon Point notes principal", 4250, "2026-06-09", ["S_HUT_10Q2"]),
                metric("debt_carrying", "Loans/notes carrying amount", 7638.4, "2026-06-30", ["S_HUT_10Q2"]),
                metric("liquidity_incl_btc", "Unrestricted cash+restricted+BTC (reported)", 8100, "2026-06-30", ["S_HUT_Q2_PR"], "Includes BTC — not all cash"),
            ],
            "financing_notes": [
                "Project notes are non-recourse to Hut 8 Corp. per company disclosures.",
                "Google backstop on Fluidstack rent — resilient to CoreWeave-specific default.",
            ],
            "risk_factors": ["Phase 2 financing needs", "BTC mark-to-market in liquidity figure"],
            "missing": ["Exact unrestricted cash excluding BTC"],
            "source_ids": ["S_HUT_10Q2", "S_HUT_Q2_PR"],
        },
        "corz_finance_i": {
            "as_of": "2026-05-06",
            "period_label": "Notes pricing",
            "currency": "USD",
            "reporting_currency": "USD",
            "overview": "SPV issuer of $3.3B secured notes backed by CoreWeave-leased HPC sites. Parent completion guarantee only.",
            "metrics": [
                metric("notes_principal", "Senior secured notes", 3300, "2026-05", ["S_CORZ_FINANCE_I"]),
            ],
            "financing_notes": ["Non-recourse notes to Core Scientific parent (no notes guarantee)."],
            "risk_factors": ["Single-tenant cash flow (CoreWeave)", "Construction completion"],
            "missing": ["DSRA balances", "Covenant tests"],
            "source_ids": ["S_CORZ_FINANCE_I"],
        },
        "galaxy_helios_ii": {
            "as_of": "2026-07",
            "period_label": "Reported Helios II financing",
            "currency": "USD",
            "reporting_currency": "USD",
            "overview": "Reported single-asset Helios Phase II financing vehicle with CoreWeave lease credit support.",
            "metrics": [
                metric("notes_principal", "Senior secured notes (reported)", 3500, "2026-07", ["S_GLXY_HELIOS_II_NOTES"], status="INFERRED"),
            ],
            "financing_notes": ["Primary indenture confirmation recommended — status INFERRED."],
            "risk_factors": ["CoreWeave tenant credit", "Construction timing"],
            "missing": ["Indenture primary source", "DSRA"],
            "source_ids": ["S_GLXY_HELIOS_II_NOTES"],
        },
    }


# Sector stress inputs consumed by engines (USD millions). Explicit assumptions documented.
SECTOR_STRESS = {
    "meta": {
        "as_of": "2026-10-20",
        "note": "Inputs for sector-wide financing contagion. Missing fields are null — never invented.",
        "disclaimer": "Analytical scenario inputs, not bankruptcy probabilities.",
    },
    "entities": {
        "cipher_digital": {
            "cash_usd_m": 715.2,
            "total_debt_usd_m": 5200,
            "floating_debt_usd_m": 50,
            "near_term_debt_usd_m": 200,
            "annual_capex_need_usd_m": 2000,
            "funding_dependence": "high",
            "cw_direct": False,
            "resilience": "levered_builder",
            "data_quality": "partial",
            "source_ids": ["S_CIFR_10Q1", "S_CIFR_10Q2"],
        },
        "whitefiber": {
            "cash_usd_m": 114.4,
            "total_debt_usd_m": 230,
            "floating_debt_usd_m": 0,
            "near_term_debt_usd_m": 0,
            "annual_capex_need_usd_m": 400,
            "funding_dependence": "high",
            "cw_direct": False,
            "resilience": "early_stage",
            "data_quality": "partial",
            "source_ids": ["S_WYFI_FY25"],
        },
        "terawulf": {
            "cash_usd_m": 2619.2,
            "total_debt_usd_m": 4121.3,
            "floating_debt_usd_m": 0,
            "near_term_debt_usd_m": 1102.0,
            "annual_capex_need_usd_m": 1500,
            "funding_dependence": "medium",
            "cw_direct": False,
            "resilience": "cash_rich_levered",
            "data_quality": "good",
            "source_ids": ["S_WULF_10Q2"],
        },
        "iren": {
            "cash_usd_m": 5895.6,
            "total_debt_usd_m": 7592.9,
            "floating_debt_usd_m": 0,
            "near_term_debt_usd_m": 169.4,
            "annual_capex_need_usd_m": 6666,
            "funding_dependence": "high",
            "cw_direct": False,
            "resilience": "cash_rich_capex",
            "data_quality": "research_synth",
            "source_ids": ["S_ACIS_NBIS_IREN", "S_IREN_FY26"],
        },
        "nebius": {
            "cash_usd_m": 8042.1,
            "total_debt_usd_m": 8545.7,
            "floating_debt_usd_m": 0,
            "near_term_debt_usd_m": 46.7,
            "annual_capex_need_usd_m": 16260,
            "funding_dependence": "high",
            "cw_direct": False,
            "resilience": "cash_rich_capex",
            "data_quality": "research_synth",
            "source_ids": ["S_ACIS_NBIS_IREN", "S_NBIS_20F25"],
        },
        "nscale": {
            "cash_usd_m": None,
            "total_debt_usd_m": None,
            "floating_debt_usd_m": None,
            "near_term_debt_usd_m": None,
            "annual_capex_need_usd_m": None,
            "funding_dependence": "unknown",
            "cw_direct": False,
            "resilience": "insufficient_data",
            "data_quality": "insufficient",
            "source_ids": ["S_NSCALE_B", "S_NSCALE_PREIPO"],
        },
        "soluna": {
            "cash_usd_m": 113.4,
            "total_debt_usd_m": 33.1,
            "floating_debt_usd_m": 0,
            "near_term_debt_usd_m": 30.1,
            "annual_capex_need_usd_m": 80,
            "funding_dependence": "low",
            "cw_direct": False,
            "resilience": "low_leverage",
            "data_quality": "good",
            "source_ids": ["S_SLNH_10Q2"],
        },
        "hut8": {
            "cash_usd_m": 7600,
            "total_debt_usd_m": 7638.4,
            "floating_debt_usd_m": 0,
            "near_term_debt_usd_m": 234.7,
            "annual_capex_need_usd_m": 1000,
            "funding_dependence": "medium",
            "cw_direct": False,
            "resilience": "ig_project_google_backstop",
            "data_quality": "good",
            "source_ids": ["S_HUT_10Q2", "S_HUT_Q2_PR"],
            "notes": "cash approx from liquidity ex-BTC attribution; project debt mostly non-recourse",
        },
        "corz_finance_i": {
            "cash_usd_m": None,
            "total_debt_usd_m": 3300,
            "floating_debt_usd_m": 0,
            "near_term_debt_usd_m": 0,
            "annual_capex_need_usd_m": None,
            "funding_dependence": "tenant",
            "cw_direct": True,
            "resilience": "spv_single_tenant",
            "data_quality": "good",
            "parent_id": "core_scientific",
            "source_ids": ["S_CORZ_FINANCE_I"],
        },
        "galaxy_helios_ii": {
            "cash_usd_m": None,
            "total_debt_usd_m": 3500,
            "floating_debt_usd_m": 0,
            "near_term_debt_usd_m": 0,
            "annual_capex_need_usd_m": None,
            "funding_dependence": "tenant",
            "cw_direct": True,
            "resilience": "spv_single_tenant",
            "data_quality": "inferred",
            "parent_id": "galaxy_digital",
            "source_ids": ["S_GLXY_HELIOS_II_NOTES"],
        },
    },
}


def main() -> None:
    src = load("sources.json")
    for s in SOURCES:
        upsert_source(src, s)
    save("sources.json", src)

    ent = load("entities.json")
    # enrich existing Group A
    for eid, role, desc, sids in [
        ("core_scientific", "데이터센터 임대인 (약 590MW) · Finance I SPV",
         "CoreWeave 대상 ~590MW/$10.2B. 자회사 Core Scientific Finance I LLC가 $3.3B 담보사채 발행(모회사 notes 미보증·완공보증).",
         ["S_CORZ", "S_CORZ_FINANCE_I"]),
        ("applied_digital", "데이터센터 임대인 · Polaris Forge / Macquarie",
         "Ellendale 등 CoreWeave 임차. Macquarie 우선주 시설 최대 $5B(최초 $112.5M).",
         ["S_APLD", "S_APLD_MACQ"]),
        ("galaxy_digital", "Helios 캠퍼스 임대인 (526MW · CoreWeave)",
         "Helios 526MW critical IT to CoreWeave. Helios II SPV 프로젝트 금융(보고).",
         ["S_GLXY_10K25", "S_GLXY_HELIOS", "S_GLXY_HELIOS_II_NOTES"]),
    ]:
        for e in ent["entities"]:
            if e["id"] == eid:
                e["role"] = role
                e["description"] = desc
                e["source_ids"] = sorted(set(e.get("source_ids") or []) | set(sids))

    after = "galaxy_digital"
    for e in entities():
        upsert_entity(ent, e, after=after)
        after = e["id"]
    save("entities.json", ent)

    # macquarie entity check for APLD edge
    eids = {e["id"] for e in ent["entities"]}
    rel = load("relationships.json")
    for r in relationships():
        if r["id"] == "d_apld_macq" and "macquarie" not in eids:
            # find blackstone-like — skip edge if no macquarie node; use note only
            print("skip d_apld_macq — macquarie entity absent")
            continue
        upsert_rel(rel, r, after="d_glxy" if r["id"] == "d_corz_spv" else None)
    save("relationships.json", rel)

    con = load("contracts.json")
    for c in contracts():
        upsert_contract(con, c)
    # update apld lease note for Polaris
    for c in con["contracts"]:
        if c["id"] == "apld_lease":
            c["detail"] = (c.get("detail") or "") + " Polaris Forge / Macquarie preferred equity partnership disclosed separately."
            c["source_ids"] = sorted(set(c.get("source_ids") or []) | {"S_APLD_MACQ"})
    save("contracts.json", con)

    prof = load("profiles.json")
    for k, v in profiles().items():
        prof["profiles"][k] = v
    save("profiles.json", prof)

    save("sector_stress.json", SECTOR_STRESS)
    print("entities", len(ent["entities"]), "relationships", len(rel["relationships"]), "profiles", len(prof["profiles"]))
    print("OK")


if __name__ == "__main__":
    main()
