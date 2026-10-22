#!/usr/bin/env python3
"""
Fix Hostway concentration, normalize Korean Hangul display names,
and expand KR DC projects from dc.namepf.com permit data (physical projects only —
no fabricated financing edges).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PF = ROOT / "frontend" / "public" / "data" / "pf"


def slug(s: str) -> str:
    s = re.sub(r"[^0-9A-Za-z가-힣]+", "_", s).strip("_")
    return s[:48] or "x"


def main() -> None:
    net = json.loads((PF / "network.json").read_text(encoding="utf-8"))
    proj = json.loads((PF / "projects.json").read_text(encoding="utf-8"))
    dash = json.loads((PF / "dc_namepf_dash.json").read_text(encoding="utf-8"))
    rows = dash["permits"]["rows"]

    by_id = {n["id"]: n for n in net["nodes"]}

    # ---- 1. Ensure Hangul display: name_ko primary for KR; keep English in name ----
    # Already have name_ko from expand script; swap so `name` is Hangul for KR UI that still reads .name,
    # and store English in name_en.
    swapped = 0
    for n in net["nodes"]:
        if n.get("region") != "KR" and n.get("country") != "KR":
            continue
        ko = (n.get("name_ko") or "").strip()
        en = n.get("name") or ""
        if ko and not re.search(r"[가-힣]", en):
            n["name_en"] = en
            n["name"] = ko  # primary display field becomes Hangul
            swapped += 1
        elif ko and re.search(r"[가-힣]", en):
            n["name_en"] = n.get("name_en") or ""
        elif not ko and re.search(r"[가-힣]", en):
            n["name_ko"] = en

    # ---- 2. Reclassify Bundang Hostway: stabilized operating colocation asset, NOT development PF ----
    if "bundang_hostway_idc" in by_id:
        b = by_id["bundang_hostway_idc"]
        b["name"] = "분당 호스트웨이 IDC"
        b["name_ko"] = "분당 호스트웨이 IDC"
        b["name_en"] = "Bundang Hostway IDC"
        b["entity_type"] = "operating_asset"
        b["role"] = "Stabilized colocation DC (not a new development PF)"
        b["description"] = (
            "Stabilized operating colocation facility in Bundang (~12.5 MW). "
            "Hostway long-term lease to 2034. Ownership via REIT/AM transactions. "
            "NOT a speculative under-construction PF project. "
            "Do not use as default Korean PF contagion hub."
        )
        b["pf_exposure_class"] = "confirmed_dc_finance"
        b["pf_exposure_class_num"] = 2
        b["key_drivers"] = ["stabilized_operating", "confirmed_dc_finance"]

    # Soften Hostway project dossier
    for p in proj["projects"]:
        if p["id"] == "bundang_hostway_idc":
            p["name"] = "분당 호스트웨이 IDC"
            p["name_ko"] = "분당 호스트웨이 IDC"
            p["construction_stage"] = "stabilized_operating"
            p["hyperscaler_capex_exposure"] = "none_operating_asset"
            p["gpu_rent_exposure"] = "none_direct"
            p["shock_role"] = "operating_colocation_not_pf_hub"
            p["note"] = (
                "Operating asset with long-term Hostway lease. "
                "Excluded from default CW/CAPEX development-PF contagion unless user selects this asset."
            )

    # Remove any ASSUMED edges that incorrectly funnel institutions into Hostway (none currently,
    # but strip korean_counterparties that are not on Hostway edges)
    for p in proj["projects"]:
        if p["id"] != "bundang_hostway_idc":
            # Ensure other projects don't list Hostway as counterparty unless true
            cps = p.get("korean_counterparties") or []
            if "bundang_hostway_idc" in cps:
                p["korean_counterparties"] = [c for c in cps if c != "bundang_hostway_idc"]

    # ---- 3. Korean Hangul names for key projects already present ----
    rename_proj = {
        "casequare_gasan": ("케이스퀘어 가산 데이터센터", "Casequare Gasan Data Center"),
        "casequare_pfv": ("케이스퀘어데이터센터PFV", "Casequare Data Center PFV"),
        "camsquare_ansan": ("캄스퀘어 안산 데이터센터", "Camsquare Ansan Data Center"),
        "camsquare_pfv": ("캄스퀘어안산데이터센터PFV", "Camsquare Ansan Data Center PFV"),
        "sds_gumi_aidc": ("삼성SDS 구미 AI 데이터센터", "Samsung SDS Gumi AI Data Center"),
        "skt_ulsan_aidc": ("SK텔레콤 울산 AIDC", "SK Telecom Ulsan AIDC"),
        "kr_pf_market": ("한국 데이터센터 PF 시장(집계)", "Korean DC PF Market (aggregate)"),
    }
    for pid, (ko, en) in rename_proj.items():
        if pid in by_id:
            by_id[pid]["name"] = ko
            by_id[pid]["name_ko"] = ko
            by_id[pid]["name_en"] = en
        for p in proj["projects"]:
            if p["id"] == pid:
                p["name"] = ko
                p["name_ko"] = ko

    # ---- 4. Expand projects from dc.namepf permits (physical universe) ----
    # Network nodes: only permits with disclosed MW OR (under construction + area>=25k) OR has news
    # All permits go into projects.json catalog with verification from namepf + seumteo basis
    existing_p = {p["id"] for p in proj["projects"]}
    existing_n = set(by_id)

    # Dedup heuristics vs known projects
    def is_dup(r: dict) -> str | None:
        nm = r.get("nm") or ""
        addr = r.get("addr") or ""
        if "가산" in addr and ("케이스" in nm or "LF" in nm.upper() or "코람코" in nm):
            return "casequare_gasan"
        if "안산" in addr and ("캄스" in nm or "성곡" in addr):
            return "camsquare_ansan"
        if "구미" in addr and "삼성" in nm:
            return "sds_gumi_aidc"
        if "분당" in addr and ("호스트" in nm or "야탑" in addr):
            return "bundang_hostway_idc"
        if "울산" in addr and ("SK" in nm or "에스케이" in nm):
            return "skt_ulsan_aidc"
        return None

    stage_map = {
        "착공 전": "pre_construction",
        "공사 중": "under_construction",
        "준공": "completed_permit",
    }

    added_catalog = 0
    added_nodes = 0
    network_candidates = []

    for r in rows:
        dup = is_dup(r)
        pid = f"kr_permit_{r['id']}"
        ko_name = r.get("nm") or f"{r.get('sd','')} {r.get('dong','')} 데이터센터"
        stage_ko = r.get("stage") or ""
        stage = stage_map.get(stage_ko, "unknown")
        cap = r.get("cap") or {}
        has_mw = isinstance(cap.get("mw"), (int, float)) and not cap.get("none")
        news = r.get("news") or []
        area = r.get("area") or 0

        dossier = {
            "id": pid,
            "name": ko_name,
            "name_ko": ko_name,
            "location": r.get("addr") or f"{r.get('sd','')} {r.get('sg','')} {r.get('dong','')}",
            "country": "KR",
            "region": "KR",
            "sido": r.get("sd"),
            "sigungu": r.get("sg"),
            "developer": None,
            "owner": None,
            "spv": None,
            "tenant": None,
            "construction_stage": stage,
            "stage_ko": stage_ko,
            "permit_date": r.get("pms"),
            "construction_start": r.get("stc"),
            "completion_date": r.get("apr"),
            "gfa_m2": r.get("area"),
            "dc_floor_area_m2": r.get("dcArea"),
            "critical_it_load_mw": cap.get("it"),
            "power_mw": cap.get("mw") if has_mw else None,
            "power_basis": cap.get("basis"),
            "power_note": cap.get("note") or cap.get("txt"),
            "capacity_note": cap.get("note"),
            "hyperscaler_capex_exposure": "future_permit_pipeline" if stage in ("pre_construction", "under_construction") else "none_operating_or_complete",
            "gpu_rent_exposure": "none_direct",
            "shock_role": "permit_pipeline_not_pf" if not has_mw else "permit_with_disclosed_mw",
            "baseline_dscr": None,
            "dscr_status": "UNKNOWN",
            "senior_debt_usd_m": None,
            "financing_disclosed": False,
            "korean_counterparties": [],
            "source_ids": ["S_DC_NAMEPF"],
            "source_urls": [n.get("u") for n in news[:3] if n.get("u")] + [s.get("u") for s in (cap.get("src") or [])[:2]],
            "verification_date": cap.get("checked") or dash.get("built") or "2026-10-21",
            "verification_status": "permit_record",
            "duplicate_of": dup,
            "missing": ["PF lenders", "SPV", "EPC award", "DSCR", "debt terms"] if not dup else ["merged_into_" + dup],
            "namepf_permit_id": r["id"],
            "kind": r.get("kind"),
        }

        if pid not in existing_p and dup is None:
            proj["projects"].append(dossier)
            existing_p.add(pid)
            added_catalog += 1
        elif dup and dup in existing_p:
            # annotate existing
            for p in proj["projects"]:
                if p["id"] == dup:
                    p.setdefault("namepf_related_permits", []).append(r["id"])
                    if has_mw and not p.get("power_mw"):
                        p["power_mw"] = cap.get("mw")
                        p["power_note"] = cap.get("note")

        # Network node criteria
        promote = (
            dup is None
            and (
                has_mw
                or (stage == "under_construction" and area >= 25000)
                or (len(news) >= 1 and area >= 15000)
            )
        )
        if promote:
            network_candidates.append((pid, dossier, r, has_mw, area))

    # Cap network nodes to keep graph readable: top by area among candidates + all with MW
    network_candidates.sort(key=lambda x: (1 if x[3] else 0, x[4]), reverse=True)
    selected = network_candidates[:35]  # plus existing projects

    for pid, dossier, r, has_mw, area in selected:
        if pid in existing_n:
            continue
        node = {
            "id": pid,
            "name": dossier["name"],
            "name_ko": dossier["name_ko"],
            "name_en": dossier["name"],
            "group": "project_finance",
            "sector": "Korean Data Center Permit / Development",
            "entity_type": "project",
            "role": f"건축인허가 · {dossier.get('stage_ko')}",
            "description": (
                f"국토부 건축인허가(dc.namepf.com 집계) 기반 물리 사업장. "
                f"연면적 {area}㎡ · 단계 {dossier.get('stage_ko')}. "
                f"인허가 ≠ 금융약정. PF 대주·신탁·시공 관계는 별도 공시로만 연결합니다."
            ),
            "listed": False,
            "ticker": None,
            "exchange": None,
            "quote_currency": None,
            "listing_note": None,
            "display_size": 1.15 if has_mw else 0.95,
            "source_status": "VERIFIED",
            "source_ids": ["S_DC_NAMEPF"],
            "key_drivers": ["permit_pipeline"],
            "region": "KR",
            "country": "KR",
            "pf_exposure_class": "research_candidate",
            "pf_exposure_class_num": 5,
            "is_demo": False,
            "sido": r.get("sd"),
            "construction_stage": dossier["construction_stage"],
        }
        net["nodes"].append(node)
        existing_n.add(pid)
        added_nodes += 1

    # Source for namepf
    if not any(s["id"] == "S_DC_NAMEPF" for s in net["sources"]):
        net["sources"].append({
            "id": "S_DC_NAMEPF",
            "title": "데이터센터 개발 현황 대시보드 (건축인허가 집계)",
            "publisher": "dc.namepf.com / 국토부 건축인허가 대장",
            "date": str(dash.get("built") or "2026-10"),
            "url": "https://dc.namepf.com/",
            "used_for": "Korean DC physical project universe from building permits; MW only when press-confirmed",
            "kind": "dashboard",
        })

    # ---- 5. Do NOT add edges from general banks → Hostway or permit projects ----
    # Keep Hostway edges only to its verified AM/tenant counterparties (already present).

    # Soften kr_pf_market hub: remove edge to Hostway if any; keep Casequare/Camsquare/Gumi only
    net["edges"] = [
        e for e in net["edges"]
        if not (
            (e.get("source") == "kr_pf_market" and e.get("target") == "bundang_hostway_idc")
            or (e.get("target") == "kr_pf_market" and e.get("source") == "bundang_hostway_idc")
        )
    ]

    # Tag Hostway edges clearly
    for e in net["edges"]:
        if "bundang" in e["id"] or e.get("source") == "bundang_hostway_idc" or e.get("target") == "bundang_hostway_idc":
            e["project_scope"] = "bundang_hostway_operating_asset_only"
            e["explanation"] = (e.get("explanation") or "") + " [Hostway 운영자산 한정 — 기본 한국 PF 허브 아님]"

    net["meta"]["as_of"] = "2026-10-21"
    net["meta"]["name"] = "CONTAGION — AI Data Center PF (US → Korea)"
    net["meta"]["disclaimer"] = (
        "한국 기관명은 Hangul 우선 표시. "
        "분당 호스트웨이 IDC는 안정화 운영 코로케이션이며 기본 위기 전파 허브가 아닙니다. "
        "dc.namepf.com 인허가 사업장은 물리 사업 우주이며 금융약정을 자동 생성하지 않습니다. "
        "검증된 PF 관계는 케이스퀘어·캄스퀘어 등 Level 1–2 공시만 실선으로 연결합니다."
    )
    net["meta"]["korean_name_display"] = "hangul_primary"
    net["meta"]["hostway_role"] = "stabilized_operating_asset_not_default_hub"
    net["meta"]["namepf_permits"] = len(rows)
    net["meta"]["namepf_projects_catalog"] = sum(1 for p in proj["projects"] if str(p["id"]).startswith("kr_permit_"))
    net["meta"]["namepf_network_nodes"] = added_nodes

    (PF / "network.json").write_text(json.dumps(net, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (PF / "projects.json").write_text(json.dumps(proj, ensure_ascii=False, indent=2), encoding="utf-8")

    kr = [n for n in net["nodes"] if n.get("region") == "KR"]
    hangul = sum(1 for n in kr if re.search(r"[가-힣]", n.get("name") or ""))
    print(f"swapped_display_names={swapped} KR_hangul_primary={hangul}/{len(kr)}")
    print(f"catalog_added={added_catalog} network_nodes_added={added_nodes} total_projects={len(proj['projects'])} total_nodes={len(net['nodes'])}")
    print(f"hostway_edges={sum(1 for e in net['edges'] if 'bundang' in e['id'])}")


if __name__ == "__main__":
    main()
