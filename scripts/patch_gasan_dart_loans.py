#!/usr/bin/env python3
"""Promote gasan_dc_jv + gasan_landmark verified 당기말 rows to dart_loan_* edges.

Notes already extracted previously; amounts match v6 ACTIVE edges but lacked dart_loan IDs.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend/public/data/pf/network.json"


def eok_cheon(cheon: int) -> float:
    return round(cheon / 100_000, 4)


def mk(eid, src, name, target, cheon, rcept, title, note, rate, maturity, limit_cheon=None):
    krw = eok_cheon(cheon)
    return {
        "id": eid,
        "source": src,
        "target": target,
        "relationship_type": "PROJECT_LOAN",
        "roles": ["lender"],
        "source_ids": [f"dart_audit_{target}_{rcept}"],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_krw_eok": krw,
        "amount_type": "outstanding_principal",
        "amount_unit": "억원",
        "amount_note": note,
        "amount_as_of": "2025-12-31",
        "impact_channel": "financial",
        "source_status": "VERIFIED",
        "label": f"{name} → {target} · {krw:g}억",
        "impact_label": f"{name} 당기말 {krw:g}억",
        "explanation": note,
        "transmission_class": "direct",
        "exposure_status": "ACTIVE_CONFIRMED",
        "relationship_status": "current",
        "shock_eligible": True,
        "layer": "fact",
        "evidence_kind": "dart_audit_note",
        "evidence_status": "DART 감사보고서 차입금 주석 당기말",
        "evidence_level": "company_filing",
        "participation_path": "직접 대출",
        "participation_directness": "direct",
        "contingent_obligation": False,
        "source_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}",
        "source_title": title,
        "source_date": f"{rcept[:4]}-{rcept[4:6]}-{rcept[6:8]}",
        "dart_receipt_number": rcept,
        "verification_date": "2026-10-22",
        "maturity": maturity,
        "interest_rate": rate,
        "financing_stage": "main_pf",
        "facility_limit_krw_eok": eok_cheon(limit_cheon) if limit_cheon else krw,
        "stress_direction": "차주 부실 → 대주 신용 익스포저",
        "exposure_kind": "loan_principal_outstanding",
        "period_basis": "current_period_당기말",
    }


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    edges = net["edges"]
    by_id = {e["id"]: i for i, e in enumerate(edges)}
    added = []

    # --- gasan_dc_jv 20260406000434 주석14 단위:천원 당기말 ---
    # Prior ING/SG/OCBC/IBK-trustee/NATIXIS 당기말 '-' already FULLY_REPAID on v6_gj_old_*
    GJ = "20260406000434"
    GJ_T = "가산디씨제이브이 감사보고서 (2025.12)"
    gj_rows = [
        ("dart_loan_bnp_gasan_jv", "bnp_paribas", "BNP파리바", 50_000_000, "CD91+1.6%", "2030-11"),
        ("dart_loan_mufg_gasan_jv", "mufg", "MUFG", 50_000_000, "CD91+1.6%", "2030-11"),
        ("dart_loan_ca_cib_gasan_jv", "ca_cib", "크레디아그리콜", 65_000_000, "CD91+1.6%", "2030-11"),
        ("dart_loan_nh_inv_gasan_jv", "nh_inv_sec", "NH투자증권", 135_000_000, "CD91+1.6%", "2030-11"),
    ]
    for eid, src, name, cheon, rate, mat in gj_rows:
        e = mk(eid, src, name, "gasan_dc_jv", cheon, GJ, GJ_T,
               f"주석14 당기말 일반자금대출 {name} {cheon:,}천원", rate, mat)
        if eid in by_id:
            edges[by_id[eid]] = e
        else:
            edges.append(e)
            by_id[eid] = len(edges) - 1
            added.append(eid)
    for e in edges:
        if e.get("target") == "gasan_dc_jv" and str(e.get("id", "")).startswith("v6_gj_loan_"):
            e["exposure_status"] = "SUPERSEDED_BY_DART_AUDIT"
            e["shock_eligible"] = False
            e["verification_gap"] = "dart_loan_*_gasan_jv supersedes"

    # --- gasan_landmark 20260406003009 주석5 단위:천원 당기말 ---
    GL = "20260406003009"
    GL_T = "가산랜드마크데이터센터피에프브이 감사보고서 (2025.12)"
    gl_rows = [
        ("dart_loan_kdb_gasan_landmark", "kdb", "한국산업은행", 100_000_000, "3.68%"),
        ("dart_loan_im_bank_gasan_landmark", "im_bank", "아이엠뱅크", 30_000_000, "3.85%"),
        ("dart_loan_kb_gasan_landmark", "kb_bank", "국민은행", 20_000_000, "3.95%"),
        ("dart_loan_bnk_kyongnam_gasan_landmark", "bnk_kyongnam", "경남은행", 20_000_000, "3.85%"),
        ("dart_loan_hana_gasan_landmark", "hana_bank", "하나은행", 20_000_000, "3.95%"),
        ("dart_loan_suhyup_gasan_landmark", "suhyup_bank", "SH수협은행", 10_000_000, "3.95%"),
    ]
    for eid, src, name, cheon, rate in gl_rows:
        e = mk(eid, src, name, "gasan_landmark_pfv", cheon, GL, GL_T,
               f"주석5 당기말 장기차입금 {name} {cheon:,}천원", rate, None)
        if eid in by_id:
            edges[by_id[eid]] = e
        else:
            edges.append(e)
            by_id[eid] = len(edges) - 1
            added.append(eid)
    for e in edges:
        if e.get("target") == "gasan_landmark_pfv" and str(e.get("id", "")).startswith("v6_glm_refi_"):
            e["exposure_status"] = "SUPERSEDED_BY_DART_AUDIT"
            e["shock_eligible"] = False
            e["verification_gap"] = "dart_loan_*_gasan_landmark supersedes"

    # sources
    for target, rcept, title in [
        ("gasan_dc_jv", GJ, GJ_T),
        ("gasan_landmark_pfv", GL, GL_T),
    ]:
        sid = f"dart_audit_{target}_{rcept}"
        if not any(s.get("id") == sid for s in net.get("sources") or []):
            net.setdefault("sources", []).append({
                "id": sid, "title": title, "publisher": "DART",
                "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}",
                "kind": "filing", "dart_receipt_number": rcept,
                "used_for": "차입금 주석 당기말",
            })

    net["edges"] = edges
    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("added", added)


if __name__ == "__main__":
    main()
