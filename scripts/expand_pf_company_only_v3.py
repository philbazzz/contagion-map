#!/usr/bin/env python3
"""
Company-only Korean AI Data Center PF map:
- Remove facility/project/permit/aggregate nodes from the graph
- Keep SPVs under legal company names
- Add verified CSPs, operators, PM-capable firms, 한화투자증권, etc.
- Add evidence-backed company-to-company edges only
- Preserve projects.json as metadata (not map nodes)
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PF = ROOT / "frontend" / "public" / "data" / "pf"
TODAY = date.today().isoformat()


def node(
    id: str,
    name_ko: str,
    name_en: str,
    *,
    group: str,
    entity_type: str,
    role: str,
    roles: list[str],
    listed: bool = False,
    ticker: str | None = None,
    exchange: str | None = None,
    description: str = "",
    pf_exposure_class: str = "research_candidate",
    connection_status: str = "연결관계 확인 필요",
) -> dict:
    return {
        "id": id,
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
        "quote_currency": "KRW" if listed and exchange in ("KRX", "KOSPI", "KOSDAQ") else ("USD" if listed else None),
        "listing_note": None if listed else "비상장",
        "display_size": 5 if entity_type == "spv" else 6,
        "source_status": "VERIFIED",
        "source_ids": ["S_PF_COMPANY_V3"],
        "key_drivers": roles[:3],
        "region": "KR",
        "country": "KR",
        "pf_exposure_class": pf_exposure_class,
        "pf_exposure_class_num": {"confirmed_aidc_project": 1, "confirmed_dc_finance": 2, "general_pf": 3, "sector_sensitivity": 4, "research_candidate": 5}.get(pf_exposure_class, 5),
        "connection_status": connection_status,
        "is_company": True,
    }


def edge(
    eid: str,
    src: str,
    tgt: str,
    rel: str,
    label: str,
    *,
    channel: str = "financial",
    status: str = "VERIFIED",
    amount: float | None = None,
    amount_note: str = "",
    project_id: str | None = None,
    project_name: str | None = None,
    transmission: str = "direct_contract",
    evidence_level: int = 2,
    stress_direction: str = "",
    obligation_trigger: str = "",
    exposure_kind: str = "",
    relationship_status: str = "current",
    source_url: str = "",
    source_title: str = "",
    source_date: str = "",
    roles: list[str] | None = None,
    impact_label: str = "",
    verification_gap: str | None = None,
) -> dict:
    if verification_gap is None:
        verification_gap = "" if status == "VERIFIED" else "추가 원문·DART 대조 권장"
    return {
        "id": eid,
        "source": src,
        "target": tgt,
        "relationship_type": rel,
        "impact_channel": channel,
        "label": label,
        "impact_label": impact_label or label,
        "source_status": status,
        "source_ids": ["S_PF_EVIDENCE_V3"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": amount,
        "amount_note": amount_note,
        "roles": roles or [],
        "transmission_class": transmission,
        "evidence_level": evidence_level,
        "project_id": project_id,
        "project_name": project_name,
        "stress_direction": stress_direction,
        "obligation_trigger": obligation_trigger,
        "exposure_kind": exposure_kind,
        "relationship_status": relationship_status,
        "source_url": source_url,
        "source_title": source_title,
        "source_date": source_date,
        "verification_date": TODAY,
        "verification_gap": verification_gap,
    }


def main() -> None:
    net = json.loads((PF / "network.json").read_text(encoding="utf-8"))
    proj = json.loads((PF / "projects.json").read_text(encoding="utf-8"))
    by = {n["id"]: n for n in net["nodes"]}

    # ---- 1. Identify non-company nodes to remove from graph ----
    remove_ids = set()
    for n in net["nodes"]:
        et = n.get("entity_type") or ""
        gid = n["id"]
        if et in ("project", "operating_asset", "market_aggregate", "facility", "permit"):
            remove_ids.add(gid)
        if gid.startswith("kr_permit_") or gid == "kr_pf_market":
            remove_ids.add(gid)
        if et == "project" and n.get("group") == "project_finance":
            remove_ids.add(gid)

    # Keep legal SPVs (entity_type spv) — they are companies
    remove_ids = {i for i in remove_ids if by.get(i, {}).get("entity_type") != "spv"}

    report = {
        "removed_nodes": sorted(remove_ids),
        "added_companies": [],
        "added_edges": [],
        "remapped_edges": [],
        "isolated_new": [],
        "evidence_gaps": [],
    }

    # ---- 2. Remap edges that touched removed nodes ----
    # Known facility → company remaps for KR operating assets / projects
    FACILITY_COMPANY = {
        # Hostway Bundang: tenant Hostway, operator Sejong — no single owner SPC in graph
        "bundang_hostway_idc": None,
        "casequare_gasan": "casequare_pfv",
        "camsquare_ansan": "camsquare_pfv",
        "sds_gumi_aidc": "samsung_sds",
        "skt_ulsan_aidc": "sk_telecom",
        # US campuses → primary developer/landlord company when known
        "polaris_forge_1": "applied_digital",
        "helios_campus": "galaxy_digital",
        "corz_cw_sites": "core_scientific",
    }

    new_edges = []
    for e in net["edges"]:
        s, t = e["source"], e["target"]
        if s not in remove_ids and t not in remove_ids:
            # Drop ASSUMED funding-market edges to/from aggregate (already removed)
            if e.get("source_status") == "ASSUMED" and e.get("relationship_type") == "FUNDING_MARKET":
                if "kr_pf_market" in (s, t) or s == "coreweave" and t.startswith("kr_"):
                    report["remapped_edges"].append(f"DROP_ASSUMED {e['id']}")
                    continue
            new_edges.append(e)
            continue

        # Try remap
        ns = FACILITY_COMPANY.get(s, s)
        nt = FACILITY_COMPANY.get(t, t)
        if s in remove_ids:
            ns = FACILITY_COMPANY.get(s)
        if t in remove_ids:
            nt = FACILITY_COMPANY.get(t)

        # Special Hostway facility edges → company-company
        if "bundang_hostway_idc" in (s, t):
            other = s if t == "bundang_hostway_idc" else t
            rel = e.get("relationship_type")
            if other == "hostway_kr" and rel == "TENANT_LEASE":
                # tenant alone without landlord company — keep Hostway, no edge fabricated
                report["remapped_edges"].append("hostway_tenant: facility node removed; landlord SPC not disclosed as separate company — no fabricated edge")
                report["evidence_gaps"].append("분당 호스트웨이: 임차인(호스트웨이)은 확인되나 현재 소유 SPC 법인명이 그래프에 없어 임차 대향 회사 엣지 미생성")
                continue
            if other == "sejong_telecom" and rel == "OPERATOR":
                new_edges.append(edge(
                    "pf_sejong_hostway_ops", "sejong_telecom", "hostway_kr",
                    "FACILITY_OPERATION", "세종텔레콤 → 호스트웨이 (분당 IDC 운영·임차 시설)",
                    channel="facility", status="INFERRED", evidence_level=2,
                    project_id="bundang_hostway_idc", project_name="분당 호스트웨이 IDC",
                    stress_direction="임차인 매출/운영 차질 → 운영사 수수료·운영수입 압력 (정성)",
                    exposure_kind="operating_revenue",
                    relationship_status="current",
                    source_url="", source_title="기존 네트워크 메타데이터 (운영사 추론)", source_date="",
                    amount_note="금액 미공시",
                ))
                report["remapped_edges"].append("sejong↔hostway facility ops")
                continue
            if other in ("igis_am", "fine_partners_am", "hana_alt_am"):
                # AM/equity related to facility — attach as metadata edge to hostway only if commercial link exists
                # Prior owner / AM without bilateral contract to tenant → keep company, no forced edge to Hostway
                report["remapped_edges"].append(f"{other}: facility edge dropped; company retained as isolated/sector pending ownership SPC disclosure")
                report["evidence_gaps"].append(f"{other}: 분당 Hostway 자산운용·지분 관계는 시설 노드 기준이었음. 소유 SPC 법인 확인 전까지 회사↔회사 엣지 보류")
                continue
            continue

        if ns and nt and ns != nt and ns not in remove_ids and nt not in remove_ids:
            ne = deepcopy(e)
            ne["source"], ne["target"] = ns, nt
            ne["id"] = e["id"] + "_co"
            # avoid PROJECT_SPV self loops
            if ne.get("relationship_type") == "PROJECT_SPV" and ns == nt:
                report["remapped_edges"].append(f"DROP_SELF {e['id']}")
                continue
            if not any(x["source"] == ns and x["target"] == nt and x.get("relationship_type") == ne.get("relationship_type") for x in new_edges):
                proj_meta = e.get("project_id") or (s if s in remove_ids else t if t in remove_ids else None)
                ne["project_id"] = ne.get("project_id") or proj_meta
                new_edges.append(ne)
                report["remapped_edges"].append(f"{e['id']}: {s}->{t} => {ns}->{nt}")
            continue

        report["remapped_edges"].append(f"DROP {e['id']} {s}->{t} (no company remap)")

    # ---- 3. Drop removed nodes; mark remaining as companies ----
    kept = []
    for n in net["nodes"]:
        if n["id"] in remove_ids:
            continue
        n["is_company"] = True
        if n.get("entity_type") == "spv":
            n["connection_status"] = n.get("connection_status") or "검증된 PFV/SPC"
        elif not any(e["source"] == n["id"] or e["target"] == n["id"] for e in new_edges):
            n["connection_status"] = n.get("connection_status") or "연결관계 확인 필요"
        else:
            n["connection_status"] = n.get("connection_status") or "관계 확인"
        # Normalize roles list
        if "roles" not in n:
            n["roles"] = [n.get("role") or n.get("group") or "company"]
        kept.append(n)
    by = {n["id"]: n for n in kept}

    # ---- 4. Add companies ----
    additions = [
        node("hanwha_inv_sec", "한화투자증권", "Hanwha Investment & Securities",
             group="kr_securities", entity_type="securities", role="증권 · 금융주선·대주(검증 건)",
             roles=["securities", "arranger", "lender"], listed=True, ticker="003530", exchange="KRX",
             description="용인 캄스퀘어 하이퍼스케일 DC 브릿지론 금융주관·선순위 대주(보도). 일반 증권사라는 이유만으로 타 PF에 연결하지 않음.",
             pf_exposure_class="confirmed_dc_finance", connection_status="관계 확인"),
        node("camsquare_yongin_pfv", "캄스퀘어용인데이터센터PFV", "Camsquare Yongin Data Center PFV",
             group="project_finance", entity_type="spv", role="용인 지곡 하이퍼스케일 DC 시행 PFV",
             roles=["spv", "borrower", "developer_vehicle"], listed=False,
             description="한국대체투자자산운용이 설립한 용인 지곡동 하이퍼스케일 데이터센터 시행법인(보도).",
             pf_exposure_class="confirmed_aidc_project", connection_status="관계 확인"),
        node("lg_uplus", "LG유플러스", "LG Uplus",
             group="kr_operator", entity_type="company", role="통신·IDC 운영 (CSP/운영)",
             roles=["csp", "operator", "telecom"], listed=True, ticker="032640", exchange="KRX",
             description="케이스퀘어 가산 데이터센터 위탁운영(2025 보도). 자체 IDC 운영.",
             pf_exposure_class="confirmed_dc_finance", connection_status="관계 확인"),
        node("kinx", "KINX", "KINX",
             group="kr_operator", entity_type="company", role="IX·코로케이션 운영",
             roles=["operator", "connectivity", "colocation"], listed=True, ticker="053110", exchange="KRX",
             description="수도권 다수 IDC 운영·CloudHub. 특정 DC PF 대주 관계는 본 데이터셋에서 미검증.",
             pf_exposure_class="sector_sensitivity", connection_status="연결관계 확인 필요"),
        node("gabia", "가비아", "Gabia",
             group="kr_operator", entity_type="company", role="호스팅·IDC 서비스",
             roles=["operator", "hosting", "csp_adjacent"], listed=True, ticker="079940", exchange="KRX",
             description="가산 등 IDC 서비스(자체/제휴 센터). 특정 PF 여신 관계는 미검증.",
             pf_exposure_class="sector_sensitivity", connection_status="연결관계 확인 필요"),
        node("nhn_cloud", "NHN클라우드", "NHN Cloud",
             group="kr_operator", entity_type="company", role="국내 CSP",
             roles=["csp", "cloud"], listed=False,
             description="국내 클라우드 서비스 제공. KINX CloudHub 연동 등. 특정 DC PF 금융 익스포저 미검증.",
             pf_exposure_class="sector_sensitivity", connection_status="연결관계 확인 필요"),
        node("kt_cloud", "KT클라우드", "KT Cloud",
             group="kr_operator", entity_type="company", role="국내 CSP·IDC",
             roles=["csp", "operator", "cloud"], listed=False,
             description="KT 계열 클라우드·IDC. 모회사 KT와 별도 법인으로 구분. 케이스퀘어 초기 구축·운영 위탁은 KT 보도(역사).",
             pf_exposure_class="sector_sensitivity", connection_status="연결관계 확인 필요"),
        node("digital_edge_kr", "디지털엣지코리아", "Digital Edge Korea",
             group="kr_operator", entity_type="company", role="데이터센터 개발·운영",
             roles=["developer", "operator", "owner"], listed=False,
             description="SEL1/SEL2 등 국내 DC 개발·운영사(업계 DB). 개별 PF 대주단은 본 작업에서 DART 미완전 대조.",
             pf_exposure_class="research_candidate", connection_status="연결관계 확인 필요"),
        node("sk_broadband", "SK브로드밴드", "SK Broadband",
             group="kr_operator", entity_type="company", role="통신·IDC",
             roles=["operator", "telecom", "csp_adjacent"], listed=False,
             description="IDC·네트워크. 특정 신규 DC PF 참여는 미검증.",
             pf_exposure_class="sector_sensitivity", connection_status="연결관계 확인 필요"),
        node("lg_cns", "LG CNS", "LG CNS",
             group="kr_operator", entity_type="company", role="IT서비스·IDC 운영",
             roles=["operator", "it_services", "csp_adjacent"], listed=False,
             description="가산·상암 등 IDC 운영(업계 DB). PF 대주 관계는 미검증.",
             pf_exposure_class="sector_sensitivity", connection_status="연결관계 확인 필요"),
        node("hanwha_corp", "한화", "Hanwha Corporation",
             group="kr_construction", entity_type="company", role="시공·자금보충(영등포 DC)",
             roles=["contractor", "credit_support", "sponsor_adjacent"], listed=True, ticker="000880", exchange="KRX",
             description="영등포 Y-eDC(엣지코어PFV) 관련 자금보충·채무인수 가능 구조(KIS 평가·보도). 시공사 예정.",
             pf_exposure_class="confirmed_dc_finance", connection_status="관계 확인"),
        node("edgecore_pfv", "엣지코어피에프브이", "EdgeCore PFV",
             group="project_finance", entity_type="spv", role="영등포 데이터센터 시행 PFV",
             roles=["spv", "borrower"], listed=False,
             description="한화 영등포 데이터센터 개발 시행법인. 브릿지/유동화 차주(보도·신용평가).",
             pf_exposure_class="confirmed_aidc_project", connection_status="관계 확인"),
        node("hanwha_solutions", "한화솔루션", "Hanwha Solutions",
             group="kr_construction", entity_type="company", role="스폰서(안성 DC)",
             roles=["sponsor", "equity"], listed=True, ticker="009830", exchange="KRX",
             description="자회사 알이씨데이터센터 PF 관련 지분 담보 제공(공시·보도).",
             pf_exposure_class="confirmed_dc_finance", connection_status="관계 확인"),
        node("rec_datacenter", "알이씨데이터센터", "REC Data Center",
             group="project_finance", entity_type="spv", role="안성 데이터센터 시행법인",
             roles=["spv", "borrower", "developer_vehicle"], listed=False,
             description="한화솔루션 안성 데이터센터 시행법인(보도).",
             pf_exposure_class="confirmed_aidc_project", connection_status="관계 확인"),
        node("samoo_cm", "삼우씨엠건축사사무소", "Samoo CM",
             group="kr_construction", entity_type="company", role="CM·설계 (후보)",
             roles=["pm_cm", "design"], listed=False,
             description="대형 복합·특수건축 CM 실적. 특정 AI DC PF CM 계약은 본 데이터셋에서 미검증 — 고립 후보.",
             pf_exposure_class="research_candidate", connection_status="연결관계 확인 필요"),
        node("hanmi_global", "한미글로벌", "HanmiGlobal",
             group="kr_construction", entity_type="company", role="PM/CM",
             roles=["pm_cm", "construction_management"], listed=True, ticker="053690", exchange="KRX",
             description="건설사업관리(CM). 특정 데이터센터 PF CM 수주는 개별 공시 확인 전 고립 유지.",
             pf_exposure_class="research_candidate", connection_status="연결관계 확인 필요"),
        node("naver_cloud", "네이버클라우드", "Naver Cloud",
             group="kr_operator", entity_type="company", role="국내 CSP",
             roles=["csp", "cloud"], listed=False,
             description="네이버 계열 클라우드. 각 세종 DC 등과 연관될 수 있으나 PF 대주 관계는 모회사·별도 공시로 구분 필요.",
             pf_exposure_class="sector_sensitivity", connection_status="연결관계 확인 필요"),
    ]

    for a in additions:
        if a["id"] not in by:
            kept.append(a)
            by[a["id"]] = a
            report["added_companies"].append(a["id"])
            if a.get("connection_status") == "연결관계 확인 필요":
                report["isolated_new"].append(a["id"])

    # Enrich existing KT / kakao roles
    if "kt" in by:
        by["kt"].setdefault("roles", [])
        for r in ["csp", "operator", "telecom"]:
            if r not in by["kt"]["roles"]:
                by["kt"]["roles"].append(r)
        by["kt"]["role"] = "통신·IDC·CSP"
    if "kakao_cloud" in by:
        by["kakao_cloud"].setdefault("roles", [])
        if "csp" not in by["kakao_cloud"]["roles"]:
            by["kakao_cloud"]["roles"].append("csp")

    # ---- 5. Evidence-backed edges ----
    evidence_edges = [
        # Hanwha Investment — Yongin Camsquare bridge (Dealsite): arranger + senior lender 530억
        edge(
            "pf_hanwha_camsq_yongin_bridge", "hanwha_inv_sec", "camsquare_yongin_pfv",
            "PROJECT_LOAN", "한화투자증권 → 캄스퀘어용인PFV 브릿지론 선순위(금융주관)",
            amount=None,
            amount_note="선순위 약 530억 원 (보도). 총 브릿지 600억 중 선순위. 개별 잔액·한도는 DART 원문 미대조 시 확정 표기 보류",
            project_id="camsquare_yongin", project_name="용인 지곡 하이퍼스케일 데이터센터",
            stress_direction="PFV 차환·인허가 지연 → 선순위 대주 신용 익스포저",
            obligation_trigger="대출약정상 기한이익상실·만기 미상환",
            exposure_kind="senior_bridge_loan",
            source_url="https://dealsite.co.kr/articles/157007",
            source_title="한국대체투자운용, 용인 데이터센터 브릿지론 600억 조달 - 딜사이트",
            source_date="2025",
            evidence_level=2, status="VERIFIED",
            roles=["arranger", "senior_lender"],
            verification_gap="딜사이트 보도 기준. 한화투자증권 개별 잔액·약정·담보는 DART 원문 미조회 — 보도 금액은 확정 익스포저로 표기하지 않음.",
        ),
        edge(
            "pf_sksec_camsq_yongin_mezz", "sk_sec", "camsquare_yongin_pfv",
            "PROJECT_LOAN", "SK증권 → 캄스퀘어용인PFV 브릿지론 후순위",
            amount_note="후순위 약 70억 원 (보도)",
            project_id="camsquare_yongin", project_name="용인 지곡 하이퍼스케일 데이터센터",
            stress_direction="선순위 부실 시 후순위 먼저 손상",
            exposure_kind="mezzanine_bridge_loan",
            source_url="https://dealsite.co.kr/articles/157007",
            source_title="딜사이트 용인 브릿지론 보도",
            source_date="2025",
            evidence_level=2, status="VERIFIED",
            roles=["mezz_lender"],
            verification_gap="동일 보도 출처. SK증권 메자닌 잔액·조건은 DART 미대조.",
        ),
        edge(
            "pf_korea_alt_camsq_yongin", "korea_alt_am", "camsquare_yongin_pfv",
            "ASSET_MANAGER", "한국대체투자자산운용 → 캄스퀘어용인PFV (설립·운용)",
            channel="equity",
            project_id="camsquare_yongin", project_name="용인 지곡 하이퍼스케일 데이터센터",
            stress_direction="브릿지 부실·개발 지연 → 운용·출자 구조 압력",
            exposure_kind="sponsor_am",
            source_url="https://dealsite.co.kr/articles/157007",
            source_title="딜사이트",
            source_date="2025",
            evidence_level=2, status="VERIFIED",
            roles=["asset_manager", "sponsor"],
            verification_gap="운용사 역할은 보도로 확인. 지분·수수료·출자 규모는 미공시·DART 미대조.",
        ),
        # Casequare Gasan — LG Uplus operator (2025); Koramco AM already linked
        edge(
            "pf_lguplus_casequare_ops", "lg_uplus", "casequare_pfv",
            "FACILITY_OPERATION", "LG유플러스 → 케이스퀘어PFV 위탁운영(가산 IDC)",
            channel="facility",
            project_id="casequare_gasan", project_name="케이스퀘어 가산 데이터센터",
            stress_direction="임차·가동률 저하 → 위탁운영 수수료·운영 수입 압력 (정성, 수수료 미공시)",
            exposure_kind="operating_revenue",
            source_url="https://zdnet.co.kr/view/?no=20250926172539",
            source_title="코람코 가산 데이터센터 가동 — LG유플러스 운영 (ZDNet)",
            source_date="2025-09-26",
            evidence_level=2, status="VERIFIED",
            roles=["operator"],
            amount_note="위탁운영 수수료 미공시",
            verification_gap="ZDNet 등 보도 기준 위탁운영. 운영수수료·계약기간·계약서는 미입수.",
        ),
        # Historical KT design/build/operate mandate (2021) — mark historical
        edge(
            "pf_kt_casequare_hist", "kt", "casequare_pfv",
            "EPC_OR_OPS_MANDATE", "KT → 케이스퀘어 설계·구축·운영 위탁(2021 발표, 이후 운영 주체 변경)",
            channel="supply_chain", status="VERIFIED", evidence_level=2,
            relationship_status="historical",
            project_id="casequare_gasan", project_name="케이스퀘어 가산 데이터센터",
            stress_direction="역사적 위탁 — 현재 운영은 LG유플러스. 현재 신용 전이 경로로 자동 사용하지 않음",
            exposure_kind="historical_mandate",
            source_url="https://zdnet.co.kr/view/?no=20210623141835",
            source_title="KT, 코람코 데이터센터 구축 사업 수주 (2021)",
            source_date="2021-06-23",
            roles=["historical_operator", "historical_builder"],
            verification_gap="과거 운영·관여(historical). 현재 계약 잔존 여부는 추가 공시 필요.",
        ),
        # Yeongdeungpo EdgeCore — Hanwha liquidity support
        edge(
            "pf_hanwha_edgecore_support", "hanwha_corp", "edgecore_pfv",
            "CREDIT_ENHANCEMENT", "한화 → 엣지코어PFV 자금보충·채무인수(유동화 구조)",
            channel="financial",
            amount_note="기초 대출 원금 약 410억 원 구조(신용평가). 한화 자금보충·미이행 시 채무인수",
            project_id="yeongdeungpo_yedc", project_name="영등포 Y-eDC 데이터센터",
            stress_direction="차주 미상환·유동화 차환 실패 → 한화 자금보충·채무인수 의무",
            obligation_trigger="자금보충확약상 청구·미이행 시 채무인수",
            exposure_kind="contingent_liquidity_and_debt_assumption",
            source_url="https://core.asiae.co.kr/article/2024110607330592990",
            source_title="한화 영등포 데이터센터 · 엣지코어PFV 자금 (아시아경제)",
            source_date="2024-11-06",
            evidence_level=2, status="VERIFIED",
            roles=["credit_support", "prospective_contractor"],
            verification_gap="한화 계열 신용지원·시행 관여 보도. 보증 한도·채무인수 조건은 DART 미완전 대조.",
        ),
        edge(
            "pf_hana_sec_edgecore", "hana_sec", "edgecore_pfv",
            "ARRANGER", "하나증권 → 엣지코어PFV 관련 유동화·주관(보도)",
            channel="financial",
            amount_note="주관·유동화 역할. 보유 신용익스포저는 공시 확인 전 미확정",
            project_id="yeongdeungpo_yedc", project_name="영등포 Y-eDC 데이터센터",
            stress_direction="인수·유동화 약정 조건에 따른 유동성 부담 가능(미확정)",
            exposure_kind="arranger_underwrite",
            source_url="https://core.asiae.co.kr/article/2024110607330592990",
            source_title="아시아경제",
            source_date="2024-11",
            evidence_level=2, status="VERIFIED",
            roles=["arranger"],
            verification_gap="하나증권 주선·참여 보도. 인수·잔여 익스포저는 DART 미대조.",
        ),
        # Hanwha Solutions — REC DC
        edge(
            "pf_hanwha_sol_rec", "hanwha_solutions", "rec_datacenter",
            "EQUITY_SPONSOR", "한화솔루션 → 알이씨데이터센터 지분·담보제공",
            channel="equity",
            amount_note="PF 약 1,500억 관련 지분 근질권(보도). 담보한도 약 1,800억(120%)",
            project_id="anseong_rec_dc", project_name="안성 알이씨 데이터센터",
            stress_direction="PF 부실 시 근질권 실행·지분 가치 손상",
            obligation_trigger="담보권 실행 조건(대출약정)",
            exposure_kind="equity_pledge",
            source_url="https://www.e-focus.co.kr/news/articleView.html?idxno=3002445",
            source_title="한화솔루션 알이씨데이터센터 PF 담보 (이포커스)",
            source_date="2024",
            evidence_level=2, status="VERIFIED",
            roles=["sponsor"],
            verification_gap="한화솔루션–REC 지분/담보 보도. 출자액·보증은 DART 미대조.",
        ),
        # Kakao Enterprise already tenant of camsquare — ensure project metadata
    ]

    # Dedup add evidence edges
    existing_pairs = {(e["source"], e["target"], e.get("relationship_type")) for e in new_edges}
    for e in evidence_edges:
        key = (e["source"], e["target"], e["relationship_type"])
        if key in existing_pairs:
            continue
        if e["source"] not in by or e["target"] not in by:
            report["evidence_gaps"].append(f"skip edge {e['id']} missing nodes")
            continue
        new_edges.append(e)
        report["added_edges"].append(e["id"])
        existing_pairs.add(key)
        # mark connection status
        by[e["source"]]["connection_status"] = "관계 확인"
        by[e["target"]]["connection_status"] = "관계 확인"

    # Annotate existing kakao_enterprise → camsquare edge if present
    for e in new_edges:
        if {e["source"], e["target"]} == {"kakao_enterprise", "camsquare_pfv"} or (
            e["source"] == "kakao_enterprise" and "camsquare" in e["target"]
        ):
            e["project_id"] = e.get("project_id") or "camsquare_ansan"
            e["project_name"] = e.get("project_name") or "캄스퀘어 안산 데이터센터"
            e.setdefault("stress_direction", "임차인 사업 악화 → 임대료 회수 위험(임차 계약 조건에 따름)")
            e.setdefault("exposure_kind", "lease_revenue_counterparty")

    # ---- 6. Projects metadata: keep all projects; mark graph_node=false for facilities ----
    for p in proj["projects"]:
        if p["id"] in remove_ids or p.get("construction_stage") in (
            "pre_construction", "under_construction", "completed_permit", "stabilized_operating", "planned", "expanding"
        ):
            p["graph_node"] = False
            p["map_policy"] = "company_only — 사업장/허가는 메타데이터"
        if p["id"] == "camsquare_yongin" or p.get("name_ko") == "용인 지곡":
            pass
    # Add yongin / yeongdeungpo / anseong project records if missing
    existing_pids = {p["id"] for p in proj["projects"]}
    extra_projects = [
        {
            "id": "camsquare_yongin",
            "name": "용인 지곡 하이퍼스케일 데이터센터",
            "name_ko": "용인 지곡 하이퍼스케일 데이터센터",
            "location": "경기도 용인 지곡동",
            "country": "KR", "region": "KR",
            "developer": "korea_alt_am",
            "spv": "camsquare_yongin_pfv",
            "construction_stage": "pre_construction",
            "financing_disclosed": True,
            "graph_node": False,
            "senior_debt_usd_m": None,
            "other_financing_note": "브릿지론 총 600억(선순위 530억 한화투자증권 주관·대주, 후순위 70억 SK증권) — 보도 기준",
            "korean_counterparties": ["hanwha_inv_sec", "sk_sec", "korea_alt_am", "camsquare_yongin_pfv"],
            "sources": [{
                "title": "딜사이트 용인 브릿지론",
                "url": "https://dealsite.co.kr/articles/157007",
                "date": "2025",
            }],
            "verification_date": TODAY,
            "missing": ["DART 원문 접수번호 미기입", "약정 만기 확정일"],
            "source_ids": ["S_DEALSITE_YONGIN"],
        },
        {
            "id": "yeongdeungpo_yedc",
            "name": "영등포 Y-eDC 데이터센터",
            "name_ko": "영등포 Y-eDC 데이터센터",
            "location": "서울 영등포",
            "country": "KR", "region": "KR",
            "developer": "hanwha_corp",
            "spv": "edgecore_pfv",
            "construction_stage": "pre_construction",
            "financing_disclosed": True,
            "graph_node": False,
            "other_financing_note": "유동화 기초 대출 약 410억 + 한화 자금보충(신용평가·보도)",
            "korean_counterparties": ["hanwha_corp", "edgecore_pfv", "hana_sec"],
            "sources": [{
                "title": "아시아경제 · KIS 구조화 평가",
                "url": "https://core.asiae.co.kr/article/2024110607330592990",
                "date": "2024-11",
            }],
            "verification_date": TODAY,
            "missing": ["본PF 대주단 미확정", "착공 여부"],
            "source_ids": ["S_ASIAC_EDGECORE"],
        },
        {
            "id": "anseong_rec_dc",
            "name": "안성 알이씨 데이터센터",
            "name_ko": "안성 알이씨 데이터센터",
            "location": "경기 안성",
            "country": "KR", "region": "KR",
            "developer": "hanwha_solutions",
            "spv": "rec_datacenter",
            "construction_stage": "under_construction",
            "financing_disclosed": True,
            "graph_node": False,
            "other_financing_note": "PF 약 1,500억 · 한화솔루션 지분 담보(보도)",
            "korean_counterparties": ["hanwha_solutions", "rec_datacenter"],
            "sources": [{
                "title": "이포커스 한화솔루션 담보",
                "url": "https://www.e-focus.co.kr/news/articleView.html?idxno=3002445",
                "date": "2024",
            }],
            "verification_date": TODAY,
            "missing": ["대주단 구성 DART 원문", "공사도급 상대방"],
            "source_ids": ["S_EFOCUS_REC"],
        },
    ]
    for p in extra_projects:
        if p["id"] not in existing_pids:
            proj["projects"].append(p)

    # Tag hostway project as facility metadata only
    for p in proj["projects"]:
        if p["id"] == "bundang_hostway_idc":
            p["graph_node"] = False
            p["note"] = (p.get("note") or "") + " 회사 전용 맵: 시설 노드는 제거. 임차인·운영사 등 회사만 표시."

    net["nodes"] = kept
    net["edges"] = new_edges
    net["meta"] = net.get("meta") or {}
    net["meta"]["company_only"] = True
    net["meta"]["company_only_note"] = "맵 노드는 식별 가능한 회사(및 법인 SPC)만. 사업장·허가지·집계 노드는 제외."
    net["meta"]["as_of"] = TODAY

    (PF / "network.json").write_text(json.dumps(net, ensure_ascii=False, indent=2), encoding="utf-8")
    (PF / "projects.json").write_text(json.dumps(proj, ensure_ascii=False, indent=2), encoding="utf-8")
    (PF / "_company_only_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "nodes": len(kept),
        "edges": len(new_edges),
        "removed": len(report["removed_nodes"]),
        "added_companies": len(report["added_companies"]),
        "added_edges": len(report["added_edges"]),
        "isolated_new": report["isolated_new"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
