#!/usr/bin/env python3
"""Hand-verified 당기말 borrowings for remaining extractable PFVs.

Sources: DART audit ZIP note tables (current-period column only).
Never uses 전기말 as current exposure.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"
OUT = ROOT / "docs" / "verified_gap_borrowings_batch2.json"

VERIFY = "2026-10-22"


def eok(krw: int) -> float:
    return round(krw / 1e8, 4)


ROWS: list[dict] = []

# --- 그린디지털인프라 20260402001874 단위:천원 ---
# Tr.A/B 당기말 = outstanding; 국민은행 신용공여 당기말 0 (한도만)
GDI = "20260402001874"
GDI_T = "그린디지털인프라 감사보고서 (2025.12)"
for eid, src, name, krw, rate, tranche in [
    ("dart_loan_kb_gdi_tra", "kb_bank", "국민은행", 80_000_000_000, "4.95%", "Tr.A"),
    ("dart_loan_kyobo_gdi_tra", "kyobo_life", "교보생명보험", 150_000_000_000, "4.95%", "Tr.A"),
    ("dart_loan_shinhan_gdi_tra", "shinhan_bank", "신한은행", 100_000_000_000, "4.95%", "Tr.A"),
    ("dart_loan_hyundai_marine_gdi_tra", "hyundai_marine", "현대해상화재보험", 30_000_000_000, "4.95%", "Tr.A"),
    ("dart_loan_kb_ins_gdi_tra", "kb_ins", "KB손해보험", 40_000_000_000, "4.95%", "Tr.A"),
    ("dart_loan_kb_gdi_trb", "kb_bank", "국민은행", 20_000_000_000, "3.75%", "Tr.B"),
    ("dart_loan_kyobo_gdi_trb", "kyobo_life", "교보생명보험", 50_000_000_000, "3.75%", "Tr.B"),
    ("dart_loan_hyundai_marine_gdi_trb", "hyundai_marine", "현대해상화재보험", 15_000_000_000, "3.75%", "Tr.B"),
    ("dart_loan_kb_ins_gdi_trb", "kb_ins", "KB손해보험", 10_000_000_000, "3.75%", "Tr.B"),
    ("dart_loan_mkif_gdi_sub", "mkif", "맥쿼리한국인프라투융자회사", 400_000_000_000, "8.5%", "후순위"),
]:
    ROWS.append({
        "id": eid, "source": src, "target": "green_digital_infra", "name": name,
        "krw": krw, "rate": rate, "maturity": None, "tranche": tranche,
        "rcept": GDI, "as_of": "2025-12-31", "title": GDI_T,
        "note": f"주석7 당기말 {tranche} {name} {eok(krw):g}억(천원표)",
    })
# undrawn facility context only (outstanding 0)
ROWS.append({
    "id": "dart_facility_kb_gdi_credit_line", "source": "kb_bank", "target": "green_digital_infra",
    "name": "국민은행", "krw": 0, "limit_krw": 20_000_000_000, "rate": None, "maturity": None,
    "rcept": GDI, "as_of": "2025-12-31", "title": GDI_T,
    "note": "주석7 당기말 신용공여대출 국민은행 약정 200억 / 당기말 잔액 0 — 한도만",
    "facility_context": True, "zero_outstanding": True,
})

# --- 신영문봉 20260401001427 단위:천원 당기말 only ---
SM = "20260401001427"
SM_T = "신영문봉피에프브이 감사보고서 (2025.12)"
for eid, src, name, krw in [
    ("dart_loan_bdh1_shinyoung", "bdh_1st_spc", "비디에이치제일차", 20_000_000_000),
    ("dart_loan_kis_savings_shinyoung", "kis_savings", "한국투자저축은행", 12_000_000_000),
    ("dart_loan_louis_alpha1_shinyoung", "louis_alpha_1st_spc", "루이스알파제일차", 6_000_000_000),
    ("dart_loan_goryo_savings_shinyoung", "goryo_savings", "고려저축은행", 9_000_000_000),
    ("dart_loan_seram_savings_shinyoung", "seram_savings", "세람저축은행", 2_000_000_000),
    ("dart_loan_db_capital_shinyoung", "db_capital", "디비캐피탈", 5_000_000_000),
    ("dart_loan_welcome_savings_shinyoung", "welcome_savings", "웰컴저축은행", 3_000_000_000),
    ("dart_loan_kiwoom_fni_shinyoung", "kiwoom_fni", "키움에프앤아이", 4_000_000_000),
    ("dart_loan_daol_savings_shinyoung", "daol_savings", "다올저축은행", 1_000_000_000),
    ("dart_loan_acuon_savings_shinyoung", "acuon_savings", "애큐온저축은행", 4_000_000_000),
    ("dart_loan_eco_capital_shinyoung", "eco_capital", "에코캐피탈", 1_000_000_000),
    ("dart_loan_nh_inv_shinyoung", "nh_inv_sec", "엔에이치투자증권", 20_000_000_000),
]:
    ROWS.append({
        "id": eid, "source": src, "target": "shinyoung_munbong_pfv", "name": name,
        "krw": krw, "rate": "6.00%" if src != "nh_inv_sec" else "20.00%", "maturity": "2026-04-29",
        "rcept": SM, "as_of": "2025-12-31", "title": SM_T,
        "note": f"주석7 당기말 개발사업브릿지론 {name} {eok(krw):g}억",
        "financing_stage": "bridge",
    })

# --- 에포크 20260331002059 단위:원 ---
EP = "20260331002059"
EP_T = "에포크피에프브이 감사보고서 (2025.12)"
for eid, src, name, krw, tranche in [
    ("dart_loan_ibk_epoch_a", "ibk_bank", "중소기업은행", 120_000_000_000, "대출금A"),
    ("dart_loan_kdb_epoch_a", "kdb", "산업은행", 42_500_000_000, "대출금A"),
    ("dart_loan_kb_epoch_a", "kb_bank", "국민은행", 30_000_000_000, "대출금A"),
    ("dart_loan_woori_epoch_a", "woori_bank", "우리은행", 42_500_000_000, "대출금A"),
    ("dart_loan_hana_epoch_a", "hana_bank", "하나은행", 42_500_000_000, "대출금A"),
    ("dart_loan_nh_epoch_a", "nh_bank", "농협은행", 42_500_000_000, "대출금A"),
    ("dart_loan_ibk_epoch_b1", "ibk_bank", "중소기업은행", 26_500_000_000, "대출금B-1"),
]:
    ROWS.append({
        "id": eid, "source": src, "target": "epoch_pfv", "name": name,
        "krw": krw, "rate": "4.8%", "maturity": None, "tranche": tranche,
        "rcept": EP, "as_of": "2025-12-31", "title": EP_T,
        "note": f"주석11 당기말 {tranche} {name} {eok(krw):g}억",
    })

# --- 케이스퀘어에코송파 20260406000992 단위:천원 당기말 ---
CES = "20260406000992"
CES_T = "케이스퀘어에코송파피에프브이 감사보고서 (2025.12)"
for eid, src, name, krw, rate, mat, stage in [
    ("dart_loan_astom1_eco_songpa", "astom_1st_spc", "아스톰제일차", 42_000_000_000, "5.00%", "2026-06-17", "bridge"),
    ("dart_loan_suhyup_eco_songpa", "suhyup_bank", "수협은행", 50_000_000_000, "7.00%", "2026-06-18", "main_pf"),
    ("dart_loan_kis_eco_songpa", "korea_inv_sec", "한국투자증권", 10_000_000_000, "7.00%", "2026-06-18", "main_pf"),
    ("dart_loan_nh_life_eco_songpa", "nh_life", "농협생명보험", 30_000_000_000, "7.50%", "2026-06-18", "main_pf"),
    ("dart_loan_shinhan_capital_eco_songpa", "shinhan_capital", "신한캐피탈", 5_000_000_000, "7.50%", "2026-06-18", "main_pf"),
    ("dart_loan_frenchshine1_eco_songpa", "frenchshine_1st_spc", "프렌치샤인제일차", 10_000_000_000, "7.50%", "2026-06-18", "main_pf"),
    ("dart_loan_ki_capital_eco_songpa", "korea_inv_capital", "한국투자캐피탈", 20_000_000_000, "7.00%", "2026-06-18", "main_pf"),
    ("dart_loan_kb_sec_eco_songpa", "kb_sec", "케이비증권", 15_000_000_000, "7.00%", "2026-06-18", "main_pf"),
    ("dart_loan_sedna1_eco_songpa", "sedna_1st_spc", "세드나제일차", 31_000_000_000, "5.00%", "2026-06-18", "main_pf"),
    ("dart_loan_dayna1_eco_songpa", "dayna_1st_spc", "데이나제일차", 53_000_000_000, "5.00%", "2026-06-18", "main_pf"),
    ("dart_loan_themis1_eco_songpa", "themis_1st_spc", "테미스제일차", 10_000_000_000, "7.00%", "2026-06-18", "main_pf"),
]:
    ROWS.append({
        "id": eid, "source": src, "target": "casequare_eco_songpa_pfv", "name": name,
        "krw": krw, "rate": rate, "maturity": mat,
        "rcept": CES, "as_of": "2025-12-31", "title": CES_T,
        "note": f"주석7 당기말 {name} {eok(krw):g}억",
        "financing_stage": stage,
    })

# --- 케이스퀘어용산 20260409002420 단위:원 당기말 ---
CY = "20260409002420"
CY_T = "케이스퀘어용산피에프브이 감사보고서 (2025.12)"
ROWS.append({
    "id": "dart_loan_bnk_sum23_yongsan", "source": "bnk_sum_23rd_spc", "target": "casequare_yongsan_pfv",
    "name": "비앤케이썸이십삼차", "krw": 190_000_000_000, "rate": "2.85%", "maturity": "2026-02-09",
    "rcept": CY, "as_of": "2025-12-31", "title": CY_T,
    "note": "주석8 당기말 단기차입금 비앤케이썸이십삼차 1,900억",
    "financing_stage": "bridge",
})
for eid, src, name, krw in [
    ("dart_loan_welcome_yongsan", "welcome_savings", "웰컴저축은행", 12_000_000_000),
    ("dart_loan_incheon_sav_yongsan", "incheon_savings", "인천저축은행", 5_000_000_000),
    ("dart_loan_samjung_sav_yongsan", "samjung_savings", "삼정저축은행", 7_000_000_000),
    ("dart_loan_osb_yongsan", "osb_savings", "OSB저축은행", 10_000_000_000),
    ("dart_loan_minguk_sav_yongsan", "minguk_savings", "민국저축은행", 2_000_000_000),
    ("dart_loan_geumhwa_sav_yongsan", "geumhwa_savings", "금화저축은행", 4_000_000_000),
    ("dart_loan_namyang_sav_yongsan", "namyang_savings", "남양저축은행", 5_000_000_000),
    ("dart_loan_imoa_yongsan", "imoa_savings", "모아저축은행", 10_000_000_000),
    ("dart_loan_inseong_sav_yongsan", "inseong_savings", "인성저축은행", 5_000_000_000),
    ("dart_loan_thek_yongsan", "thek_savings", "더케이저축은행", 5_000_000_000),
    ("dart_loan_sky_sav_yongsan", "sky_savings", "스카이저축은행", 3_000_000_000),
    ("dart_loan_anyang_sav_yongsan", "anyang_savings", "안양저축은행", 5_000_000_000),
    ("dart_loan_union_sav_yongsan", "union_savings", "유니온저축은행", 5_000_000_000),
    ("dart_loan_yungchang_sav_yongsan", "yungchang_savings", "융창저축은행", 2_000_000_000),
    ("dart_loan_jt_yongsan", "jt_savings", "JT저축은행", 7_000_000_000),
    ("dart_loan_seram_yongsan", "seram_savings", "세람저축은행", 3_000_000_000),
    ("dart_loan_db_sav_yongsan", "db_savings", "DB저축은행", 10_000_000_000),
    ("dart_loan_sangsangin_yongsan", "sangsangin_savings", "상상인저축은행", 5_000_000_000),
    ("dart_loan_ok_yongsan", "ok_savings", "OK저축은행", 11_000_000_000),
    ("dart_loan_woori_sav_yongsan", "woori_savings", "우리저축은행", 2_000_000_000),
    ("dart_loan_hanwha_sav_yongsan", "hanwha_savings", "한화저축은행", 3_500_000_000),
    ("dart_loan_kiwoom_sav_yongsan", "kiwoom_savings", "키움저축은행", 3_000_000_000),
    ("dart_loan_acuon_yongsan", "acuon_savings", "애큐온저축은행", 8_000_000_000),
    ("dart_loan_cham_sav_yongsan", "cham_savings", "참저축은행", 4_500_000_000),
    ("dart_loan_yeongjin_sav_yongsan", "yeongjin_savings", "영진저축은행", 2_500_000_000),
    ("dart_loan_jt_chinae_yongsan", "jt_chinae_savings", "JT친애저축은행", 8_000_000_000),
    ("dart_loan_nh_sav_yongsan", "nh_savings", "NH저축은행", 5_000_000_000),
    ("dart_loan_kis_sav_yongsan", "kis_savings", "한국투자저축은행", 11_000_000_000),
    ("dart_loan_burim_sav_yongsan", "burim_savings", "부림저축은행", 5_000_000_000),
    ("dart_loan_osung_yongsan", "osung_savings", "오성저축은행", 800_000_000),
    ("dart_loan_snt_sav_yongsan", "snt_savings", "SNT저축은행", 2_000_000_000),
]:
    ROWS.append({
        "id": eid, "source": src, "target": "casequare_yongsan_pfv", "name": name,
        "krw": krw, "rate": "6.20%", "maturity": "2026-03-19",
        "rcept": CY, "as_of": "2025-12-31", "title": CY_T,
        "note": f"주석8 당기말 유동성장기차입금 {name} {eok(krw):g}억",
    })

# --- 북항 누락 대주 20260408000471 단위:천원 ---
BH = "20260408000471"
BH_T = "북항아이디씨피에프브이 감사보고서 (2025.12)"
for eid, src, name, krw, rate in [
    ("dart_loan_hj_heavy_bukhang", "hj_heavy", "에이치제이중공업", 24_800_000_000, "4.6%"),
    ("dart_loan_a1_breeze_bukhang", "a1_breeze", "에이원브리즈", 12_900_000_000, "7.0%"),
    ("dart_loan_icecream_bukhang", "icecream_media", "아이스크림미디어", 5_000_000_000, "10.0%"),
    ("dart_loan_a1_living_bukhang", "a1_living", "에이원리빙", 8_000_000_000, "11.0%"),
    ("dart_loan_theym_bukhang", "the_ym_korea", "더와이엠코리아", 500_000_000, "9.0%"),
]:
    ROWS.append({
        "id": eid, "source": src, "target": "bukhang_idc_pfv", "name": name,
        "krw": krw, "rate": rate, "maturity": None,
        "rcept": BH, "as_of": "2025-12-31", "title": BH_T,
        "note": f"주석6 당기말 단기차입금 {name} {eok(krw):g}억",
        "financing_stage": "bridge",
    })

# Convert existing bukhang v6 bridge edges to dart-verified period_basis if matching
# (leave in place; new dart edges are additive — demote overlapping v6 below)


def promote(net, node_id, name=None):
    ids = {n["id"] for n in net["nodes"]}
    if node_id in ids:
        return True
    for i, n in enumerate(net.get("hidden_nodes") or []):
        if n.get("id") == node_id:
            p = deepcopy(n)
            p.pop("map_hidden", None)
            for k in ("roles", "key_drivers", "source_ids"):
                if not isinstance(p.get(k), list):
                    p[k] = []
            net["nodes"].append(p)
            net["hidden_nodes"].pop(i)
            return True
    if name:
        net["nodes"].append({
            "id": node_id,
            "name": name,
            "name_ko": name,
            "group": "financial",
            "entity_type": "lender",
            "region": "KR",
            "listed": False,
            "display_size": 1,
            "source_status": "VERIFIED",
            "roles": ["lender"],
            "key_drivers": [],
            "source_ids": [],
            "connection_status": "관계 확인",
            "is_company": True,
            "pf_exposure_class": "confirmed_dc_finance",
        })
        return True
    return False


def edge_from(row: dict) -> dict:
    fac = bool(row.get("facility_context"))
    zero = bool(row.get("zero_outstanding")) or (row.get("krw") == 0)
    krw_eok = eok(row["krw"]) if row.get("krw") is not None else None
    rcept = row["rcept"]
    src_id = f"dart_audit_{row['target']}_{rcept}"
    return {
        "id": row["id"],
        "source": row["source"],
        "target": row["target"],
        "relationship_type": "PROJECT_LOAN",
        "roles": ["facility_context"] if fac else ["lender"],
        "source_ids": [src_id],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": None,
        "amount_krw_eok": krw_eok,
        "amount_type": "facility_total_context" if fac else "outstanding_principal",
        "amount_unit": "억원",
        "amount_note": row["note"],
        "amount_as_of": row["as_of"],
        "impact_channel": "financial",
        "source_status": "VERIFIED",
        "label": f"{row['name']} → {row['target']} · {krw_eok:g}억" if not zero else f"{row['name']} → {row['target']} · 한도(잔액0)",
        "impact_label": row["note"][:80],
        "explanation": row["note"],
        "transmission_class": "direct",
        "exposure_status": "ACTIVE_CONFIRMED" if not zero else "COMMITMENT_UNDRAWN",
        "relationship_status": "current",
        "shock_eligible": (not fac) and (not zero) and (krw_eok or 0) > 0,
        "layer": "fact",
        "evidence_kind": "dart_audit_note",
        "evidence_status": "DART 감사보고서 차입금 주석 당기말",
        "evidence_level": "company_filing",
        "participation_path": "직접 대출",
        "participation_directness": "direct",
        "contingent_obligation": False,
        "source_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}",
        "source_title": row["title"],
        "source_date": f"{rcept[:4]}-{rcept[4:6]}-{rcept[6:8]}",
        "dart_receipt_number": rcept,
        "verification_date": VERIFY,
        "maturity": row.get("maturity"),
        "interest_rate": row.get("rate"),
        "financing_stage": row.get("financing_stage") or "main_pf",
        "facility_limit_krw_eok": eok(row["limit_krw"]) if row.get("limit_krw") else None,
        "tranche": row.get("tranche"),
        "stress_direction": "차주 부실 → 대주 신용 익스포저",
        "exposure_kind": "facility_total_context" if fac else "loan_principal_outstanding",
        "period_basis": "current_period_당기말",
        "verification_gap": "개별 배분 미공개" if fac else None,
    }


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    edges = net["edges"]
    by_id = {e["id"]: i for i, e in enumerate(edges)}
    added, replaced = [], []

    for row in ROWS:
        if row.get("zero_outstanding") and row.get("krw") == 0 and row.get("facility_context"):
            # skip adding zero-outstanding facility edge to avoid clutter; record in docs only
            continue
        promote(net, row["source"], row["name"])
        if row["target"] not in {n["id"] for n in net["nodes"]}:
            continue
        e = edge_from(row)
        src_id = e["source_ids"][0]
        if not any(s.get("id") == src_id for s in net.get("sources") or []):
            net.setdefault("sources", []).append({
                "id": src_id, "title": row["title"], "publisher": "DART",
                "url": e["source_url"], "kind": "filing", "dart_receipt_number": row["rcept"],
                "used_for": "차입금 주석 당기말",
            })
        if e["id"] in by_id:
            edges[by_id[e["id"]]] = e
            replaced.append(e["id"])
        else:
            edges.append(e)
            by_id[e["id"]] = len(edges) - 1
            added.append(e["id"])

    # Fix gaya facility: mark facility_total_context explicitly
    for e in edges:
        if e.get("id") == "dart_facility_gaya_term_loan_2025":
            e["amount_type"] = "facility_total_context"
            e["facility_total_context"] = True
            e["shock_eligible"] = False
            e["roles"] = ["facility_context"]
            e["period_basis"] = "current_period_당기말"
            e["exposure_kind"] = "facility_total_context"
            e["amount_note"] = (
                "Term Loan A+B 당기말 합계 2,385억 — 시설 합계 컨텍스트. "
                "개별 대주 잔액은 dart_loan_*_gaya_* 에 매핑."
            )
        if e.get("id", "").startswith("dart_loan_") and e.get("target") == "gaya_pfv":
            e["period_basis"] = e.get("period_basis") or "current_period_당기말"

    # Demote landmark KB A-2 300억 — not in 당기말 note (KB only 200억)
    for e in edges:
        if e.get("id") == "v6_glm_refi_kb_bank_A-2":
            e["exposure_status"] = "SUPERSEDED_BY_DART_AUDIT"
            e["shock_eligible"] = False
            e["relationship_status"] = "unverified_current"
            e["verification_gap"] = "2025.12 감사 주석5 당기말 KB국민은행 200억만 기재 — A-2 300억 미확인"
            e["period_basis"] = "not_in_latest_current_column"

    # Align landmark current edges period_basis
    for e in edges:
        if e.get("target") == "gasan_landmark_pfv" and str(e.get("exposure_status", "")).startswith("ACTIVE"):
            if e.get("id", "").startswith("v6_glm_refi_") and "A-2" not in e.get("id", ""):
                e["period_basis"] = "current_period_당기말"
                e["amount_as_of"] = e.get("amount_as_of") or "2025-12-31"
                e["source_title"] = e.get("source_title") or "가산랜드마크데이터센터피에프브이 감사보고서 (2025.12)"
                e["dart_receipt_number"] = e.get("dart_receipt_number") or "20260406003009"

    # Align gasan_dc_jv current edges
    for e in edges:
        if e.get("target") == "gasan_dc_jv" and str(e.get("exposure_status", "")).startswith("ACTIVE"):
            e["period_basis"] = "current_period_당기말"
            e["amount_as_of"] = e.get("amount_as_of") or "2025-12-31"
            e["dart_receipt_number"] = e.get("dart_receipt_number") or "20260406000434"

    # Demote overlapping bukhang v6 where dart now covers same lenders (avoid double count)
    dart_bukhang_sources = {r["source"] for r in ROWS if r["target"] == "bukhang_idc_pfv"}
    # also existing dart-like - meritz etc still on v6 — convert v6 active to superseded when we have full dart set
    # Add dart edges for meritz etc as well for consistency
    for eid, src, name, krw, rate in [
        ("dart_loan_meritz_fire_bukhang", "meritz_fire", "메리츠화재해상보험", 25_800_000_000, "7.0%"),
        ("dart_loan_meritz_capital_bukhang", "meritz_capital", "메리츠캐피탈", 25_800_000_000, "7.0%"),
        ("dart_loan_jt_bukhang", "jt_savings", "JT저축은행", 3_000_000_000, "7.0%"),
        ("dart_loan_daol_bukhang", "daol_savings", "다올저축은행", 10_000_000_000, "9.0%"),
        ("dart_loan_artic_bukhang", "artic_nh_lp", "합자조합 ARTIC NORTH HARBOUR", 5_000_000_000, "12.0%"),
        ("dart_loan_acuon_sav_bukhang", "acuon_savings", "애큐온저축은행", 4_000_000_000, "9.0%"),
        ("dart_loan_acuon_cap_bukhang", "acuon_capital", "애큐온캐피탈", 4_000_000_000, "9.0%"),
    ]:
        row = {
            "id": eid, "source": src, "target": "bukhang_idc_pfv", "name": name,
            "krw": krw, "rate": rate, "maturity": None,
            "rcept": BH, "as_of": "2025-12-31", "title": BH_T,
            "note": f"주석6 당기말 단기차입금 {name} {eok(krw):g}억",
            "financing_stage": "bridge",
        }
        promote(net, src, name)
        e = edge_from(row)
        if e["id"] in by_id:
            edges[by_id[e["id"]]] = e
            replaced.append(e["id"])
        else:
            edges.append(e)
            by_id[e["id"]] = len(edges) - 1
            added.append(e["id"])

    for e in edges:
        if e.get("target") == "bukhang_idc_pfv" and str(e.get("id", "")).startswith("v6_bh_br_"):
            e["exposure_status"] = "SUPERSEDED_BY_DART_AUDIT"
            e["shock_eligible"] = False
            e["verification_gap"] = "당기말 잔액은 dart_loan_*_bukhang 로 대체"

    net["edges"] = edges
    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.write_text(json.dumps({
        "added": added, "replaced": replaced, "row_defs": len(ROWS),
        "blueribbon_status": "Reviewed — no outstanding borrowings disclosed (당기말 잔액 전부 -)",
        "koramco_status": "Reviewed — no outstanding borrowings disclosed",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"batch2 added={len(added)} replaced={len(replaced)}")


if __name__ == "__main__":
    main()
