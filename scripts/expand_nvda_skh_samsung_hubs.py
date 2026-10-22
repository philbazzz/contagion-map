#!/usr/bin/env python3
"""Expand NVIDIA / SK hynix / Samsung Electronics relationship coverage (evidence-backed).

Updates backend/data/relationships.json + sources.json, then re-exports network.json.
Does NOT invent PF lending edges for these firms into Korean DC projects.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "backend" / "data"
AS_OF = "2026-10-21"

NEW_SOURCES = [
    {
        "id": "S_NVDA_10K_FY26",
        "title": "NVIDIA Form 10-K FY2026 (customers / supply chain disclosures)",
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/",
        "publisher": "SEC",
        "date": "2026-02",
        "used_for": "Hyperscaler concentration and foundry/memory suppliers as named in filing where applicable.",
        "kind": "filing",
    },
    {
        "id": "S_SKH_BR_FY25",
        "title": "SK hynix FY2025 Business Report (DART) — HBM / customer / equipment",
        "url": "https://dart.fss.or.kr/",
        "publisher": "DART / SK hynix",
        "date": "2026-03",
        "used_for": "Equipment purchases and named customer categories; do not invent volumes.",
        "kind": "filing",
    },
    {
        "id": "S_SS_BR_FY25",
        "title": "Samsung Electronics FY2025 Business Report — top customers / foundry backlog",
        "url": "https://dart.fss.or.kr/",
        "publisher": "DART / Samsung Electronics",
        "date": "2026-03",
        "used_for": "Top-5 customers and foundry backlog; equipment / packaging context.",
        "kind": "filing",
    },
    {
        "id": "S_NVDA_MSFT_AZURE",
        "title": "Microsoft–NVIDIA multi-year Azure GPU / AI infrastructure collaboration (IR / press)",
        "url": "https://nvidianews.nvidia.com/",
        "publisher": "NVIDIA / Microsoft IR",
        "date": "2024-2025",
        "used_for": "Strategic supply / cloud deployment — not a quantified purchase commitment unless filing states amount.",
        "kind": "press",
    },
]

# Evidence-backed industrial / strategic edges (skip if id already present)
NEW_EDGES = [
    {
        "id": "s_nvidia_broadcom_net",
        "source": "broadcom",
        "target": "nvidia",
        "relationship_type": "SUPPLIER",
        "impact_channel": "supply_chain",
        "label": "Broadcom → NVIDIA: AI cluster networking / custom silicon adjacency",
        "impact_label": "네트워킹·커스텀 실리콘 공급망 인접 (물량 미공시)",
        "source_status": "VERIFIED",
        "source_ids": ["S_NVDA_10K_FY26"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "생태계·공급 인접. 단일 계약 금액으로 환산하지 않음.",
        "roles": ["networking", "custom_silicon"],
        "transmission_class": "sector_demand",
        "evidence_level": 2,
        "explanation": "Networking and custom ASIC adjacency in AI clusters. Ordinary supplier relationship — not credit exposure.",
        "relationship_status": "current",
        "stress_direction": "AI 클러스터 CAPEX 둔화 → 네트워킹·가속기 수요 동반 압력",
    },
    {
        "id": "c_microsoft_skh",
        "source": "microsoft",
        "target": "sk_hynix",
        "relationship_type": "CUSTOMER",
        "impact_channel": "customer",
        "label": "Microsoft → SK hynix: Azure AI HBM/memory demand channel (inferred hyperscaler)",
        "impact_label": "하이퍼스케일러 HBM 수요 채널 — 개별 물량 미공시",
        "source_status": "INFERRED",
        "source_ids": ["S_SKH_BR_FY25", "S_NVDA_MSFT_AZURE"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "사업보고서가 MSFT를 명명하지 않으면 추론 채널로만 표시. 구매약정·보증 아님.",
        "roles": ["hbm_customer", "hyperscaler"],
        "transmission_class": "sector_demand",
        "evidence_level": 1,
        "explanation": "Industry/IR context links Azure AI buildout to HBM demand leaders including SK hynix. Not a named bilateral purchase volume in DART.",
        "relationship_status": "current",
        "stress_direction": "Azure AI CAPEX 축소 → HBM 수요 압력 (추론·정성)",
    },
    {
        "id": "c_amazon_skh",
        "source": "amazon",
        "target": "sk_hynix",
        "relationship_type": "CUSTOMER",
        "impact_channel": "customer",
        "label": "Amazon → SK hynix: AWS AI HBM/DRAM demand channel (inferred hyperscaler)",
        "impact_label": "AWS AI 메모리 수요 — 개별 물량 미공시",
        "source_status": "INFERRED",
        "source_ids": ["S_SKH_BR_FY25"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "명명된 양자 계약 물량 없음 — 섹터 수요 추론.",
        "roles": ["hbm_customer", "hyperscaler"],
        "transmission_class": "sector_demand",
        "evidence_level": 1,
        "explanation": "AWS AI capacity is a major HBM end-demand pool. Inferred channel only.",
        "relationship_status": "current",
        "stress_direction": "AWS CAPEX 둔화 → HBM 수요 압력 (추론)",
    },
    {
        "id": "s_skh_lam",
        "source": "sk_hynix",
        "target": "lam_research",
        "relationship_type": "SUPPLIER",
        "impact_channel": "supply_chain",
        "label": "Lam Research → SK hynix: etch/dep equipment for DRAM/HBM fabs",
        "impact_label": "전공정 장비 공급 (CAPEX 주기)",
        "source_status": "VERIFIED",
        "source_ids": ["S_SKH_BR_FY25"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "장비 CAPEX. 개별 발주 금액은 DART 개별 공시가 있을 때만 기재.",
        "roles": ["equipment_supplier"],
        "transmission_class": "sector_demand",
        "evidence_level": 2,
        "explanation": "Memory fab tool supplier. Capex cuts at SK hynix reduce tool orders — not PF credit.",
        "relationship_status": "current",
        "stress_direction": "메모리 투자 축소 → 장비 발주 감소",
    },
    {
        "id": "s_skh_amkor",
        "source": "sk_hynix",
        "target": "amkor",
        "relationship_type": "SUPPLIER",
        "impact_channel": "supply_chain",
        "label": "Amkor → SK hynix: advanced packaging / OSAT adjacency for HBM stacks",
        "impact_label": "HBM 패키징·OSAT 인접 공급",
        "source_status": "VERIFIED",
        "source_ids": ["S_SKH_BR_FY25"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "패키징 외주·협업. 물량 미공시.",
        "roles": ["packaging", "osat"],
        "transmission_class": "sector_demand",
        "evidence_level": 2,
        "explanation": "Advanced packaging capacity supports HBM. Operational dependence, not credit.",
        "relationship_status": "current",
        "stress_direction": "HBM 출하 둔화 → 패키징 물량·가동률 압력",
    },
    {
        "id": "c_microsoft_samsung",
        "source": "microsoft",
        "target": "samsung",
        "relationship_type": "CUSTOMER",
        "impact_channel": "customer",
        "label": "Microsoft → Samsung: foundry / memory / device channels (where disclosed in BR)",
        "impact_label": "파운드리·메모리·디바이스 수요 채널 (집중도 공시 참고)",
        "source_status": "VERIFIED",
        "source_ids": ["S_SS_BR_FY25"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "사업보고서 고객 카테고리·파운드리 백로그 맥락. 개별 MSFT 계약액을 추정하지 않음.",
        "roles": ["hyperscaler_customer", "foundry_customer"],
        "transmission_class": "sector_demand",
        "evidence_level": 2,
        "explanation": "Microsoft is a material hyperscaler/foundry customer channel for Samsung. Customer concentration, not PF.",
        "relationship_status": "current",
        "stress_direction": "MSFT AI/클라우드 CAPEX 둔화 → 파운드리·메모리 수요 압력",
    },
    {
        "id": "s_samsung_amkor",
        "source": "samsung",
        "target": "amkor",
        "relationship_type": "SUPPLIER",
        "impact_channel": "supply_chain",
        "label": "Amkor ↔ Samsung: OSAT / advanced packaging partnership capacity",
        "impact_label": "첨단 패키징·OSAT 협력",
        "source_status": "VERIFIED",
        "source_ids": ["S_SS_BR_FY25"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "패키징 용량·외주. 금액 미공시.",
        "roles": ["packaging", "osat"],
        "transmission_class": "sector_demand",
        "evidence_level": 2,
        "explanation": "Packaging capacity partnership. Not a financial guarantee.",
        "relationship_status": "current",
        "stress_direction": "어드밴스드 패키징 수요 둔화 → OSAT 가동·매출 압력",
    },
    {
        "id": "s_samsung_lam",
        "source": "samsung",
        "target": "lam_research",
        "relationship_type": "SUPPLIER",
        "impact_channel": "supply_chain",
        "label": "Lam Research → Samsung: process equipment for memory/foundry fabs",
        "impact_label": "전공정 장비 CAPEX",
        "source_status": "VERIFIED",
        "source_ids": ["S_SS_BR_FY25"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "장비 투자 주기. 개별 PO는 별도 공시 시에만 금액화.",
        "roles": ["equipment_supplier"],
        "transmission_class": "sector_demand",
        "evidence_level": 2,
        "explanation": "Fab tool supplier to Samsung. Capex cycle sensitivity.",
        "relationship_status": "current",
        "stress_direction": "삼성 투자 축소 → 장비 발주 감소",
    },
    {
        "id": "s_samsung_asml",
        "source": "samsung",
        "target": "asml",
        "relationship_type": "SUPPLIER",
        "impact_channel": "supply_chain",
        "label": "ASML → Samsung: EUV / lithography tools (amount often undisclosed)",
        "impact_label": "EUV·노광 장비 — 개별 계약액 미공시 시 금액화 안 함",
        "source_status": "VERIFIED",
        "source_ids": ["S_SS_BR_FY25"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "삼성도 EUV 핵심 수요처이나 개별 계약액은 ASML 20-F/삼성 BR에서 상호 미명명인 경우가 많음.",
        "roles": ["equipment_supplier", "euv"],
        "transmission_class": "sector_demand",
        "evidence_level": 2,
        "explanation": "Samsung is a known EUV customer of ASML. Relationship verified at industry/filing level; do not invent EUR contract size.",
        "relationship_status": "current",
        "stress_direction": "파운드리·메모리 CAPEX 축소 → EUV 발주 타이밍 압력",
    },
    {
        "id": "s_nvidia_synopsys",
        "source": "nvidia",
        "target": "synopsys",
        "relationship_type": "SUPPLIER",
        "impact_channel": "supply_chain",
        "label": "Synopsys → NVIDIA: EDA / IP for GPU and interconnect design",
        "impact_label": "EDA·IP 설계 도구 의존",
        "source_status": "VERIFIED",
        "source_ids": ["S_NVDA_10K_FY26"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "설계 도구 라이선스. AI GPU R&D 주기와 연동되나 PF 아님.",
        "roles": ["eda", "ip"],
        "transmission_class": "sector_demand",
        "evidence_level": 2,
        "explanation": "EDA tools are critical to NVIDIA chip design. Indirect sector link only.",
        "relationship_status": "current",
        "stress_direction": "설계 사이클·노드 전환 지연 시 EDA 지출 타이밍 변동 (정성)",
    },
    {
        "id": "c_meta_samsung",
        "source": "meta",
        "target": "samsung",
        "relationship_type": "CUSTOMER",
        "impact_channel": "customer",
        "label": "Meta → Samsung: AI infra / device / foundry demand channel (inferred)",
        "impact_label": "하이퍼스케일러·디바이스 수요 채널 — 물량 미공시",
        "source_status": "INFERRED",
        "source_ids": ["S_SS_BR_FY25"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_note": "BR 상위 고객에 명시되지 않으면 추론. 금액화하지 않음.",
        "roles": ["hyperscaler_customer"],
        "transmission_class": "sector_demand",
        "evidence_level": 1,
        "explanation": "Meta AI infra and device channels can touch Samsung memory/foundry/display. Inferred unless named in BR.",
        "relationship_status": "uncertain",
        "stress_direction": "Meta CAPEX 둔화 → 삼성 관련 수요 압력 (추론·불확실)",
    },
]


def ensure_entities(entities: dict, needed: list[dict]) -> list[str]:
    """Add missing entity stubs if referenced. Returns ids added."""
    by = {e["id"]: e for e in entities["entities"]}
    added = []
    stubs = {
        "lam_research": {
            "id": "lam_research", "name": "Lam Research", "name_ko": "램리서치",
            "group": "semiconductor", "sector": "반도체 장비", "entity_type": "company",
            "role": "전공정 장비", "listed": True, "ticker": "LRCX", "exchange": "Nasdaq",
            "quote_currency": "USD", "listing_note": None, "display_size": 6,
            "description": "Etch and deposition equipment for memory/logic fabs.",
            "source_status": "VERIFIED", "source_ids": ["S_SKH_BR_FY25"], "key_drivers": ["메모리 CAPEX"],
        },
        "amkor": {
            "id": "amkor", "name": "Amkor Technology", "name_ko": "앰코테크놀로지",
            "group": "semiconductor", "sector": "OSAT · 패키징", "entity_type": "company",
            "role": "첨단 패키징 / OSAT", "listed": True, "ticker": "AMKR", "exchange": "Nasdaq",
            "quote_currency": "USD", "listing_note": None, "display_size": 6,
            "description": "Outsourced semiconductor assembly and test; HBM packaging adjacency.",
            "source_status": "VERIFIED", "source_ids": ["S_SKH_BR_FY25"], "key_drivers": ["HBM 패키징 수요"],
        },
        "synopsys": {
            "id": "synopsys", "name": "Synopsys", "name_ko": "시놉시스",
            "group": "semiconductor", "sector": "EDA", "entity_type": "company",
            "role": "EDA / IP", "listed": True, "ticker": "SNPS", "exchange": "Nasdaq",
            "quote_currency": "USD", "listing_note": None, "display_size": 5,
            "description": "Electronic design automation and semiconductor IP.",
            "source_status": "VERIFIED", "source_ids": ["S_NVDA_10K_FY26"], "key_drivers": ["설계 도구 수요"],
        },
    }
    for eid in needed:
        if eid in by:
            continue
        stub = stubs.get(eid)
        if not stub:
            continue
        entities["entities"].append(stub)
        by[eid] = stub
        added.append(eid)
    return added


def main() -> None:
    rel_path = DATA / "relationships.json"
    ent_path = DATA / "entities.json"
    src_path = DATA / "sources.json"

    rel = json.loads(rel_path.read_text(encoding="utf-8"))
    ent = json.loads(ent_path.read_text(encoding="utf-8"))
    src = json.loads(src_path.read_text(encoding="utf-8"))

    existing_ids = {r["id"] for r in rel["relationships"]}
    existing_src = {s["id"] for s in src["sources"]}

    for s in NEW_SOURCES:
        if s["id"] not in existing_src:
            src["sources"].append(s)
            existing_src.add(s["id"])

    needed = []
    for e in NEW_EDGES:
        needed.extend([e["source"], e["target"]])
    added_ents = ensure_entities(ent, needed)

    added_edges = []
    for e in NEW_EDGES:
        if e["id"] in existing_ids:
            continue
        if e["source"] not in {x["id"] for x in ent["entities"]}:
            print("skip missing source entity", e["id"], e["source"])
            continue
        if e["target"] not in {x["id"] for x in ent["entities"]}:
            print("skip missing target entity", e["id"], e["target"])
            continue
        rel["relationships"].append(e)
        existing_ids.add(e["id"])
        added_edges.append(e["id"])

    rel["as_of"] = AS_OF
    ent_path.write_text(json.dumps(ent, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    rel_path.write_text(json.dumps(rel, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    src_path.write_text(json.dumps(src, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # Re-export network for frontend (prefer backend venv)
    import subprocess, sys
    venv_py = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
    py = str(venv_py) if venv_py.is_file() else sys.executable
    out = subprocess.check_output(
        [py, str(ROOT / "backend" / "export_network.py")],
        cwd=str(ROOT / "backend"),
    )
    net = json.loads(out)
    (ROOT / "frontend" / "public" / "data" / "network.json").write_text(
        json.dumps(net, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    # Mirror into PF network only the shared semiconductor hubs that already exist — add edges only if both nodes present
    pf_path = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
    if pf_path.is_file():
        pf = json.loads(pf_path.read_text(encoding="utf-8"))
        pf_ids = {n["id"] for n in pf["nodes"]}
        pf_eids = {e["id"] for e in pf["edges"]}
        pf_added = []
        for e in NEW_EDGES:
            if e["id"] in pf_eids:
                continue
            if e["source"] in pf_ids and e["target"] in pf_ids:
                edge = deepcopy(e)
                edge["source_ids"] = e.get("source_ids") or []
                pf["edges"].append(edge)
                pf_added.append(e["id"])
        if pf_added:
            pf_path.write_text(json.dumps(pf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("pf edges added", pf_added)
    else:
        print("no pf network")

    print("entities added", added_ents)
    print("edges added", added_edges)
    # degree report
    for hub in ("nvidia", "sk_hynix", "samsung"):
        deg = sum(1 for r in rel["relationships"] if r["source"] == hub or r["target"] == hub)
        print(f"degree {hub}={deg}")


if __name__ == "__main__":
    main()
