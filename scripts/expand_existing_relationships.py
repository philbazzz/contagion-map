"""
Expand verified relationships among ALREADY-REGISTERED entities.
No new companies. Prefer SEC/IR/official announcements. As of 2026-10-20.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "backend" / "data"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save(name: str, obj: dict) -> None:
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


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
        "roles": [],
        "explanation": explanation,
    }


NEW_SOURCES = [
    {
        "id": "S_NVDA_10K_FY26_MFG",
        "title": "NVIDIA Form 10-K FY2026 — Manufacturing / suppliers (TSMC, Samsung, SK hynix, Micron, Hon Hai, Wistron)",
        "publisher": "SEC EDGAR",
        "date": "2026-02-25",
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm",
        "used_for": "Named foundry, memory, and CMS suppliers",
        "kind": "10-K",
    },
    {
        "id": "S_DELL_AI_FACTORY",
        "title": "Dell AI Factory with NVIDIA (official Dell blog / partnership)",
        "publisher": "Dell Technologies",
        "date": "2024-05-20",
        "url": "https://www.dell.com/en-us/blog/transform-innovation-into-value-the-dell-ai-factory-with-nvidia/",
        "used_for": "Dell–NVIDIA strategic AI Factory partnership",
        "kind": "press",
    },
    {
        "id": "S_HPE_NVDA_AI",
        "title": "HPE and NVIDIA: NVIDIA AI Computing by HPE partnership expansion",
        "publisher": "HPE Newsroom",
        "date": "2025-06-24",
        "url": "https://www.hpe.com/us/en/newsroom/blog-post/2025/06/hpe-and-nvidia-a-partnership-driving-the-next-generation-of-ai-innovation.html",
        "used_for": "HPE–NVIDIA AI Computing partnership",
        "kind": "press",
    },
    {
        "id": "S_SMCI_10K_FY25",
        "title": "Super Micro Computer Form 10-K (year ended June 30, 2025)",
        "publisher": "SEC EDGAR",
        "date": "2025",
        "url": "https://www.sec.gov/Archives/edgar/data/1375365/000137536525000027/smci-20250630.htm",
        "used_for": "SMCI collaborates with NVIDIA, Intel, AMD on product cycles",
        "kind": "10-K",
    },
    {
        "id": "S_AMD_AR24",
        "title": "AMD 2024 Annual Report — shareholder letter (Meta, Microsoft, Oracle Instinct; AWS/Azure instances)",
        "publisher": "AMD IR / SEC",
        "date": "2025",
        "url": "https://ir.amd.com/financial-information/sec-filings/content/0001193125-25-067185/0001193125-25-067185.pdf",
        "used_for": "Named hyperscaler deployments of AMD Instinct / EPYC",
        "kind": "ir",
    },
    {
        "id": "S_MSFT_EXPRESSROUTE",
        "title": "Azure ExpressRoute Metro locations (Equinix / Digital Realty listed)",
        "publisher": "Microsoft Learn",
        "date": "2026",
        "url": "https://learn.microsoft.com/en-us/azure/expressroute/metro",
        "used_for": "Microsoft Azure interconnection via Equinix and Digital Realty",
        "kind": "docs",
    },
    {
        "id": "S_EQIX_AZURE",
        "title": "Equinix partner page — Microsoft Azure / ExpressRoute",
        "publisher": "Equinix",
        "date": "2026",
        "url": "https://www.equinix.com/partners/microsoft-azure",
        "used_for": "Equinix as Azure ExpressRoute connectivity partner",
        "kind": "ir",
    },
    {
        "id": "S_DLR_AZURE",
        "title": "Digital Realty expands Microsoft Azure ExpressRoute relationship",
        "publisher": "Digital Realty",
        "date": "2024",
        "url": "https://www.digitalrealty.com/about/newsroom/press-releases/123278/digital-realty-expands-global-relationship-with-microsoft-with-the-deployment-of-microsoft-azure-expressroute-cloud-on-ramp-in-dallas-and-the-launch-of-the-new-azure-expressroute-metro-service-in-amsterdam-and-zurich",
        "used_for": "Digital Realty–Microsoft ExpressRoute on-ramps",
        "kind": "press",
    },
    {
        "id": "S_AWS_DX_PARTNERS",
        "title": "AWS Direct Connect Partners (Equinix / Digital Realty locations)",
        "publisher": "Amazon Web Services",
        "date": "2026",
        "url": "https://aws.amazon.com/directconnect/partners/",
        "used_for": "AWS Direct Connect validated partners include Equinix and Digital Realty",
        "kind": "docs",
    },
    {
        "id": "S_EQIX_AWS",
        "title": "Equinix — AWS Direct Connect partner page",
        "publisher": "Equinix",
        "date": "2026",
        "url": "https://www.equinix.com/partners/aws",
        "used_for": "Equinix Fabric / Direct Connect to AWS",
        "kind": "ir",
    },
    {
        "id": "S_DLR_AWS",
        "title": "Digital Realty — AWS Direct Connect / Outposts partner page",
        "publisher": "Digital Realty",
        "date": "2026",
        "url": "https://www.digitalrealty.com/partners/aws",
        "used_for": "Digital Realty hosts AWS Direct Connect on-ramps",
        "kind": "ir",
    },
    {
        "id": "S_ORCL_FC_EQIX",
        "title": "Oracle FastConnect regions by partner — Equinix Fabric / Digital Realty",
        "publisher": "Oracle",
        "date": "2026",
        "url": "https://www.oracle.com/cloud/networking/fastconnect/regions-by-partner/",
        "used_for": "OCI FastConnect partners include Equinix Fabric and Digital Realty",
        "kind": "docs",
    },
    {
        "id": "S_OAI_NVDA_10GW",
        "title": "OpenAI and NVIDIA announce strategic partnership to deploy 10 GW of NVIDIA systems",
        "publisher": "OpenAI / NVIDIA Newsroom",
        "date": "2025-09-22",
        "url": "https://openai.com/index/openai-nvidia-systems-partnership/",
        "used_for": "OpenAI–NVIDIA LOI: ≥10 GW systems; NVIDIA intends up to $100B investment as GW deployed",
        "kind": "press",
    },
    {
        "id": "S_OAI_ORCL_STARGATE",
        "title": "Stargate advances with 4.5 GW partnership with Oracle",
        "publisher": "OpenAI",
        "date": "2025-07-22",
        "url": "https://openai.com/index/stargate-advances-with-partnership-with-oracle/",
        "used_for": "OpenAI–Oracle Stargate data-center capacity agreement",
        "kind": "press",
    },
    {
        "id": "S_OAI_STARGATE",
        "title": "Announcing The Stargate Project",
        "publisher": "OpenAI",
        "date": "2025-01-21",
        "url": "https://openai.com/index/announcing-the-stargate-project",
        "used_for": "Stargate initial partners: SoftBank, OpenAI, Oracle, MGX; tech partners include Microsoft, NVIDIA, Oracle",
        "kind": "press",
    },
    {
        "id": "S_AMZN_ANTHROPIC",
        "title": "Amazon and Anthropic expand strategic collaboration (equity + AWS compute)",
        "publisher": "Amazon / Anthropic",
        "date": "2026-04-20",
        "url": "https://www.anthropic.com/news/anthropic-amazon-compute",
        "used_for": "Amazon equity in Anthropic; Anthropic AWS primary cloud / Trainium compute",
        "kind": "press",
    },
    {
        "id": "S_AMZN_ANTHROPIC_INV",
        "title": "Amazon announces additional Anthropic investment",
        "publisher": "Amazon",
        "date": "2026",
        "url": "https://www.aboutamazon.com/news/company-news/amazon-invests-additional-5-billion-anthropic-ai",
        "used_for": "Amazon $5B + up to $20B future investment in Anthropic (on top of prior $8B)",
        "kind": "press",
    },
    {
        "id": "S_MICRON_NVDA_HBM",
        "title": "Micron HBM / SOCAMM designed for NVIDIA platforms (GTC press)",
        "publisher": "Micron IR",
        "date": "2025-03-18",
        "url": "https://investors.micron.com/news/press-release/2025/Micron-Innovates-From-the-Data-Center-to-the-Edge-With-NVIDIA-03-18-2025/default.aspx",
        "used_for": "Micron HBM3E/SOCAMM for NVIDIA Blackwell platforms",
        "kind": "press",
    },
]


UPGRADES = {
    "s_nvidia_tsmc": {
        "source_status": "VERIFIED",
        "relationship_type": "SUPPLIER",
        "label": "NVIDIA wafers at TSMC (named 10-K)",
        "impact_label": "NVIDIA wafers at TSMC (named 10-K)",
        "source_ids": ["S_NVDA_10K_FY26", "S_NVDA_10K_FY26_MFG"],
        "explanation": (
            "NVIDIA FY2026 10-K Manufacturing: utilizes foundries such as TSMC and Samsung to produce semiconductor wafers; "
            "uses CoWoS packaging. Named supplier relationship — wafer volumes/prices not disclosed."
        ),
        "amount_note": "웨이퍼 물량·단가 미공시",
    },
    "sc_samsung_nv": {
        "source_status": "VERIFIED",
        "relationship_type": "SUPPLIER",
        "label": "NVIDIA foundry + memory at Samsung (named 10-K)",
        "impact_label": "NVIDIA foundry + memory at Samsung (named 10-K)",
        "source_ids": ["S_NVDA_10K_FY26", "S_NVDA_10K_FY26_MFG", "S_SMSN_FY25"],
        "explanation": (
            "NVIDIA FY2026 10-K: uses Samsung as a wafer foundry and purchases memory from Samsung "
            "(alongside SK hynix and Micron). Upgraded from industry-structure inference to named supplier disclosure."
        ),
        "amount_note": "물량·단가 미공시",
    },
    "s_dell_nvidia": {
        "source_status": "VERIFIED",
        "relationship_type": "STRATEGIC_PARTNERSHIP",
        "impact_channel": "supply_chain",
        "label": "Dell AI Factory with NVIDIA",
        "impact_label": "Dell AI Factory with NVIDIA",
        "source_ids": ["S_DELL_AI_FACTORY", "S_NVDA_10K_FY26"],
        "explanation": (
            "Dell official announcement of Dell AI Factory with NVIDIA (end-to-end enterprise AI solutions). "
            "Long-standing OEM/systems partnership; not a disclosed hyperscaler GPU PO amount."
        ),
        "amount_note": "전략 파트너십 · 계약액 미공시",
    },
    "s_hpe_nvidia": {
        "source_status": "VERIFIED",
        "relationship_type": "STRATEGIC_PARTNERSHIP",
        "impact_channel": "supply_chain",
        "label": "NVIDIA AI Computing by HPE",
        "impact_label": "NVIDIA AI Computing by HPE",
        "source_ids": ["S_HPE_NVDA_AI", "S_NVDA_10K_FY26"],
        "explanation": (
            "HPE official partnership materials: NVIDIA AI Computing by HPE / Private Cloud AI with Blackwell support. "
            "Strategic OEM/systems collaboration — unit purchase USD not disclosed."
        ),
        "amount_note": "전략 파트너십 · 계약액 미공시",
    },
    "s_smci_nvidia": {
        "source_status": "VERIFIED",
        "source_ids": ["S_SMCI_10K_FY25", "S_SMCI_NV", "S_NVDA_10K_FY26"],
        "explanation": (
            "SMCI FY2025 10-K: works closely with NVIDIA (and Intel/AMD) to align products with processor release cycles; "
            "ships Hopper/Blackwell-compatible systems. Reinforced by SMCI IR releases on NVIDIA-certified systems."
        ),
    },
    "s_nvidia_micron": {
        "source_ids": ["S_NVDA_10K_FY26", "S_NVDA_10K_FY26_MFG", "S_MICRON_NVDA_HBM"],
        "explanation": (
            "NVIDIA FY2026 10-K names Micron as a memory supplier. Micron IR: HBM3E/SOCAMM products designed for "
            "NVIDIA Blackwell platforms. Supply relationship — USD of memory purchases not disclosed."
        ),
    },
    "s_nvidia_foxconn": {
        "source_ids": ["S_NVDA_10K_FY26", "S_NVDA_10K_FY26_MFG"],
        "source_status": "VERIFIED",
        "explanation": (
            "NVIDIA FY2026 10-K Manufacturing: engages Hon Hai Precision Industry (Foxconn) among contract manufacturers "
            "for assembly, testing and packaging of final products."
        ),
    },
    "s_nvidia_wistron": {
        "source_ids": ["S_NVDA_10K_FY26", "S_NVDA_10K_FY26_MFG"],
        "source_status": "VERIFIED",
        "explanation": (
            "NVIDIA FY2026 10-K Manufacturing: engages Wistron Corporation among contract manufacturers for assembly, "
            "testing and packaging of final products."
        ),
    },
    "s_equinix_vertiv": {
        "amount_note": "섹터 경로 · 개별 PO 미특정 — Vertiv는 Equinix 캠퍼스에서 흔히 쓰이는 전력·냉각 벤더군에 속하나 개별 계약액 미공시",
    },
}

NEW_RELS = [
    # Cloud ↔ DC interconnect (facility / strategic)
    rel(
        "sp_msft_equinix", "microsoft", "equinix", "STRATEGIC_PARTNERSHIP", "facility",
        "Azure ExpressRoute via Equinix", "VERIFIED",
        ["S_MSFT_EXPRESSROUTE", "S_EQIX_AZURE"],
        "Microsoft Learn lists Equinix among ExpressRoute Metro/service providers; Equinix markets Azure ExpressRoute on-ramps. "
        "Interconnection partnership — not a disclosed Azure lease USD amount.",
        "상호접속 · 임차액 미공시",
    ),
    rel(
        "sp_msft_dlr", "microsoft", "digital_realty", "STRATEGIC_PARTNERSHIP", "facility",
        "Azure ExpressRoute via Digital Realty", "VERIFIED",
        ["S_MSFT_EXPRESSROUTE", "S_DLR_AZURE"],
        "Microsoft Learn lists Digital Realty in ExpressRoute Metro locations; Digital Realty announced Azure ExpressRoute "
        "Cloud On-Ramp expansion. Interconnection — lease USD not disclosed here.",
        "상호접속 · 임차액 미공시",
    ),
    rel(
        "sp_amazon_equinix", "amazon", "equinix", "STRATEGIC_PARTNERSHIP", "facility",
        "AWS Direct Connect via Equinix", "VERIFIED",
        ["S_AWS_DX_PARTNERS", "S_EQIX_AWS"],
        "AWS Direct Connect Partners program lists Equinix at multiple DX locations; Equinix documents Dedicated/Hosted DX. "
        "Connectivity partnership — not a named AWS CapEx contract.",
        "상호접속 · 계약액 미공시",
    ),
    rel(
        "sp_amazon_dlr", "amazon", "digital_realty", "STRATEGIC_PARTNERSHIP", "facility",
        "AWS Direct Connect via Digital Realty", "VERIFIED",
        ["S_AWS_DX_PARTNERS", "S_DLR_AWS"],
        "AWS Direct Connect partner listings and Digital Realty AWS partner page: DLR hosts multiple DX on-ramps. "
        "Connectivity partnership — not a disclosed hyperscale build USD.",
        "상호접속 · 계약액 미공시",
    ),
    rel(
        "sp_oracle_equinix", "oracle", "equinix", "STRATEGIC_PARTNERSHIP", "facility",
        "OCI FastConnect via Equinix Fabric", "VERIFIED",
        ["S_ORCL_FC_EQIX"],
        "Oracle FastConnect regions-by-partner lists Equinix Fabric across many metros. Official partner interconnect — "
        "not a disclosed OCI campus lease amount.",
        "상호접속 · 계약액 미공시",
    ),
    rel(
        "sp_oracle_dlr", "oracle", "digital_realty", "STRATEGIC_PARTNERSHIP", "facility",
        "OCI FastConnect via Digital Realty", "VERIFIED",
        ["S_ORCL_FC_EQIX"],
        "Oracle FastConnect regions-by-partner lists Digital Realty in multiple regions. Official partner interconnect.",
        "상호접속 · 계약액 미공시",
    ),
    # OpenAI multi-edges
    rel(
        "sp_openai_nvidia", "openai", "nvidia", "STRATEGIC_PARTNERSHIP", "supply_chain",
        "OpenAI–NVIDIA ≥10 GW systems LOI", "VERIFIED",
        ["S_OAI_NVDA_10GW"],
        "OpenAI and NVIDIA (2025-09-22) letter of intent to deploy ≥10 GW of NVIDIA systems (Vera Rubin first GW 2H2026). "
        "Preferred strategic compute/networking partner language. Final definitive terms noted as forthcoming.",
        "≥10 GW 규모 · GPU 단가 미공시",
    ),
    rel(
        "eq_nvidia_openai", "nvidia", "openai", "EQUITY_INVESTMENT", "equity",
        "NVIDIA intended investment in OpenAI (up to $100B as GW deployed)", "VERIFIED",
        ["S_OAI_NVDA_10GW"],
        "Same LOI: NVIDIA intends to invest up to $100B in OpenAI progressively as each gigawatt is deployed. "
        "Investment is contingent on deployment milestones; treat as announced intent, not closed single tranche.",
        "최대 $100B 의도 · 단계적",
        amount_usd_m=100000,
    ),
    rel(
        "sp_openai_oracle", "openai", "oracle", "STRATEGIC_PARTNERSHIP", "facility",
        "OpenAI–Oracle Stargate capacity", "VERIFIED",
        ["S_OAI_ORCL_STARGATE", "S_OAI_STARGATE"],
        "OpenAI: agreement with Oracle to develop 4.5 GW additional Stargate DC capacity; Stargate I Abilene on OCI with "
        "NVIDIA GB200 racks. Strategic infrastructure partnership — not CoreWeave-centric.",
        "4.5 GW+ Stargate · 금액은 보도 기준 상이",
    ),
    # Amazon–Anthropic (distinct equity + cloud)
    rel(
        "eq_amazon_anthropic", "amazon", "anthropic", "EQUITY_INVESTMENT", "equity",
        "Amazon minority equity in Anthropic", "VERIFIED",
        ["S_AMZN_ANTHROPIC", "S_AMZN_ANTHROPIC_INV"],
        "Amazon official: prior $8B investment; additional $5B announced with up to $20B future tied to milestones. "
        "Minority stake; Anthropic governance notes Long Term Benefit Trust remains.",
        "누적 투자 공시 (단계별)",
        amount_usd_m=13000,
    ),
    rel(
        "c_anthropic_amazon", "anthropic", "amazon", "CUSTOMER", "customer",
        "Anthropic primary cloud / Trainium on AWS", "VERIFIED",
        ["S_AMZN_ANTHROPIC"],
        "Anthropic: AWS primary training/cloud provider; >$100B ten-year commitment to AWS technologies; up to 5 GW capacity "
        "including Trainium. Claude on Bedrock. Distinct from equity stake.",
        "10년 >$100B AWS 커밋 (회사 발표)",
        amount_usd_m=100000,
    ),
    # AMD hyperscaler deployments (AMD AR 2024 letter)
    rel(
        "c_microsoft_amd", "microsoft", "amd", "CUSTOMER", "customer",
        "Microsoft Azure / Copilot on AMD Instinct (AMD AR)", "VERIFIED",
        ["S_AMD_AR24"],
        "AMD 2024 Annual Report shareholder letter: Microsoft highlighted TCO of Instinct MI300X for Copilot; "
        "Azure instances with AMD Instinct. Customer/deployer — not a >10% AMD revenue disclosure.",
        "배포 확인 · 매출비중 미공시",
    ),
    rel(
        "c_meta_amd", "meta", "amd", "CUSTOMER", "customer",
        "Meta deploys AMD Instinct / EPYC (AMD AR)", "VERIFIED",
        ["S_AMD_AR24"],
        "AMD 2024 AR: Meta deployed MI300X for inference (incl. Llama 405B) and >1.5M EPYC processors across fleet. "
        "Named deployment — not AMD 10-K >10% customer line.",
        "배포 확인 · 매출비중 미공시",
    ),
    rel(
        "c_oracle_amd", "oracle", "amd", "CUSTOMER", "customer",
        "Oracle Cloud deploys AMD Instinct (AMD AR)", "VERIFIED",
        ["S_AMD_AR24"],
        "AMD 2024 AR: Oracle Cloud among cloud providers adopting Instinct accelerators for public instances.",
        "배포 확인 · 매출비중 미공시",
    ),
    rel(
        "c_amazon_amd", "amazon", "amd", "CUSTOMER", "customer",
        "AWS offers AMD EPYC / Instinct instances (AMD AR)", "VERIFIED",
        ["S_AMD_AR24"],
        "AMD 2024 AR: >1,000 AMD-powered public cloud instances including AWS; hyperscale data-center demand described in 10-K generally.",
        "클라우드 인스턴스 · 매출비중 미공시",
    ),
    rel(
        "sp_smci_amd", "smci", "amd", "STRATEGIC_PARTNERSHIP", "supply_chain",
        "SMCI product co-development with AMD", "VERIFIED",
        ["S_SMCI_10K_FY25"],
        "SMCI FY2025 10-K: works closely with NVIDIA, Intel and AMD to develop products compatible with latest processors.",
        "제품 공동 개발 · 구매액 미공시",
    ),
    # Alphabet ExpressRoute-style — Equinix is major Google Cloud interconnect provider; use Equinix AWS/Azure pattern carefully
    # Skip Alphabet-Equinix without a clean official Google doc in this pass.
]


def upsert_source(sources: list[dict], row: dict) -> bool:
    for i, s in enumerate(sources):
        if s["id"] == row["id"]:
            sources[i] = {**s, **row}
            return False
    sources.append(row)
    return True


def main() -> None:
    ents = load("entities.json")
    idset = {e["id"] for e in ents["entities"]}
    rels_doc = load("relationships.json")
    src_doc = load("sources.json")
    existing_ids = {r["id"] for r in rels_doc["relationships"]}

    added_src = sum(1 for s in NEW_SOURCES if upsert_source(src_doc["sources"], s))

    # upgrades
    upgraded = 0
    by_id = {r["id"]: r for r in rels_doc["relationships"]}
    for rid, patch in UPGRADES.items():
        if rid not in by_id:
            print("WARN missing upgrade target", rid)
            continue
        by_id[rid].update(patch)
        upgraded += 1

    added = 0
    skipped = []
    for row in NEW_RELS:
        if row["source"] not in idset or row["target"] not in idset:
            skipped.append((row["id"], "unknown entity"))
            continue
        if row["id"] in existing_ids:
            # refresh in place
            for i, r in enumerate(rels_doc["relationships"]):
                if r["id"] == row["id"]:
                    rels_doc["relationships"][i] = row
                    break
            continue
        # avoid exact duplicate undirected same type
        dup = False
        for r in rels_doc["relationships"]:
            if (
                {r["source"], r["target"]} == {row["source"], row["target"]}
                and r["relationship_type"] == row["relationship_type"]
            ):
                dup = True
                break
        if dup:
            skipped.append((row["id"], "duplicate type pair"))
            continue
        rels_doc["relationships"].append(row)
        existing_ids.add(row["id"])
        added += 1

    save("relationships.json", rels_doc)
    save("sources.json", src_doc)

    # quick stats
    rels = rels_doc["relationships"]
    cw = sum(1 for e in rels if e["source"] == "coreweave" or e["target"] == "coreweave")
    print(f"sources +{added_src} total={len(src_doc['sources'])}")
    print(f"upgraded {upgraded}")
    print(f"new_edges +{added} total={len(rels)} CW={cw} nonCW={len(rels)-cw}")
    if skipped:
        print("skipped", skipped)


if __name__ == "__main__":
    main()
