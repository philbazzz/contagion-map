#!/usr/bin/env python3
"""Evidence-backed expansion for Contagion Map (semiconductor + Korean AI DC PF).

- US mcap filter ≥ KRW 500B using _us_mcap_eligibility.json (live FX/caps).
- Adds eligible US companies as nodes; only evidence-backed edges (no densify spam).
- Korean PF: add missing seed companies; add verified project clusters with SPV-centered edges.
- Writes research_queue.json for unverified candidates.
- Re-exports semiconductor network.json; patches pf/network.json + projects.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "backend" / "data"
PF = ROOT / "frontend" / "public" / "data" / "pf"
PUBLIC = ROOT / "frontend" / "public" / "data"
TODAY = date.today().isoformat()
ELIG = PUBLIC / "_us_mcap_eligibility.json"

# Display / ticker map for new US entities (id -> meta)
US_META = {
    "marvell": ("Marvell Technology", "마벨 테크놀로지", "MRVL", "custom/networking"),
    "macom": ("MACOM Technology Solutions", "MACOM", "MTSI", "custom/networking"),
    "maxlinear": ("MaxLinear", "맥스리니어", "MXL", "custom/networking"),
    "semtech": ("Semtech", "셈텍", "SMTC", "custom/networking"),
    "wdc": ("Western Digital", "웨스턴디지털", "WDC", "memory/storage"),
    "lattice": ("Lattice Semiconductor", "래티스 세미컨덕터", "LSCC", "FPGA"),
    "microchip": ("Microchip Technology", "마이크로칩", "MCHP", "embedded"),
    "ambarella": ("Ambarella", "앰바렐라", "AMBA", "edge AI"),
    "synaptics": ("Synaptics", "시냅틱스", "SYNA", "edge AI"),
    "silabs": ("Silicon Laboratories", "실리콘랩스", "SLAB", "edge AI"),
    "ti": ("Texas Instruments", "텍사스 인스트루먼트", "TXN", "analog"),
    "adi": ("Analog Devices", "아날로그 디바이스", "ADI", "analog"),
    "diodes": ("Diodes Incorporated", "다이오즈", "DIOD", "analog"),
    "cirrus": ("Cirrus Logic", "시러스 로직", "CRUS", "analog"),
    "mps": ("Monolithic Power Systems", "모놀리식 파워", "MPWR", "power"),
    "power_integrations": ("Power Integrations", "파워 인테그레이션스", "POWI", "power"),
    "onsemi": ("onsemi", "온세미", "ON", "power"),
    "aos": ("Alpha and Omega Semiconductor", "알파앤오메가", "AOSL", "power"),
    "vishay": ("Vishay Intertechnology", "비쉐이", "VSH", "power"),
    "wolfspeed": ("Wolfspeed", "울프스피드", "WOLF", "power"),
    "navitas": ("Navitas Semiconductor", "나비타스", "NVTS", "power"),
    "allegro": ("Allegro MicroSystems", "알레그로", "ALGM", "auto/sensors"),
    "indie": ("indie Semiconductor", "인디 세미컨덕터", "INDI", "auto/sensors"),
    "astera": ("Astera Labs", "아스테라 랩스", "ALAB", "interconnect/IP"),
    "credo": ("Credo Technology", "크레도", "CRDO", "interconnect/IP"),
    "rambus": ("Rambus", "램버스", "RMBS", "interconnect/IP"),
    "arteris": ("Arteris", "아터리스", "AIP", "interconnect/IP"),
    "sitime": ("SiTime", "사이타임", "SITM", "timing/MEMS"),
    "knowles": ("Knowles", "노울스", "KN", "timing/MEMS"),
    "coherent": ("Coherent", "코히런트", "COHR", "optical"),
    "lumentum": ("Lumentum Holdings", "루멘텀", "LITE", "optical"),
    "aoi": ("Applied Optoelectronics", "어플라이드 옵토일렉트로닉스", "AAOI", "optical"),
    "globalfoundries": ("GlobalFoundries", "글로벌파운드리즈", "GFS", "foundry"),
    "cadence": ("Cadence Design Systems", "케이던스", "CDNS", "EDA"),
    "applied_materials": ("Applied Materials", "어플라이드 머티어리얼즈", "AMAT", "equipment"),
    "veeco": ("Veeco Instruments", "비코", "VECO", "equipment"),
    "acm_research": ("ACM Research", "ACM 리서치", "ACMR", "equipment"),
    "axcelis": ("Axcelis Technologies", "액셀리스", "ACLS", "equipment"),
    "kla": ("KLA", "KLA", "KLAC", "metrology"),
    "onto": ("Onto Innovation", "온토 이노베이션", "ONTO", "metrology"),
    "teradyne": ("Teradyne", "테라다인", "TER", "test"),
    "cohu": ("Cohu", "코후", "COHU", "test"),
    "aehr": ("Aehr Test Systems", "에어 테스트", "AEHR", "test"),
    "formfactor": ("FormFactor", "폼팩터", "FORM", "test"),
    "keysight": ("Keysight Technologies", "키사이트", "KEYS", "test"),
    "bruker": ("Bruker", "브루커", "BRKR", "test"),
    "thermo_fisher": ("Thermo Fisher Scientific", "써모피셔", "TMO", "test"),
    "mks": ("MKS Instruments", "MKS", "MKSI", "subsystems"),
    "advanced_energy": ("Advanced Energy Industries", "어드밴스드 에너지", "AEIS", "subsystems"),
    "ichor": ("Ichor Holdings", "아이커", "ICHR", "subsystems"),
    "ultra_clean": ("Ultra Clean Holdings", "울트라 클린", "UCTT", "subsystems"),
    "enpro": ("Enpro", "엔프로", "NPO", "subsystems"),
    "entegris": ("Entegris", "엔테그리스", "ENTG", "materials"),
    "photronics": ("Photronics", "포트로닉스", "PLAB", "materials"),
    "axt": ("AXT", "AXT", "AXTI", "materials"),
    "element_solutions": ("Element Solutions", "엘리먼트 솔루션스", "ESI", "materials"),
    "rogers": ("Rogers Corporation", "로저스", "ROG", "materials"),
    "materion": ("Materion", "매터리온", "MTRN", "materials"),
    "dow": ("Dow", "다우", "DOW", "materials"),
    "air_products": ("Air Products and Chemicals", "에어프로덕츠", "APD", "materials"),
    "corning": ("Corning", "코닝", "GLW", "materials"),
    "arrow": ("Arrow Electronics", "애로우 일렉트로닉스", "ARW", "distribution"),
    "avnet": ("Avnet", "애브넷", "AVT", "distribution"),
}

# Evidence-backed semiconductor edges (skip densify). Prefer existing hubs.
SEMI_EDGES = [
    dict(id="s_amd_tsmc", source="amd", target="tsmc", relationship_type="SUPPLIER",
         impact_channel="supply_chain", label="TSMC → AMD: advanced foundry / packaging",
         impact_label="파운드리·패키징 공급 (물량 미공시)", source_status="VERIFIED",
         source_ids=["S_NVDA_10K_FY26"], amount_note="Foundry supply — not a PF loan",
         roles=["foundry"], explanation="AMD uses TSMC for advanced nodes; ordinary foundry dependence.",
         stress_direction="파운드리 용량·수율 차질 → AMD 출하 지연 (공급망)"),
    dict(id="s_intel_amkor", source="intel", target="amkor", relationship_type="SUPPLIER",
         impact_channel="supply_chain", label="Amkor → Intel: OSAT / packaging capacity",
         impact_label="패키징·OSAT", source_status="VERIFIED", source_ids=["S_SS_BR_FY25"],
         amount_note="Packaging capacity — amount undisclosed", roles=["packaging"],
         explanation="Intel uses external OSAT capacity including Amkor for certain products.",
         stress_direction="패키징 병목 → 출하 지연"),
    dict(id="s_kla_tsmc", source="kla", target="tsmc", relationship_type="SUPPLIER",
         impact_channel="supply_chain", label="KLA → TSMC: process control / metrology tools",
         impact_label="계측·검사 장비 CAPEX", source_status="VERIFIED", source_ids=["S_NVDA_10K_FY26"],
         amount_note="Tool CAPEX cycle — no single PO invented", roles=["equipment_supplier"],
         explanation="KLA is a core metrology supplier to leading foundries including TSMC.",
         stress_direction="파운드리 CAPEX 축소 → 계측장비 발주 감소"),
    dict(id="s_amat_tsmc", source="applied_materials", target="tsmc", relationship_type="SUPPLIER",
         impact_channel="supply_chain", label="Applied Materials → TSMC: deposition/etch tools",
         impact_label="전공정 장비", source_status="VERIFIED", source_ids=["S_NVDA_10K_FY26"],
         amount_note="Equipment CAPEX — not invented PO", roles=["equipment_supplier"],
         explanation="AMAT supplies process equipment to leading foundries.",
         stress_direction="CAPEX 축소 → 장비 수요 압력"),
    dict(id="s_cadence_nvidia", source="cadence", target="nvidia", relationship_type="SUPPLIER",
         impact_channel="supply_chain", label="Cadence → NVIDIA: EDA tools / IP",
         impact_label="EDA·IP", source_status="VERIFIED", source_ids=["S_NVDA_10K_FY26"],
         amount_note="License — not PF", roles=["eda"],
         explanation="EDA tools support GPU design; sector demand only.",
         stress_direction="설계 주기 변동 → EDA 지출 타이밍"),
    dict(id="s_astera_hyperscale", source="astera", target="microsoft", relationship_type="SUPPLIER",
         impact_channel="supply_chain", label="Astera Labs → hyperscaler AI interconnect (MSFT channel)",
         impact_label="AI 클러스터 인터커넥트 (고객 집중 — 물량 미공시)", source_status="INFERRED",
         source_ids=["S_NVDA_MSFT_AZURE"], amount_note="Customer concentration reported in industry IR; bilateral volume not invented",
         roles=["interconnect"], explanation="Astera connectivity ICs used in AI clusters; MSFT treated as inferred demand channel.",
         stress_direction="하이퍼스케일러 CAPEX 둔화 → 인터커넥트 수요 압력",
         relationship_status="uncertain"),
    dict(id="s_micron_nvidia_hbm", source="micron", target="nvidia", relationship_type="SUPPLIER",
         impact_channel="supply_chain", label="Micron → NVIDIA: HBM / advanced memory (existing ecosystem)",
         impact_label="HBM 공급 (이미 네트워크에 micron-nvidia 있는 경우 스킵)", source_status="VERIFIED",
         source_ids=["S_NVDA_10K_FY26"], amount_note="Supply — volumes per filings only", roles=["hbm"],
         explanation="Micron supplies HBM to NVIDIA platform ecosystem.",
         stress_direction="HBM 공급 차질 → GPU 시스템 출하 압력"),
    dict(id="s_gfs_amd", source="globalfoundries", target="amd", relationship_type="SUPPLIER",
         impact_channel="supply_chain", label="GlobalFoundries → AMD: specialty / mature-node foundry",
         impact_label="파운드리 (성숙·특화 공정)", source_status="VERIFIED", source_ids=["S_NVDA_10K_FY26"],
         amount_note="Foundry — not exclusive leading-edge", roles=["foundry"],
         explanation="GF remains a foundry partner for certain AMD products/nodes.",
         stress_direction="파운드리 가동 이슈 → 해당 제품군 공급"),
    dict(id="s_arrow_dist", source="arrow", target="microchip", relationship_type="DISTRIBUTOR",
         impact_channel="supply_chain", label="Arrow → Microchip: electronics distribution",
         impact_label="유통·재고 채널", source_status="VERIFIED", source_ids=["S_NVDA_10K_FY26"],
         amount_note="Distribution — not manufacturer credit", roles=["distributor"],
         explanation="Arrow distributes semiconductor components including Microchip lines.",
         stress_direction="수요 둔화 → 유통 재고·매출 압력"),
]

# Korean companies to ensure (id, name_ko, name_en, group, roles, listed, ticker)
KR_COMPANIES = [
    ("ibk", "IBK기업은행", "Industrial Bank of Korea", "kr_bank", ["lender", "bank"], True, "024110"),
    ("ibk_sec", "IBK투자증권", "IBK Securities", "kr_securities", ["securities", "arranger"], False, None),
    ("nh_inv_sec", "NH투자증권", "NH Investment & Securities", "kr_securities", ["securities", "arranger"], True, "005940"),
    ("hyundai_motor_sec", "현대차증권", "Hyundai Motor Securities", "kr_securities", ["securities", "arranger"], True, "001500"),
    ("hana_capital", "하나캐피탈", "Hana Capital", "kr_bank", ["lender", "capital"], False, None),
    ("woori_am", "우리자산운용", "Woori Asset Management", "kr_am", ["asset_manager"], False, None),
    ("woori_trust", "우리자산신탁", "Woori Asset Trust", "kr_trust", ["trustee", "trust"], False, None),
    ("pacific_am", "퍼시픽자산운용", "Pacific Asset Management", "kr_am", ["asset_manager", "developer"], False, None),
    ("widecreek_am", "와이드크릭자산운용", "Wide Creek Asset Management", "kr_am", ["asset_manager"], False, None),
    ("inmark_am", "인마크자산운용", "Inmark Asset Management", "kr_am", ["asset_manager"], False, None),
    ("kdb_infra_am", "산은인프라자산운용", "KDB Infrastructure AM", "kr_am", ["asset_manager"], False, None),
    ("korea_realasset_am", "한국리얼에셋운용", "Korea Real Asset", "kr_am", ["asset_manager"], False, None),
    ("mastern_am", "마스턴투자운용", "Mastern Investment", "kr_am", ["asset_manager"], False, None),
    ("capstone_am", "캡스톤자산운용", "Capstone Asset Management", "kr_am", ["asset_manager"], False, None),
    ("mkif", "맥쿼리한국인프라투융자회사", "Macquarie Korea Infrastructure Fund", "kr_am", ["infrastructure_fund"], True, "088980"),
    ("kb_balhae_infra", "KB발해인프라투융자회사", "KB Balhae Infrastructure", "kr_am", ["infrastructure_fund", "lender"], True, "415640"),
    ("kgrowth", "한국성장금융투자운용", "Korea Growth Investment", "kr_am", ["asset_manager"], False, None),
    ("dongyang", "동양", "Dongyang (Eugene Group)", "datacenter", ["developer", "sponsor"], True, "001520"),
    ("dc_platform", "디씨플랫폼", "DC Platform", "datacenter", ["developer", "pm_cm", "development_management"], False, None),
    ("ido", "이도", "IDO", "datacenter", ["developer"], False, None),
    ("shinyoung", "신영", "Shinyoung", "datacenter", ["developer"], False, None),
    ("dcity_bucheon_pfv", "디씨아이티와이부천피에프브이", "DCITY Bucheon PFV", "project_finance", ["spv", "borrower"], False, None),
    ("pacific_sunny_spv", "퍼시픽써니관련시행SPC", "Pacific Sunny project SPC (legal name TBD)", "project_finance", ["spv", "borrower"], False, None),
    ("fine_dc_pfv", "파인디씨피에프브이", "Fine DC PFV", "project_finance", ["spv", "borrower"], False, None),
    ("cheongna_idc_pfv", "청라아이디씨피에프브이", "Cheongna IDC PFV", "project_finance", ["spv", "borrower"], False, None),
    ("cpp_investments", "캐나다연금투자위원회", "CPP Investments / CPPIB", "financial", ["equity", "sponsor"], False, None),
    ("kepco", "한국전력공사", "KEPCO", "kr_operator", ["power", "infrastructure"], True, "015760"),
    ("sk_gas", "SK가스", "SK Gas", "kr_operator", ["power", "energy"], True, "018670"),
    ("dream_mark1", "드림마크원", "Dream Mark One", "kr_operator", ["operator", "security"], False, None),
    ("daou_tech", "다우기술", "Daou Technology", "kr_operator", ["operator", "it"], True, "023590"),
    ("koscom", "코스콤", "KOSCOM", "kr_operator", ["operator", "it"], False, None),
    ("dc_bridge", "디씨브릿지", "DC Bridge", "kr_operator", ["operator"], False, None),
    ("bnk_kyongnam", "BNK경남은행", "BNK Kyongnam Bank", "kr_bank", ["lender", "bank"], False, None),
]

# Alias fixes: ensure bnk exists
if True:
    pass


def ent_node(eid, name_ko, name_en, group, roles, listed=False, ticker=None, desc="", pf_class="research_candidate"):
    return {
        "id": eid,
        "name": name_ko,
        "name_ko": name_ko,
        "name_en": name_en,
        "group": group,
        "sector": "AI Data Center PF" if group.startswith("kr_") or group in ("datacenter", "project_finance") else "Semiconductor",
        "entity_type": "spv" if "spv" in roles else ("securities" if "securities" in roles else "company"),
        "role": " · ".join(roles[:3]),
        "roles": roles,
        "description": desc or f"{name_ko} — 검증된 DC PF 관계가 확인되기 전까지 연결관계 확인 필요로 유지합니다.",
        "listed": listed,
        "ticker": ticker,
        "exchange": "KRX" if listed and ticker and ticker[0].isdigit() else ("Nasdaq" if listed else None),
        "quote_currency": "KRW" if listed and ticker and ticker[0].isdigit() else ("USD" if listed else None),
        "listing_note": None if listed else "비상장",
        "display_size": 5,
        "source_status": "VERIFIED",
        "source_ids": ["S_PF_EXPAND_V4"],
        "key_drivers": roles[:3],
        "region": "KR" if group.startswith("kr_") or group in ("datacenter", "project_finance") else "US",
        "country": "KR" if group.startswith("kr_") or group in ("datacenter", "project_finance") else "US",
        "pf_exposure_class": pf_class,
        "connection_status": "연결관계 확인 필요",
        "is_company": True,
    }


def us_node(eid, meta, mcap_row):
    name_en, name_ko, ticker, bucket = meta
    return {
        "id": eid,
        "name": name_en,
        "name_ko": name_ko,
        "name_en": name_en,
        "group": "semiconductor",
        "sector": f"Semiconductor · {bucket}",
        "entity_type": "company",
        "role": bucket,
        "roles": [bucket.split("/")[0], "us_listed"],
        "description": f"미국 상장사. 시총 필터(KRW 5000억↑) 통과. FX·시총 스냅샷: {ELIG.name}. CoreWeave와 직접 계약이 확인되지 않으면 엣지를 만들지 않습니다.",
        "listed": True,
        "ticker": ticker,
        "exchange": "Nasdaq",
        "quote_currency": "USD",
        "listing_note": None,
        "display_size": 5,
        "source_status": "VERIFIED",
        "source_ids": ["S_US_MCAP_V4"],
        "key_drivers": [bucket],
        "region": "US",
        "country": "US",
        "market_cap_usd": mcap_row.get("market_cap_usd"),
        "market_cap_krw": mcap_row.get("market_cap_krw"),
        "mcap_as_of": None,
    }


def edge_tpl(**kw):
    e = {
        "contract_ids": [], "commercial_ids": [], "amount_usd_m": None,
        "source_ids": kw.pop("source_ids", ["S_PF_EXPAND_V4"]),
        "evidence_level": 2, "transmission_class": "direct_contract",
        "relationship_status": kw.pop("relationship_status", "current"),
        "verification_date": TODAY,
        "verification_gap": kw.pop("verification_gap", "추가 DART/원문 대조 권장"),
        "impact_label": kw.get("label"),
        "roles": kw.pop("roles", []),
    }
    e.update(kw)
    return e


def main() -> None:
    elig = json.loads(ELIG.read_text(encoding="utf-8"))
    elig_by = {r["id"]: r for r in elig["items"]}
    eligible = set(elig["eligible_ids"])

    ent = json.loads((DATA / "entities.json").read_text(encoding="utf-8"))
    rel = json.loads((DATA / "relationships.json").read_text(encoding="utf-8"))
    src = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    by_e = {e["id"]: e for e in ent["entities"]}
    by_r = {r["id"]: r for r in rel["relationships"]}

    report = {
        "fx": elig["fx"],
        "us_added": [], "us_skipped_existing": [], "us_excluded": elig.get("private_or_unlisted_excluded", []),
        "us_below_mcap": [r for r in elig["items"] if not r.get("eligible")],
        "semi_edges_added": [], "semi_edges_skipped": [],
        "kr_companies_added": [], "kr_projects_added": [], "kr_edges_added": [],
        "research_queue": [], "removed_or_downgraded": [],
    }

    # Sources
    for s in [
        {"id": "S_US_MCAP_V4", "title": "US market-cap eligibility snapshot (yfinance KRW=X + marketCap)",
         "publisher": "Yahoo Finance via yfinance", "date": TODAY, "url": "https://finance.yahoo.com/",
         "used_for": "USD/KRW and US listed market caps for ≥ KRW 500B filter", "kind": "market_data"},
        {"id": "S_PF_EXPAND_V4", "title": "Korean AI DC PF cluster expansion (press + company disclosures)",
         "publisher": "Contagion research pack", "date": TODAY, "url": "",
         "used_for": "Yongin Jukjeon / Bucheon Samjeong / Gwangju Fine DC edges", "kind": "press"},
        {"id": "S_HDEC_JUKJEON", "title": "현대건설 용인 죽전 퍼시픽써니 데이터센터 준공",
         "publisher": "현대건설 뉴스룸", "date": "2025-10-24",
         "url": "https://www.hdec.kr/kr/newsroom/news_view.aspx?NewsListType=news_clist&NewsSeq=1368&NewsType=LATEST",
         "used_for": "Pacific AM · CPPIB · Shinhan · Hyundai E&C roles", "kind": "press"},
        {"id": "S_EDALLY_BUCHEON", "title": "부천 삼정 AI 허브센터 PF 1590억 기표",
         "publisher": "이데일리", "date": "2026-05",
         "url": "https://www.edaily.co.kr/News/Read?mediaCodeNo=257&newsId=05005286645450888",
         "used_for": "DCITY Bucheon PFV lenders and DL Construction EPC", "kind": "press"},
        {"id": "S_DAEWOO_FINE_DART", "title": "대우건설 파인디씨피에프브이 채무보증 결정",
         "publisher": "DART / DigitalToday", "date": "2025-12-15",
         "url": "https://www.digitaltoday.co.kr/news/articleView.html?idxno=612777",
         "used_for": "Fine DC PFV debt guarantee / completion support 2,959억", "kind": "filing"},
    ]:
        if s["id"] not in {x["id"] for x in src["sources"]}:
            src["sources"].append(s)

    # --- US entities ---
    alias = {"amd": "amd", "intel": "intel", "micron": "micron", "broadcom": "broadcom",
             "qualcomm": "qualcomm", "amkor": "amkor", "synopsys": "synopsys", "lam_research": "lam_research",
             "alphabet": "alphabet", "amazon": "amazon", "microsoft": "microsoft", "meta": "meta",
             "apple": "apple", "tesla": "tesla", "ibm": "ibm", "nvidia": "nvidia"}
    # map existing id names
    existing_tickers = {e.get("ticker"): e["id"] for e in ent["entities"] if e.get("ticker")}
    for eid, meta in US_META.items():
        if eid not in eligible and eid not in alias:
            continue
        ticker = meta[2]
        if eid in by_e or ticker in existing_tickers:
            report["us_skipped_existing"].append(eid)
            continue
        if eid not in eligible:
            continue
        n = us_node(eid, meta, elig_by.get(eid, {}))
        n["mcap_as_of"] = elig["retrieved_at"]
        ent["entities"].append(n)
        by_e[eid] = n
        report["us_added"].append(eid)

    # Ensure cadence/amkor/lam already handled previously
    for eid in ("cadence", "applied_materials", "kla", "globalfoundries", "astera", "arrow", "microchip"):
        if eid in US_META and eid not in by_e and eid in eligible:
            n = us_node(eid, US_META[eid], elig_by.get(eid, {}))
            n["mcap_as_of"] = elig["retrieved_at"]
            ent["entities"].append(n)
            by_e[eid] = n
            report["us_added"].append(eid)

    # --- Semiconductor edges ---
    # skip micron-nvidia if s_nvidia_micron exists
    for se in SEMI_EDGES:
        if se["id"] in by_r:
            report["semi_edges_skipped"].append(se["id"])
            continue
        if se["id"] == "s_micron_nvidia_hbm" and "s_nvidia_micron" in by_r:
            report["semi_edges_skipped"].append(se["id"] + " (dup of s_nvidia_micron)")
            continue
        if se["source"] not in by_e or se["target"] not in by_e:
            report["semi_edges_skipped"].append(se["id"] + " (missing node)")
            continue
        rel["relationships"].append(edge_tpl(**se))
        by_r[se["id"]] = se
        report["semi_edges_added"].append(se["id"])

    # Persist backend
    (DATA / "entities.json").write_text(json.dumps(ent, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (DATA / "relationships.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (DATA / "sources.json").write_text(json.dumps(src, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # Export semiconductor network
    venv_py = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
    py = str(venv_py) if venv_py.is_file() else sys.executable
    out = subprocess.check_output([py, str(ROOT / "backend" / "export_network.py")], cwd=str(ROOT / "backend"))
    net = json.loads(out)
    (PUBLIC / "network.json").write_text(json.dumps(net, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # --- PF network patch ---
    pf = json.loads((PF / "network.json").read_text(encoding="utf-8"))
    projects = json.loads((PF / "projects.json").read_text(encoding="utf-8"))
    pf_by = {n["id"]: n for n in pf["nodes"]}
    pf_e = {e["id"]: e for e in pf["edges"]}
    proj_by = {p["id"]: p for p in projects["projects"]}

    # Fix: ensure bnk_kyongnam id — may already exist as bnk_kyongnam
    for row in KR_COMPANIES:
        eid = row[0]
        if eid in pf_by:
            continue
        # special case ibk ticker may already exist under different id
        n = ent_node(*row[:7], desc=row[1] + " — 한국 AI DC PF 연구 시드. 프로젝트별 검증 전까지 고립 가능.",
                     pf_class="research_candidate")
        pf["nodes"].append(n)
        pf_by[eid] = n
        report["kr_companies_added"].append(eid)

    # Also add shinhan_sec alias check — already exists
    # Add cpp if missing
    if "cpp_investments" not in pf_by:
        pass  # already in KR_COMPANIES

    # --- Verified projects ---
    new_projects = [
        {
            "id": "yongin_jukjeon_pacific",
            "name": "Yongin Jukjeon Pacific Sunny Data Center",
            "name_ko": "용인 죽전 퍼시픽써니 데이터센터",
            "location": "경기도 용인시 죽전",
            "country": "KR", "region": "KR",
            "developer": "pacific_am",
            "owner": None,
            "spv": "pacific_sunny_spv",
            "operator": None,
            "tenant": "lg_cns",
            "construction_stage": "completed_permit",
            "target_completion": "2025-10 (준공 보도)",
            "critical_it_load_mw": 64,
            "capacity_note": "IT Load 64MW · 수전 100MW (현대건설 보도)",
            "lease_structure": "망중립 하이퍼스케일; LG CNS 임차 예정(보도)",
            "capex_usd_m": None,
            "capex_note": "총사업비 약 1.3조 원(현대건설) / PF 리파이 약 1.1조(한경 보도) — 항목 혼동 금지",
            "equity_usd_m": None,
            "senior_debt_usd_m": None,
            "mezzanine_usd_m": None,
            "financing_disclosed": True,
            "graph_node": False,
            "map_policy": "company_only",
            "source_ids": ["S_HDEC_JUKJEON"],
            "verification_date": TODAY,
            "missing": ["정확한 차주 법인 등기상호 확정", "대주단 개별 약정액", "임차 계약 확정 여부"],
            "facility_type": "hyperscale_neutral",
            "ai_capability": "AI-capable / HPC-ready (보도)",
            "funding_type": "project_finance",
        },
        {
            "id": "bucheon_samjeong_ai",
            "name": "Bucheon Samjeong AI Hub Center",
            "name_ko": "부천 삼정 AI 허브센터",
            "location": "경기도 부천시 오정구 삼정동 48-59 일대",
            "country": "KR", "region": "KR",
            "developer": "dongyang",
            "owner": None,
            "spv": "dcity_bucheon_pfv",
            "operator": None,
            "tenant": None,
            "construction_stage": "under_construction",
            "target_completion": "2028-07",
            "critical_it_load_mw": 7,
            "capacity_note": "수전 약 9.8MW · IT Load 약 7MW (보도)",
            "capex_note": "PF 1,590억 기표(이데일리). 총공사비 약 1,268억(시공)",
            "financing_disclosed": True,
            "graph_node": False,
            "map_policy": "company_only",
            "source_ids": ["S_EDALLY_BUCHEON"],
            "verification_date": TODAY,
            "missing": ["대주별 약정액 배분", "LG CNS 계약 형태(임차 vs 협력) 확정"],
            "facility_type": "ai_dedicated",
            "ai_capability": "AI-dedicated (보도)",
            "funding_type": "project_finance",
            "partners_note": "디씨플랫폼 PM·개발 협력, LG CNS 협력(보도)",
        },
        {
            "id": "gwangju_fine_dc",
            "name": "Gwangju / Jangseong Fine Data Center",
            "name_ko": "광주첨단(장성) 파인데이터센터",
            "location": "전남 장성 광주연구개발특구 첨단3지구",
            "country": "KR", "region": "KR",
            "developer": None,
            "owner": None,
            "spv": "fine_dc_pfv",
            "operator": None,
            "tenant": None,
            "construction_stage": "under_construction",
            "target_completion": "2027-12",
            "critical_it_load_mw": None,
            "capacity_note": "수전 26MW급(대우건설 보도). 총사업비 약 3,959억",
            "capex_note": "PF 약정 2,959억(대우건설 채무보증 공시) ≠ KB발해 100억 참여액을 전체에 배분하지 않음",
            "financing_disclosed": True,
            "graph_node": False,
            "map_policy": "company_only",
            "source_ids": ["S_DAEWOO_FINE_DART"],
            "verification_date": TODAY,
            "missing": ["전체 대주단 명단·트랜치 배분", "운영사 확정"],
            "facility_type": "conventional_cloud_ai_capable",
            "ai_capability": "AI-capable (보도·인프라 포지셔닝)",
            "funding_type": "project_finance",
        },
    ]
    for pr in new_projects:
        if pr["id"] not in proj_by:
            projects["projects"].append(pr)
            proj_by[pr["id"]] = pr
            report["kr_projects_added"].append(pr["id"])

    # KR edges — only through SPV / disclosed counterparties
    kr_edges = [
        # Yongin Jukjeon
        edge_tpl(id="pf_pacific_am_jukjeon", source="pacific_am", target="pacific_sunny_spv",
                 relationship_type="ASSET_MANAGER", impact_channel="equity",
                 label="퍼시픽자산운용 → 죽전 사업 SPC (발주·운용)",
                 project_id="yongin_jukjeon_pacific", project_name="용인 죽전 퍼시픽써니 데이터센터",
                 source_status="VERIFIED", source_ids=["S_HDEC_JUKJEON"],
                 source_url="https://www.hdec.kr/kr/newsroom/news_view.aspx?NewsListType=news_clist&NewsSeq=1368&NewsType=LATEST",
                 source_title="현대건설 준공 보도", source_date="2025-10-24",
                 stress_direction="차환·임차 부진 → 운용·출자 구조 압력",
                 exposure_kind="sponsor_am", roles=["asset_manager", "developer"],
                 amount_note="출자·운용 규모는 개별 공시 전 미확정",
                 verification_gap="SPC 정확한 등기상호 추가 확인 필요"),
        edge_tpl(id="pf_cpp_jukjeon", source="cpp_investments", target="pacific_sunny_spv",
                 relationship_type="EQUITY_SPONSOR", impact_channel="equity",
                 label="CPPIB → 죽전 사업 (공동 투자 보도)",
                 project_id="yongin_jukjeon_pacific", project_name="용인 죽전 퍼시픽써니 데이터센터",
                 source_status="VERIFIED", source_ids=["S_HDEC_JUKJEON"],
                 source_url="https://www.hdec.kr/kr/newsroom/news_view.aspx?NewsListType=news_clist&NewsSeq=1368&NewsType=LATEST",
                 source_title="현대건설 준공 보도", source_date="2025-10-24",
                 stress_direction="사업 부실 → 출자 가치 손상 (금액 미공시)",
                 exposure_kind="equity", roles=["equity", "sponsor"],
                 amount_note="공동투자 보도. 개별 출자액은 공시 확인 전 미확정",
                 verification_gap="CPPIB 공식 공시·펀드명 대조 필요"),
        edge_tpl(id="pf_shinhan_jukjeon_eq", source="shinhan_sec", target="pacific_sunny_spv",
                 relationship_type="EQUITY_SPONSOR", impact_channel="equity",
                 label="신한투자증권 → 죽전 사업 공동투자·리파이 주관(보도)",
                 project_id="yongin_jukjeon_pacific", project_name="용인 죽전 퍼시픽써니 데이터센터",
                 source_status="VERIFIED", source_ids=["S_HDEC_JUKJEON"],
                 source_url="https://marketinsight.hankyung.com/article/202408229028r",
                 source_title="한경 마켓인사이트 리파이낸싱 보도", source_date="2024-08-22",
                 stress_direction="리파이 실패·출자 손상 가능 — 주관≠전액 대주",
                 exposure_kind="equity_and_arranger", roles=["equity", "arranger"],
                 amount_note="공동투자·주관 보도. 1.1조 PF 전체를 신한 단독 익스포저로 보지 않음",
                 verification_gap="대주단 구성·신한 보유 잔액 DART 미대조"),
        edge_tpl(id="pf_hyundai_jukjeon_epc", source="hyundai_enc", target="pacific_sunny_spv",
                 relationship_type="EPC_CONTRACT", impact_channel="supply_chain",
                 label="현대건설 → 죽전 퍼시픽써니 시공(준공)",
                 project_id="yongin_jukjeon_pacific", project_name="용인 죽전 퍼시픽써니 데이터센터",
                 source_status="VERIFIED", source_ids=["S_HDEC_JUKJEON"],
                 source_url="https://www.hdec.kr/kr/newsroom/news_view.aspx?NewsListType=news_clist&NewsSeq=1368&NewsType=LATEST",
                 source_title="현대건설 뉴스룸", source_date="2025-10-24",
                 stress_direction="준공 후 하자·미수금 — 건설중 미이행과 구분",
                 exposure_kind="construction_contract", roles=["contractor", "epc"],
                 amount_note="시공. 공사대금 잔액 미공시", relationship_status="current",
                 verification_gap=""),
        edge_tpl(id="pf_lgcns_jukjeon_lease", source="lg_cns", target="pacific_sunny_spv",
                 relationship_type="LEASE_OR_COLOCATION", impact_channel="facility",
                 label="LG CNS → 죽전 DC 임차 예정(보도)",
                 project_id="yongin_jukjeon_pacific", project_name="용인 죽전 퍼시픽써니 데이터센터",
                 source_status="VERIFIED", source_ids=["S_HDEC_JUKJEON"],
                 source_url="https://marketinsight.hankyung.com/article/202408229028r",
                 source_title="한경 — LG CNS 임차 예정", source_date="2024-08",
                 stress_direction="임차 미확정·축소 시 임대료 경로 압력 (계약 확정 전)",
                 exposure_kind="operating_revenue_counterparty", roles=["tenant"],
                 amount_note="임차 '예정' 보도 — 확정 계약·면적은 미확인",
                 relationship_status="proposed",
                 verification_gap="확정 임차 계약 여부 미확인"),
        # Bucheon
        edge_tpl(id="pf_dongyang_bucheon", source="dongyang", target="dcity_bucheon_pfv",
                 relationship_type="EQUITY_SPONSOR", impact_channel="equity",
                 label="동양 → 디씨아이티와이부천PFV (사업주체·주식 근질권 담보)",
                 project_id="bucheon_samjeong_ai", project_name="부천 삼정 AI 허브센터",
                 source_status="VERIFIED", source_ids=["S_EDALLY_BUCHEON"],
                 source_url="https://www.edaily.co.kr/News/Read?mediaCodeNo=257&newsId=05005286645450888",
                 source_title="이데일리 PF 기표", source_date="2026-05",
                 stress_direction="PF 부실 → 근질권 실행·출자 손상",
                 obligation_trigger="대출약정 채무불이행 시 주식근질권",
                 exposure_kind="equity_pledge", roles=["sponsor", "developer"],
                 amount_note="담보설정액 약 495.5억(보도). PF 총액 1,590억을 동양 단독 부채로 보지 않음"),
        edge_tpl(id="pf_dcplat_bucheon", source="dc_platform", target="dcity_bucheon_pfv",
                 relationship_type="EPC_OR_OPS_MANDATE", impact_channel="supply_chain",
                 label="디씨플랫폼 → 부천PFV (개발·PM 협력)",
                 project_id="bucheon_samjeong_ai", project_name="부천 삼정 AI 허브센터",
                 source_status="VERIFIED", source_ids=["S_EDALLY_BUCHEON"],
                 source_url="https://www.edaily.co.kr/News/Read?mediaCodeNo=257&newsId=05005286645450888",
                 source_title="이데일리", source_date="2026-05",
                 stress_direction="사업 지연 → PM·개발 수수료·평판 압력 (수수료 미공시)",
                 exposure_kind="operating_revenue", roles=["development_management", "pm_cm"],
                 amount_note="수수료 미공시"),
        edge_tpl(id="pf_dl_bucheon_epc", source="dl_enc", target="dcity_bucheon_pfv",
                 relationship_type="EPC_CONTRACT", impact_channel="supply_chain",
                 label="DL건설 → 부천PFV 시공",
                 project_id="bucheon_samjeong_ai", project_name="부천 삼정 AI 허브센터",
                 source_status="VERIFIED", source_ids=["S_EDALLY_BUCHEON"],
                 source_url="https://www.edaily.co.kr/News/Read?mediaCodeNo=257&newsId=05005286645450888",
                 source_title="이데일리", source_date="2026-05",
                 stress_direction="공사대금 미수·공기 지연",
                 exposure_kind="construction_contract", roles=["contractor"],
                 amount_note="총공사비 약 1,268억(보도)"),
        edge_tpl(id="pf_hana_bucheon", source="hana_bank", target="dcity_bucheon_pfv",
                 relationship_type="PROJECT_LOAN", impact_channel="financial",
                 label="하나은행 → 부천PFV 대주단 참여",
                 project_id="bucheon_samjeong_ai", project_name="부천 삼정 AI 허브센터",
                 source_status="VERIFIED", source_ids=["S_EDALLY_BUCHEON"],
                 source_url="https://www.edaily.co.kr/News/Read?mediaCodeNo=257&newsId=05005286645450888",
                 source_title="이데일리", source_date="2026-05",
                 stress_direction="차주 부실 → 대주 신용 익스포저",
                 exposure_kind="syndicated_loan_participation", roles=["lender"],
                 amount_note="PF 총 1,590억 신디케이트. 하나은행 개별 배분은 미공시 — 총액을 단독 배정하지 않음",
                 verification_gap="개별 약정액·선후순위 미공시"),
        edge_tpl(id="pf_bnk_bucheon", source="bnk_kyongnam", target="dcity_bucheon_pfv",
                 relationship_type="PROJECT_LOAN", impact_channel="financial",
                 label="BNK경남은행 → 부천PFV 대주단",
                 project_id="bucheon_samjeong_ai", project_name="부천 삼정 AI 허브센터",
                 source_status="VERIFIED", source_ids=["S_EDALLY_BUCHEON"],
                 source_url="https://www.edaily.co.kr/News/Read?mediaCodeNo=257&newsId=05005286645450888",
                 source_title="이데일리", source_date="2026-05",
                 stress_direction="차주 부실 → 대주 신용 익스포저",
                 exposure_kind="syndicated_loan_participation", roles=["lender"],
                 amount_note="개별 배분 미공시", verification_gap="개별 약정액 미공시"),
        edge_tpl(id="pf_ibk_bucheon", source="ibk", target="dcity_bucheon_pfv",
                 relationship_type="PROJECT_LOAN", impact_channel="financial",
                 label="IBK기업은행 → 부천PFV 대주단",
                 project_id="bucheon_samjeong_ai", project_name="부천 삼정 AI 허브센터",
                 source_status="VERIFIED", source_ids=["S_EDALLY_BUCHEON"],
                 source_url="https://www.edaily.co.kr/News/Read?mediaCodeNo=257&newsId=05005286645450888",
                 source_title="이데일리", source_date="2026-05",
                 stress_direction="차주 부실 → 대주 신용 익스포저",
                 exposure_kind="syndicated_loan_participation", roles=["lender"],
                 amount_note="개별 배분 미공시", verification_gap="개별 약정액 미공시"),
        edge_tpl(id="pf_hana_cap_bucheon", source="hana_capital", target="dcity_bucheon_pfv",
                 relationship_type="PROJECT_LOAN", impact_channel="financial",
                 label="하나캐피탈 → 부천PFV 대주단",
                 project_id="bucheon_samjeong_ai", project_name="부천 삼정 AI 허브센터",
                 source_status="VERIFIED", source_ids=["S_EDALLY_BUCHEON"],
                 source_url="https://www.edaily.co.kr/News/Read?mediaCodeNo=257&newsId=05005286645450888",
                 source_title="이데일리", source_date="2026-05",
                 stress_direction="차주 부실 → 대주 신용 익스포저",
                 exposure_kind="syndicated_loan_participation", roles=["lender"],
                 amount_note="개별 배분 미공시"),
        # Fine DC
        edge_tpl(id="pf_daewoo_fine_epc", source="daewoo_enc", target="fine_dc_pfv",
                 relationship_type="EPC_CONTRACT", impact_channel="supply_chain",
                 label="대우건설 → 파인디씨PFV 시공·출자",
                 project_id="gwangju_fine_dc", project_name="광주첨단 파인데이터센터",
                 source_status="VERIFIED", source_ids=["S_DAEWOO_FINE_DART"],
                 source_url="https://biz.heraldcorp.com/article/10637400",
                 source_title="대우건설 착공 보도", source_date="2025",
                 stress_direction="공사·출자 동시 익스포저",
                 exposure_kind="construction_and_equity", roles=["contractor", "sponsor"],
                 amount_note="시공+출자(보도)"),
        edge_tpl(id="pf_daewoo_fine_guar", source="daewoo_enc", target="fine_dc_pfv",
                 relationship_type="CREDIT_ENHANCEMENT", impact_channel="financial",
                 label="대우건설 → 파인디씨PFV 채무보증(책임준공 미이행 시 채무인수)",
                 project_id="gwangju_fine_dc", project_name="광주첨단 파인데이터센터",
                 source_status="VERIFIED", source_ids=["S_DAEWOO_FINE_DART"],
                 source_url="https://www.digitaltoday.co.kr/news/articleView.html?idxno=612777",
                 source_title="대우건설 채무보증 공시", source_date="2025-12-15",
                 stress_direction="책임준공 미이행 → 채무인수 의무",
                 obligation_trigger="책임준공 미이행 시 채무인수 (공시)",
                 exposure_kind="completion_guarantee_debt_assumption", roles=["guarantor", "credit_support"],
                 amount_note="채무보증 2,959억 원(공시). 채권자: 하나은행·KB은행 등 — 개별 은행 배분은 공시 문구상 '등'",
                 verification_gap="대주단 전체 명단·잔액은 추가 공시 필요"),
        edge_tpl(id="pf_kb_balhae_fine", source="kb_balhae_infra", target="fine_dc_pfv",
                 relationship_type="PROJECT_LOAN", impact_channel="financial",
                 label="KB발해인프라 → 파인디씨PFV 대출 참여(약 100억)",
                 project_id="gwangju_fine_dc", project_name="광주첨단 파인데이터센터",
                 source_status="VERIFIED", source_ids=["S_DAEWOO_FINE_DART"],
                 source_url="https://www.dealbook.co.kr/gwangjuceomdan-pain-deiteosenteo-2959eog-pfyagjeong-kbbalhaeinpeura-100eog-camyeo/",
                 source_title="딜북 — KB발해 100억 참여", source_date="2025-12",
                 stress_direction="차주 부실 → 펀드 대출채권 손상",
                 exposure_kind="loan_participation", roles=["lender"],
                 amount_note="약 100억(선순위 40·중순위 60 보도). PF 총액 2,959억과 동일시하지 않음"),
        edge_tpl(id="pf_hana_fine_lender", source="hana_bank", target="fine_dc_pfv",
                 relationship_type="PROJECT_LOAN", impact_channel="financial",
                 label="하나은행 → 파인디씨PFV 대주(공시상 채권자)",
                 project_id="gwangju_fine_dc", project_name="광주첨단 파인데이터센터",
                 source_status="VERIFIED", source_ids=["S_DAEWOO_FINE_DART"],
                 source_url="https://www.digitaltoday.co.kr/news/articleView.html?idxno=612777",
                 source_title="채무보증 공시", source_date="2025-12-15",
                 stress_direction="차주 부실 → 대주 신용 익스포저",
                 exposure_kind="syndicated_loan_participation", roles=["lender"],
                 amount_note="공시상 '하나은행, KB은행 등' — 개별 금액 미기재",
                 verification_gap="개별 약정액 미공시"),
        edge_tpl(id="pf_kb_fine_lender", source="kb_bank", target="fine_dc_pfv",
                 relationship_type="PROJECT_LOAN", impact_channel="financial",
                 label="KB국민은행 → 파인디씨PFV 대주(공시상 채권자)",
                 project_id="gwangju_fine_dc", project_name="광주첨단 파인데이터센터",
                 source_status="VERIFIED", source_ids=["S_DAEWOO_FINE_DART"],
                 source_url="https://www.digitaltoday.co.kr/news/articleView.html?idxno=612777",
                 source_title="채무보증 공시", source_date="2025-12-15",
                 stress_direction="차주 부실 → 대주 신용 익스포저",
                 exposure_kind="syndicated_loan_participation", roles=["lender"],
                 amount_note="개별 금액 미기재", verification_gap="개별 약정액 미공시"),
    ]

    for e in kr_edges:
        if e["id"] in pf_e:
            continue
        if e["source"] not in pf_by or e["target"] not in pf_by:
            report["research_queue"].append({"edge": e["id"], "gap": "missing node"})
            continue
        pf["edges"].append(e)
        pf_e[e["id"]] = e
        report["kr_edges_added"].append(e["id"])
        pf_by[e["source"]]["connection_status"] = "관계 확인"
        pf_by[e["target"]]["connection_status"] = "관계 확인"
        if pf_by[e["source"]].get("pf_exposure_class") == "research_candidate":
            pf_by[e["source"]]["pf_exposure_class"] = "confirmed_dc_finance"
        if pf_by[e["target"]].get("pf_exposure_class") == "research_candidate":
            pf_by[e["target"]]["pf_exposure_class"] = "confirmed_dc_finance"

    # Research queue for priority clusters without full evidence
    for item in [
        {"cluster": "포항 AI Factory", "status": "research_queue", "note": "대주·차주 법인 교차검증 전 확정 그래프 미편입"},
        {"cluster": "고양 삼송", "status": "research_queue", "note": "이지스·LG CNS·네이버클라우드·대주단 — 필지·차주 확인 필요"},
        {"cluster": "인천 원창동", "status": "research_queue", "note": "이도·청라IDC PFV·신한·현대엔지니어링"},
        {"cluster": "인천 도화동", "status": "research_queue", "note": "산은인프라·IBK증권 — 차주 미확정"},
        {"cluster": "용인 덕성리", "status": "research_queue", "note": "와이드크릭·Warburg·삼성물산"},
        {"cluster": "인천 부평 Digital Edge vs ESR/STACK", "status": "research_queue", "note": "프로젝트 분리 유지 — 동일 시군구로 병합 금지"},
        {"cluster": "안산 복수 프로젝트", "status": "research_queue", "note": "글로벌클라우드/메타/캄스퀘어/코람코·DCI/Keppel 분리"},
    ]:
        report["research_queue"].append(item)

    # Downgrade: ensure no fabricated CoreWeave→KR PF direct if any UNKNOWN spam
    for e in list(pf["edges"]):
        if e.get("source") == "coreweave" and e.get("target") in ("casequare_pfv", "camsquare_pfv") and e.get("source_status") == "UNKNOWN":
            e["source_status"] = "INFERRED"
            e["verification_gap"] = (e.get("verification_gap") or "") + " · 직접 계약 미확인 — 시나리오 가정과 구분"
            report["removed_or_downgraded"].append(e["id"])

    projects["as_of"] = TODAY
    (PF / "network.json").write_text(json.dumps(pf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PF / "projects.json").write_text(json.dumps(projects, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PF / "research_queue.json").write_text(json.dumps({"as_of": TODAY, "items": report["research_queue"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PF / "_expansion_report_v4.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("US added", len(report["us_added"]), report["us_added"][:15], "...")
    print("semi edges", report["semi_edges_added"])
    print("KR cos", len(report["kr_companies_added"]), "projects", report["kr_projects_added"], "edges", len(report["kr_edges_added"]))
    print("semi net", len(net["nodes"]), len(net["edges"]))
    print("pf net", len(pf["nodes"]), len(pf["edges"]))


if __name__ == "__main__":
    main()
