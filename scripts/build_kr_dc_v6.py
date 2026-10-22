#!/usr/bin/env python3
"""
국내 AI 데이터센터 PF 관계 데이터 v6 빌드.

입력
  scripts/data/pf_v5_baseline/network.json, projects.json   (v5 기준선 — 덮어쓰지 않음)
  scripts/kr_dc_ledger.py                                   (조사 원장)
출력
  frontend/public/data/pf/network.json, projects.json       (앱이 읽는 데이터)
  frontend/public/data/pf/kr_dc_relationships.json / .csv   (관계·출처 목록)
  frontend/public/data/pf/kr_dc_entity_status.json / .csv   (기업별 조사 현황)
  frontend/public/data/pf/kr_dc_open_issues.json            (미해결 목록)
  frontend/public/data/pf/kr_dc_changelog.json              (변경 내역)

재실행해도 결과가 같다(기준선에서 매번 다시 만든다).

원칙
- 총 PF·주선 규모를 개별 대주에 배분하지 않는다. 비공개 금액은 None.
- 금액 종류(약정/실행/잔액/한도/도급액)를 섞어 합산하지 않는다.
- 같은 프로젝트 참여만으로 기업끼리 직접 연결하지 않는다(모든 관계는 차주·SPV·펀드를 거친다).
- 계약 방향(제공→수취)과 충격 전파 방향은 별도 필드로 둔다.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "data" / "pf_v5_baseline"
OUT = ROOT / "frontend" / "public" / "data" / "pf"
TODAY = "2026-10-21"


def load_ledger():
    spec = importlib.util.spec_from_file_location("kr_dc_ledger", ROOT / "scripts" / "kr_dc_ledger.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── 1. 중복 법인 병합 (old_id → canonical_id) ──────────────────────────
MERGE = {
    "kreit": "korealand_trust",            # 한국토지신탁 (3중복)
    "korea_land_trust": "korealand_trust",
    "woori_trust": "woori_asset_trust",    # 우리자산신탁 (2중복)
    "ibk": "ibk_bank",                     # IBK기업은행 = 기업은행
    "woori_ib": "woori_inv_sec",           # 우리종합금융 → 2024 우리투자증권으로 재편
    "hanwha_eng": "hanwha_corp",           # 한화건설 → 2022 (주)한화 건설부문으로 합병
    "kfcc": "nh_fg",                       # ID 'kfcc'(새마을금고 약칭)에 '농협금융지주' 이름이 붙어 있던 오류
}
CANON_PATCH = {
    "korealand_trust": dict(name="한국토지신탁", name_ko="한국토지신탁", entity_type="trust_company", group="kr_trust"),
    "nh_fg": dict(name="농협금융지주", name_ko="농협금융지주", entity_type="holding", group="kr_bank"),
    "ibk_bank": dict(name="IBK기업은행", name_ko="IBK기업은행", entity_type="bank", group="kr_bank"),
    "woori_inv_sec": dict(name="우리투자증권", name_ko="우리투자증권"),
    "pacific_sunny_spv": dict(name="퍼시픽써니 시행 SPC(법인명 미확인)", name_ko="퍼시픽써니 시행 SPC(법인명 미확인)"),
}
# 실재 단일 법인이 아닌 노드 (새마을금고는 개별 금고 또는 중앙회 단위로만 계약한다)
DELETE_NODES = {
    "mg_seoul": "‘서울특별시새마을금고’ 등 시·도 명칭 노드는 실재 단일 법인이 아님(중앙회 지역본부/가칭) — 삭제",
    "mg_busan": "시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님", "mg_incheon": "시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님",
    "mg_daegu": "시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님", "mg_gwangju": "시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님",
    "mg_daejeon": "시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님", "mg_ulsan": "시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님",
    "mg_gyeonggi": "시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님",
}

# ── 2. v5 관계 중 공시로 대체·정정되는 것 ──────────────────────────────
REPLACED = {
    # 케이스퀘어 가산: 딜사이트(2024-07) 대주·금액 → 2025 감사보고서(상환된 종전 대주 + 리파이낸싱 대주)로 대체
    **{k: "케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)" for k in [
        "pf_nh_casequare", "pf_tongyang_casequare", "pf_hyundai_cap_casequare", "pf_woori_cap_casequare",
        "pf_shinhan_cap_casequare", "pf_kb_cap_casequare", "pf_hyundai_com_casequare", "pf_woori_ib_casequare",
        "pf_thek_casequare", "pf_kis_junior_casequare", "pf_mountain_casequare"]},
    "pf_koramco_am_casequare": "감사보고서 주주·자산관리 관계로 대체", "pf_koramco_trust_eq": "감사보고서 주주명부로 대체",
    "pf_db_ins_eq": "감사보고서 주주명부로 대체",
    "pf_lf_casequare": "LF 출자액 97억(오기) → 감사보고서 970억(66.9%)으로 정정 대체",
    "pf_hyundai_casequare_epc_co": "감사보고서 시공·우선수익권 소멸(준공) 관계로 대체",
    # 캄스퀘어 안산
    "pf_eugene_camsquare": "감사보고서 2종종류주 출자로 대체", "pf_korea_alt_camsquare": "감사보고서 AMC·출자 관계로 대체",
    "pf_camsquare_first_to_pfv": "감사보고서 Tr.A 약정 1,240억·실행 200.8억으로 대체",
    # 캄스퀘어 용인: '한화투자증권 530억 직접 대출' → 'SPC 380억(선순위)' + 'SK증권 SPC 70억(후순위)'
    "pf_hanwha_camsq_yongin_bridge": "딜북(2026-02) 기준 한화투자증권 SPC 380억 경유 관계로 정정 — 선순위 530억 전액 배분 오류",
    "pf_sksec_camsq_yongin_mezz": "SK증권 SPC 경유 관계로 정정",
    # 마그나 덕이: 금액 없는 대주 8곳 → 감사보고서 대주별 약정·실행액
    **{f"pf_magna_lender_{k}": "마그나 2025 감사보고서 대주별 약정·실행액으로 대체" for k in [
        "ibk", "hana_bank", "nh_bank", "kb_bank", "shinhan_bank", "hyundai_capital", "shinhan_capital", "hanwha_life"]},
    "pf_hana_sec_magna_arranger": "원장 주선 관계로 대체", "pf_gs_magna_parent": "감사보고서 주주명부(51.39%)로 대체",
    "pf_gs_magna_epc": "감사보고서 도급액 1,783억(GMP)·책임준공으로 대체", "pf_k1_magna_equity": "감사보고서 주주명부로 대체",
    "pf_hana_sec_magna_equity": "감사보고서 주주명부로 대체",
    # 부천 삼정 (유진)
    "pf_dongyang_bucheon": "공시(유상증자·주식근질권)로 대체", "pf_hana_bucheon": "공시 채권자 목록으로 대체",
    "pf_bnk_bucheon": "공시 채권자 목록으로 대체", "pf_ibk_bucheon": "공시 채권자 목록으로 대체",
    "pf_hana_cap_bucheon": "공시 채권자 목록으로 대체",
    # 장성 파인DC
    "pf_daewoo_fine_epc": "대우건설 단일판매공급계약(2,525억) 공시로 대체", "pf_daewoo_fine_guar": "대우건설 채무보증결정(2,959억) 공시로 대체",
    # 영등포 엣지코어
    "pf_hanwha_edgecore_support": "한화 주식근질권(2,860억 한도)·도급 공시로 대체",
}
# v5 관계 상태 정정 (삭제하지 않고 상태만 바꾼다)
PATCH_EDGE = {
    "pf_yuanta_mountain": dict(relationship_status="repaid", evidence_status="과거 참여",
                               note_add="마운틴리치제일차의 케이스퀘어 대출(2024말 108억)은 2025 리파이낸싱으로 상환 — 매입확약도 종료된 것으로 봄"),
    "pf_kiwoom_refin": dict(relationship_status="unknown", evidence_status="현재 잔액 미확인",
                            note_add="2025 리파이낸싱 실행(약정 3,800억) — 키움 잔여 보유분 미확인. Tr.B 케이더블유투금제사차(300억) 경유 가능성"),
    "pf_hyundai_camsquare_eq": dict(relationship_status="historical", evidence_status="과거 참여",
                                   note_add="2025말 캄스퀘어안산PFV 주주명부에 현대건설 없음 — 과거 관계"),
    "pf_samsung_sec_camsquare_equity": dict(relationship_status="unknown", evidence_status="자료 상충",
                                            note_add="2025말 주주명부에 삼성증권 없음(특수관계자로만 기재) — 지분 보유 미확인"),
    "pf_admin_camsquare_co": dict(relationship_status="unknown", evidence_status="자료 상충", participation_directness="indirect",
                                  participation_path="대한지방행정공제회 → (투자 경로 미공개: KAAM2호 펀드 수익자 추정) → PFV",
                                  note_add="감사보고서 주주명부에 행정공제회 직접 지분 없음 — 보도된 1,300억은 펀드 경유로 추정"),
    "pf_dl_bucheon_epc": dict(evidence_status="자료 상충", note_add="서울파이낸스(2026-10)는 'DL건설' 수주로 표기 — 법인 표기 확인 필요"),
    "pf_hana_sec_edgecore": dict(evidence_status="자료 상충", note_add="2025 감사보고서에서 하나증권 주선 확인되지 않음 — 언론 보도로만 유지"),
    "pf_cw_kr_funding": dict(layer="scenario", relationship_status="assumption", evidence_status="가정(시나리오 전용)",
                             note_add="코어위브와 새마을금고중앙회 사이에 계약 관계 없음. 시나리오의 '자금시장 심리' 경로를 나타내는 가정 연결이며 직접 익스포저가 아님"),
}

# ── 3. 관계 유형 → 영향 채널·한국어 설명 ───────────────────────────────
CHANNEL = {
    "PROJECT_LOAN": "financial", "ACQUISITION_LOAN": "financial", "CORPORATE_LOAN": "financial", "REVOLVER": "financial",
    "SHAREHOLDER_LOAN": "financial", "PRIORITY_BENEFICIARY": "financial", "CREDIT_ENHANCEMENT": "financial",
    "ABS_SPONSOR": "financial", "DEBT_ASSUMPTION": "financial", "LOAN_GUARANTEE": "financial",
    "COMPLETION_GUARANTEE": "financial", "SHARE_PLEDGE": "financial", "LEASE_GUARANTEE": "financial",
    "COLLATERAL_PROVIDED": "financial", "EQUITY_INVESTMENT": "equity",
    "EPC_CONTRACT": "facility", "FACILITY_OPERATION": "facility", "TENANT_LEASE": "customer",
    "ARRANGER": "contract", "FINANCIAL_ADVISOR": "contract", "ASSET_MANAGER": "contract", "TRUST_SERVICES": "contract",
    "INSURANCE_PLEDGE": "contract", "ASSET_SALE": "contract", "PARENT_AFFILIATE": "contract",
}
VERB = {
    "PROJECT_LOAN": "{s}이(가) {t}에 {stage}대출을 제공",
    "ACQUISITION_LOAN": "{s}이(가) {t}에 인수금융 대출을 제공",
    "CORPORATE_LOAN": "{s}이(가) {t}에 시설자금(기업) 대출을 제공",
    "REVOLVER": "{s}이(가) {t}에 신용공여(한도) 대출을 약정",
    "SHAREHOLDER_LOAN": "주주 {s}이(가) {t}에 주주대여(후순위 성격)를 제공",
    "PRIORITY_BENEFICIARY": "{s}이(가) {t} 담보신탁의 우선수익권을 보유(대출 담보 목적)",
    "CREDIT_ENHANCEMENT": "{s}이(가) {t}의 차입에 신용보강(매입확약·보증 등)을 제공",
    "ABS_SPONSOR": "{s}이(가) 유동화 SPC {t}를 통해 대출에 관여(신용보강 조건 미공개)",
    "DEBT_ASSUMPTION": "{s}이(가) 조건 충족 시 {t}의 대출 채무를 인수할 의무를 부담",
    "LOAN_GUARANTEE": "{s}이(가) {t}의 차입금에 연대보증을 제공",
    "COMPLETION_GUARANTEE": "시공사 {s}이(가) {t} 사업의 책임준공을 대주에게 확약",
    "SHARE_PLEDGE": "{s}이(가) 보유한 {t} 주식을 대주에게 근질권 담보로 제공",
    "LEASE_GUARANTEE": "{s}이(가) {t}에 대한 임차인의 책임임차 의무를 연대보증",
    "COLLATERAL_PROVIDED": "{s}이(가) {t}의 차입을 위해 자기 자산을 추가 담보로 제공",
    "EQUITY_INVESTMENT": "{s}이(가) {t}에 출자(지분 보유)",
    "EPC_CONTRACT": "{s}이(가) {t}와 공사(시공) 계약",
    "FACILITY_OPERATION": "{s}이(가) {t}의 데이터센터를 위탁운영",
    "TENANT_LEASE": "{s}이(가) {t}의 데이터센터를 임차(임대료 지급)",
    "ARRANGER": "{s}이(가) {t}의 금융을 주선(주선 규모는 보유 익스포저가 아님)",
    "FINANCIAL_ADVISOR": "{s}이(가) {t}의 금융자문을 수행",
    "ASSET_MANAGER": "{s}이(가) {t}의 자산관리(AMC)·운용을 담당",
    "TRUST_SERVICES": "{s}이(가) {t}의 담보신탁·자금관리를 수탁(자기 익스포저 아님)",
    "INSURANCE_PLEDGE": "{s}이(가) 보험금채권을 {t} 대주에게 근질권으로 제공",
    "ASSET_SALE": "{s}이(가) {t}에 사업부지·자산을 매도",
    "PARENT_AFFILIATE": "{s}이(가) {t}의 모회사·계열",
}
SHOCK_DIR = {
    "PROJECT_LOAN": "차주(사업법인) 부실 → 대주 신용손실 가능 (손실률은 선후순위·담보에 따라 다름 · 미산정)",
    "ACQUISITION_LOAN": "차주 현금흐름 악화 → 대주 신용위험 (미산정)",
    "CORPORATE_LOAN": "차주(운영사) 부실 → 대주 신용위험 (미산정)",
    "REVOLVER": "미인출 한도 — 인출 시 신용위험",
    "SHAREHOLDER_LOAN": "후순위 성격 — 사업 손실을 선순위보다 먼저 흡수",
    "PRIORITY_BENEFICIARY": "담보 처분 시 순위에 따라 회수",
    "CREDIT_ENHANCEMENT": "사업 차환 실패 시 제공자에게 유동성·인수 부담 (조건부)",
    "ABS_SPONSOR": "유동화증권 차환 실패 시 매입확약 이행 가능성 (조건 미공개)",
    "DEBT_ASSUMPTION": "책임준공 미이행 시에만 채무인수 — 원리금 자동 보증 아님",
    "LOAN_GUARANTEE": "차주 미상환 시 보증인 이행 (조건부)",
    "COMPLETION_GUARANTEE": "준공 지연·미준공 시 시공사 부담 — 원리금 지급보증과 다름",
    "SHARE_PLEDGE": "기한이익상실 시 주식 처분 — 출자자의 지분가치 상실(추가 보증 아님)",
    "LEASE_GUARANTEE": "임차인 미지급 시 보증인 이행 (조건부)",
    "COLLATERAL_PROVIDED": "담보 실행 시 제공자 자산 처분",
    "EQUITY_INVESTMENT": "사업 손실 → 지분가치 감소 (최후순위)",
    "EPC_CONTRACT": "사업 중단 → 공사대금 회수 지연 (미수공사비 미공개)",
    "FACILITY_OPERATION": "가동률·임차 저하 → 운영수수료 감소 (정성)",
    "TENANT_LEASE": "임차인 부실 → 사업 임대수입 감소 (반대 방향)",
}

STAGE_KO = {"bridge": "브릿지 ", "main_pf": "본PF ", "refinancing": "리파이낸싱 ", "securitization": "유동화 ",
            "equity": "", "construction": "", "operations": "", None: ""}
STATUS_KO = {"review": "검토·협의", "mou": "MOU·의향서", "committed": "약정 체결", "funded": "실행·투자 집행",
             "operating": "운영 중", "repaid": "상환·회수·양도", "terminated": "종료·철회", "unknown": "현재 상태 미확인",
             "historical": "과거 관계", "assumption": "가정(시나리오)", "current": "현재"}

FOREIGN = {"brookfield_apac_dc": "SG", "stt_korea_dc": "SG", "mizuho_bank": "JP", "ca_cib": "FR", "ubob_seoul": "SG",
           "bnp_paribas": "FR", "mufg": "JP", "ing_bank": "NL", "socgen": "FR", "ocbc": "SG", "natixis": "FR",
           "warburg_pincus": "US", "digital_edge_dev": "SG"}
FIN_GROUPS = {"kr_bank", "kr_securities", "kr_insurance", "kr_savings", "kr_cooperative", "kr_am", "kr_trust", "financial"}


def fmt_eok(v):
    if v is None:
        return None
    return f"{v:,.2f}".rstrip("0").rstrip(".") + "억"


def amount_note(r):
    at = r["amount_type"]
    a, d = r["amount_krw_eok"], r["drawn_krw_eok"]
    label = {
        "institution_commitment": "기관별 약정", "historical_commitment": "과거 약정(상환됨)",
        "historical_outstanding": "과거 잔액(상환됨)", "outstanding": "기준일 잔액", "equity_paid_in": "출자 납입액",
        "equity_par_value": "출자(액면 기준)", "equity_book_value": "보유주식 장부가", "equity_subscription": "증자 납입액",
        "priority_beneficiary_limit": "우선수익권 한도", "guarantee_limit": "보증·채무인수 한도",
        "guarantee_amount": "보증 금액", "pledge_limit": "근질권 한도", "construction_contract_value": "공사 도급액",
        "construction_billing_period": "기간 기성·거래예정액(총 도급액 아님)", "fee_paid": "지급 수수료",
        "facility_total_context": "시설 총액(맥락)", "asset_sale_price": "매매대금", "collateral_limit": "담보 설정액",
        "credit_support_limit": "신용보강 한도",
    }.get(at or "", at or "")
    if a is None:
        return f"{label} 금액 미공개" if label else "금액 미공개"
    s = f"{label} {fmt_eok(a)}"
    if d is not None and at in ("institution_commitment",):
        s += f" · 실행 {fmt_eok(d)}"
    if r.get("amount_as_of"):
        s += f" (기준 {r['amount_as_of']})"
    return s


def evidence_status(r):
    if r["relationship_status"] == "repaid":
        return "과거 참여"
    if r.get("conflict"):
        return "자료 상충"
    if r["relationship_status"] in ("review", "mou"):
        return "추진·협의 중"
    if r["relationship_status"] == "unknown":
        return "현재 상태 미확인"
    if r["amount_krw_eok"] is None:
        return "금액 미공개"
    return "공시 확인" if r["evidence_kind"] == "공시" else ("공식 발표 확인" if r["evidence_kind"] == "공식발표" else "언론 보도 확인")


def is_inferred(r):
    blob = " ".join(str(x or "") for x in (r.get("note"), r.get("participation_path"), r.get("role")))
    return "추정" in blob or "INFERRED" in blob


def main():
    L = load_ledger()
    net = json.load(open(BASE / "network.json", encoding="utf-8"))
    pj = json.load(open(BASE / "projects.json", encoding="utf-8"))
    log = {"merged": [], "deleted_nodes": [], "replaced_edges": [], "patched_edges": [], "added_nodes": [],
           "added_edges": [], "projects_added": [], "projects_updated": [], "hidden_nodes": []}

    nodes = {n["id"]: n for n in net["nodes"]}
    # ── 병합 ──
    for old, new in MERGE.items():
        if old not in nodes:
            continue
        if new not in nodes:
            n = deepcopy(nodes[old]); n["id"] = new; nodes[new] = n
        aliases = set(nodes[new].get("aliases", [])) | {old}
        if nodes[old].get("name_ko") and nodes[old]["name_ko"] != nodes[new].get("name_ko"):
            aliases.add(nodes[old]["name_ko"])
        nodes[new]["aliases"] = sorted(aliases)
        del nodes[old]
        log["merged"].append({"from": old, "to": new})
    for cid, patch in CANON_PATCH.items():
        if cid in nodes:
            nodes[cid].update(patch)
    for nid, why in DELETE_NODES.items():
        if nid in nodes:
            del nodes[nid]
            log["deleted_nodes"].append({"id": nid, "reason": why})

    # ── v5 관계 정리 ──
    edges = []
    for e in net["edges"]:
        e = deepcopy(e)
        e["source"] = MERGE.get(e["source"], e["source"]); e["target"] = MERGE.get(e["target"], e["target"])
        if e["id"] in REPLACED:
            log["replaced_edges"].append({"id": e["id"], "reason": REPLACED[e["id"]]})
            continue
        if e["id"] in PATCH_EDGE:
            p = dict(PATCH_EDGE[e["id"]]); add = p.pop("note_add", None)
            e.update(p)
            if add:
                e["amount_note"] = ((e.get("amount_note") or "") + " · " + add).strip(" ·")
                e["verification_gap"] = add
            log["patched_edges"].append({"id": e["id"], "patch": PATCH_EDGE[e["id"]]})
        e.setdefault("layer", "fact")
        e.setdefault("evidence_kind", "언론" if (e.get("source_url") or "").startswith("http") else "기존 데이터")
        if e["source"] in nodes and e["target"] in nodes:
            edges.append(e)

    # ── 신규 기관 노드 ──
    for eid, ent in L.ENTITIES.items():
        if eid in nodes or eid in MERGE:
            continue
        country = FOREIGN.get(eid, "KR")
        nodes[eid] = {
            "id": eid, "name": ent["name_ko"], "name_ko": ent["name_ko"], "name_en": ent["name_en"],
            "group": ent["group"], "sector": ent["entity_type"], "entity_type": ent["entity_type"],
            "role": ent.get("note") or "", "description": ent.get("note") or "",
            "listed": bool(ent.get("listed")), "ticker": None, "exchange": None, "quote_currency": None,
            "listing_note": None if ent.get("listed") else "비상장", "display_size": 1.0,
            "source_status": "VERIFIED", "source_ids": [], "key_drivers": [], "region": "KR", "country": country,
            "is_company": True, "connection_status": "관계 확인", "roles": [], "aliases": ent.get("aliases") or [],
            "added_in": "v6",
        }
        log["added_nodes"].append(eid)

    # ── 출처 ──
    src_by_id = {s["id"]: s for s in net["sources"]}
    for sid, s in L.SOURCES.items():
        src_by_id[sid] = {"id": sid, "title": s["title"], "publisher": s["publisher"], "date": s["date"], "url": s["url"],
                          "used_for": s.get("section") or "", "kind": {"공시": "filing", "언론": "news", "공식발표": "press"}[s["kind"]],
                          "evidence_kind": s["kind"], "rcept_no": s.get("rcept_no")}
    # v5 기사 출처 id 보정 (원장에서 참조하는 기존 출처)
    for legacy in ["S_CASEQUARE_KIWOOM_REFIN", "S_MAGNA_THEBELL_REFIN"]:
        if legacy not in src_by_id:
            src_by_id[legacy] = {"id": legacy, "title": legacy, "publisher": "", "date": "", "url": "", "used_for": "", "kind": "news"}

    # ── 프로젝트 ──
    projects = {p["id"]: p for p in pj["projects"]}
    for pid, P in L.PROJECTS.items():
        base = projects.get(pid)
        if base is None:
            base = {"id": pid, "country": "KR", "region": "KR", "construction_stage": "planned", "source_ids": [],
                    "missing": [], "developer": None, "owner": None, "tenant": None, "target_completion": None,
                    "critical_it_load_mw": None, "korean_counterparties": []}
            projects[pid] = base
            log["projects_added"].append(pid)
        else:
            log["projects_updated"].append(pid)
        base.update({
            "name": P.get("name_ko", base.get("name")), "name_ko": P.get("name_ko", base.get("name_ko")),
            "location": P.get("address") or base.get("location"), "address": P.get("address"),
            "spv": P.get("borrower") or base.get("spv"), "borrower": P.get("borrower"),
            "dc_class": P.get("dc_class"), "stage_ko": P.get("stage"), "financing_summary": P.get("financing_summary"),
            "financing_disclosed": True, "region": "KR", "country": "KR",
            "source_ids": sorted(set((base.get("source_ids") or []) + (P.get("sources") or []))),
            "verification_date": TODAY, "research_v6": True,
        })
        if P.get("permit_match"):
            base["permit_ids"] = sorted(set(base.get("permit_ids", []) + [P["permit_match"]]))
    # 조사로 확인한 단계(stage_ko) ↔ 시뮬레이션용 construction_stage 정합화 (v5 값이 실제 진행 단계와 달랐음)
    STAGE_ENUM = {
        "casequare_gasan": "stabilized_operating", "camsquare_ansan": "under_construction",
        "bundang_hostway_idc": "stabilized_operating", "camsquare_yongin": "pre_construction",
        "yeongdeungpo_yedc": "under_construction", "anseong_rec_dc": "under_construction",
        "yongin_jukjeon_pacific": "stabilized_operating", "bucheon_samjeong_ai": "pre_construction",
        "gwangju_fine_dc": "under_construction", "magna_deogi": "under_construction",
        "incheon_guwol_ai": "planned", "keppel_ansan": "pre_construction", "koramco_siheung_dc": "planned",
        "gasan_stt_seoul1": "stabilized_operating", "busan_ecodelta_dc": "pre_construction",
        "incheon_wonchang_dc": "pre_construction", "bucheon_peach_dc": "under_construction",
        "gasan_dci_sel1": "stabilized_operating", "gunsan_sgc_dc": "pre_construction",
        "donghae_gs_aidc": "pre_construction", "hanam_mkif_dc": "stabilized_operating",
        "bupyeong_digital_edge": "expanding", "goyang_samsong_dc": "completed_permit",
        "pohang_ai_factory": "pre_construction", "yongin_deokseong_dc": "under_construction",
        "incheon_dohwa_dc": "pre_construction", "hanam_edge_dc": "under_construction",
        "incheon_bukhang_idc": "pre_construction", "gasan_edc_mastern": "pre_construction",
        "guro_gaebong_dc": "planned",
    }
    log.setdefault("project_field_fixes", [])
    for pid, enum in STAGE_ENUM.items():
        if pid in projects and projects[pid].get("construction_stage") != enum:
            log["project_field_fixes"].append({"project": pid, "field": "construction_stage",
                                               "from": projects[pid].get("construction_stage"), "to": enum,
                                               "reason": f"조사 단계 '{projects[pid].get('stage_ko')}'와 불일치"})
            projects[pid]["construction_stage"] = enum

    # v5 프로젝트 메타 오류 정정
    log.setdefault("project_field_fixes", [])
    cam = projects.get("camsquare_ansan")
    if cam and "아워디씨" in (cam.get("power_note") or ""):
        # 아워디씨(반월산단 엣지DC)는 별개 사업 — 캄스퀘어 안산(성곡동 670-4)에 잘못 매칭된 전력 정보 제거
        cam["power_mw"] = None
        cam["power_note"] = "수전용량 공개자료 미확인 (v5의 7.6MW·아워디씨 기사는 별개 사업 오매칭으로 삭제)"
        log["project_field_fixes"].append({"project": "camsquare_ansan", "field": "power_mw/power_note",
                                           "reason": "아워디씨(반월국가산단 엣지DC) 기사 내용이 잘못 매칭됨 — 별개 사업"})
    for p_ in projects.values():
        for legacy in ("senior_debt_krw_b", "epc_krw_b"):
            if legacy in p_:
                log["project_field_fixes"].append({"project": p_["id"], "field": legacy, "reason":
                    f"단위 표기 오류(값 {p_[legacy]}는 억원인데 필드명은 십억원) · 화면 미사용 — 삭제, 금액은 공시 원장 관계(amount_krw_eok)로 대체"})
                del p_[legacy]

    # 인허가 목록 ↔ 확인 프로젝트 연결 (같은 주소)
    EXTRA_PERMIT = {"magna_deogi": "kr_permit_1000000000000000252655", "bucheon_samjeong_ai": "kr_permit_1000000000000000833142"}
    for pid, permit in EXTRA_PERMIT.items():
        projects[pid]["permit_ids"] = sorted(set(projects[pid].get("permit_ids", []) + [permit]))
    for pid, p in projects.items():
        for permit in p.get("permit_ids", []):
            if permit in projects:
                projects[permit]["linked_project"] = pid
                projects[permit]["map_policy"] = "linked_to_confirmed_project"

    # ── 원장 관계 → 네트워크 엣지 ──
    rel_rows = []
    for r in L.RELS:
        s, t = MERGE.get(r["source"], r["source"]), MERGE.get(r["target"], r["target"])
        if s not in nodes or t not in nodes:
            raise SystemExit(f"unknown node in {r['id']}: {s} / {t}")
        src = src_by_id.get(r["source_ids"][0]) if r["source_ids"] else None
        sname, tname = nodes[s].get("name_ko") or nodes[s]["name"], nodes[t].get("name_ko") or nodes[t]["name"]
        proj = projects.get(r["project_id"]) if r["project_id"] else None
        verb = VERB.get(r["relationship_type"], "{s} → {t}").format(s=sname, t=tname, stage=STAGE_KO.get(r["financing_stage"], ""))
        ev = evidence_status(r)
        e = {
            "id": f"v6_{r['id']}", "source": s, "target": t, "relationship_type": r["relationship_type"],
            "impact_channel": CHANNEL.get(r["relationship_type"], "contract"),
            "label": f"{sname} → {tname} · {verb.split('이(가) ')[-1] if '이(가) ' in verb else verb}",
            "impact_label": verb, "explanation": verb + (f" — {r['role']}" if r.get("role") else ""),
            "source_status": "INFERRED" if is_inferred(r) else "VERIFIED",
            "source_ids": r["source_ids"], "contract_ids": [], "commercial_ids": [],
            "amount_usd_m": None, "amount_krw_eok": r["amount_krw_eok"], "amount_type": r["amount_type"],
            "drawn_krw_eok": r["drawn_krw_eok"], "amount_as_of": r["amount_as_of"], "amount_note": amount_note(r),
            "roles": [r["role"]] if r.get("role") else [], "transmission_class": "direct_contract" if r["participation_directness"] == "direct" else "indirect_vehicle",
            "project_id": r["project_id"], "project_name": (proj or {}).get("name_ko"),
            "financing_stage": r["financing_stage"], "seniority": r["seniority"], "rate": r["rate"], "maturity": r["maturity"],
            "relationship_status": r["relationship_status"], "relationship_status_ko": STATUS_KO.get(r["relationship_status"], r["relationship_status"]),
            "participation_directness": r["participation_directness"], "participation_path": r["participation_path"],
            "evidence_kind": r["evidence_kind"], "evidence_status": ev, "evidence_quote": r["evidence_quote"],
            "contingent_obligation": r["contingent_obligation"], "obligation_trigger": r["obligation_trigger"],
            "stress_direction": SHOCK_DIR.get(r["relationship_type"], ""),
            "verification_date": r["verification_date"], "verification_gap": r.get("note") or "", "conflict": r.get("conflict") or None,
            "source_url": (src or {}).get("url"), "source_title": (src or {}).get("title"), "source_date": (src or {}).get("date"),
            "source_publisher": (src or {}).get("publisher"), "rcept_no": (src or {}).get("rcept_no"),
            "layer": "fact", "added_in": "v6",
        }
        edges.append(e)
        log["added_edges"].append(e["id"])
        rel_rows.append(e)

    # ── 노드 분류·조사 현황 ──
    deg = Counter(); ev_kinds = defaultdict(set); live_fin = defaultdict(bool)
    for e in edges:
        if e.get("layer") == "scenario":
            continue
        for x in (e["source"], e["target"]):
            deg[x] += 1
            ev_kinds[x].add(e.get("evidence_kind") or "")
            if e["impact_channel"] in ("financial", "equity") and e.get("relationship_status") not in ("repaid", "terminated", "historical"):
                live_fin[x] = True
    SELF_DC = {"kakao_cloud": "자체 데이터센터(카카오 안산) 운영 — PF·금융 관계 미발견",
               "naver_cloud": "자체 데이터센터(각 세종 등) 운영 — PF·금융 관계 미발견",
               "kinx": "자체 IDC 운영 — PF·금융 관계 미발견", "gabia": "자체 IDC 운영 — PF·금융 관계 미발견",
               "sk_broadband": "자체 IDC 운영 — PF·금융 관계 미발견", "daou_tech": "자체 데이터센터(죽전) 운영 — PF 관계 미발견",
               "koscom": "자체 데이터센터(안양 호계동) 신축 — PF 관계 미발견", "kepco": "전력 공급자 — 프로젝트별 계약 공시 미발견",
               "dream_mark1": "데이터센터 관련 사업 근거 미발견"}
    HOLDINGS = {"kb_fg", "shinhan_fg", "hana_fg", "woori_fg", "nh_fg"}
    status_rows = []
    hidden = []
    for nid, n in list(nodes.items()):
        is_kr = n.get("region") == "KR" or (not n.get("region") and str(n.get("group", "")).startswith("kr_"))
        if not is_kr:
            continue
        kinds = ev_kinds.get(nid, set())
        if deg[nid] == 0:
            if nid in SELF_DC:
                st, note = "자료 미발견", SELF_DC[nid]
            elif nid in HOLDINGS:
                st, note = "자료 미발견", "지주회사 — 자회사(은행·증권 등)의 개별 참여는 자회사 노드에 표시. 지주 직접 참여 근거 없음"
            else:
                st, note = "자료 미발견", ("DART 사업법인 감사보고서 30여 건의 대주·주주·보증 명부 대조와 언론 검색에서 "
                                         "국내 데이터센터 사업 참여 근거를 찾지 못함 (공개자료 부재 ≠ 관계 없음)")
            n["research_status"] = st; n["research_note"] = note; n["map_hidden"] = True
            hidden.append(n); del nodes[nid]
            log["hidden_nodes"].append(nid)
        else:
            if "공시" in kinds:
                st = "조사 완료 · 공시 확인"
            elif kinds & {"언론", "공식발표"}:
                st = "일부 확인 · 언론/공식발표"
            else:
                st = "기존 데이터 유지 · 추가 근거 미발견"
            n["research_status"] = st
            n["connection_status"] = "관계 확인"
            if n.get("group") in FIN_GROUPS or n.get("entity_type") in ("fund", "spv"):
                n["pf_exposure_class"] = "confirmed_dc_finance" if live_fin[nid] else (n.get("pf_exposure_class") or "confirmed_dc_finance")
            elif n.get("group") in ("project_finance",):
                n["pf_exposure_class"] = "confirmed_aidc_project"
            elif n.get("added_in") == "v6" or n.get("pf_exposure_class") in (None, "research_candidate", "general_pf"):
                n["pf_exposure_class"] = "confirmed_aidc_project"
        status_rows.append({"id": nid, "name_ko": n.get("name_ko") or n["name"], "group": n.get("group"),
                            "entity_type": n.get("entity_type"), "research_status": n.get("research_status"),
                            "relations": deg[nid], "live_financial_or_equity": bool(live_fin[nid]),
                            "evidence_kinds": "/".join(sorted(k for k in kinds if k)),
                            "note": n.get("research_note", ""), "added_in": n.get("added_in", "v5"),
                            "aliases": "/".join(n.get("aliases", []))})
    for m in log["merged"]:
        status_rows.append({"id": m["from"], "name_ko": "", "group": "", "entity_type": "", "research_status": "병합",
                            "relations": 0, "live_financial_or_equity": False, "evidence_kinds": "",
                            "note": f"중복 법인 → {m['to']}로 병합 (별칭 보존)", "added_in": "v5", "aliases": ""})
    for d in log["deleted_nodes"]:
        status_rows.append({"id": d["id"], "name_ko": "", "group": "kr_cooperative", "entity_type": "cooperative",
                            "research_status": "삭제", "relations": 0, "live_financial_or_equity": False,
                            "evidence_kinds": "", "note": d["reason"], "added_in": "v5", "aliases": ""})

    # 프로젝트별 참여 기관 목록(korean_counterparties) 갱신
    by_proj = defaultdict(set)
    for e in edges:
        if e.get("project_id"):
            by_proj[e["project_id"]] |= {e["source"], e["target"]}
    for pid, ids in by_proj.items():
        if pid in projects:
            projects[pid]["korean_counterparties"] = sorted(i for i in ids if i in nodes)
            projects[pid]["graph_node"] = True

    # ── 메타·출력 ──
    net["nodes"] = list(nodes.values())
    net["edges"] = edges
    net["hidden_nodes"] = hidden
    net["sources"] = list(src_by_id.values())
    net["meta"]["as_of"] = TODAY
    net["meta"]["kr_dc_research"] = {
        "version": "v6", "date": TODAY, "ledger": "scripts/kr_dc_ledger.py", "build": "scripts/build_kr_dc_v6.py",
        "method": "DART 사업법인(PFV·SPC·시행사) 감사보고서 주석(주주·차입금·약정·담보신탁·특수관계자)과 "
                  "건설사·계열사 공시(채무보증·도급·담보·유상증자)를 1차 근거로, 신뢰 가능한 언론·회사 발표를 2차 근거로 사용",
        "amount_unit": "억원 (KRW 100,000,000)",
        "principles": ["총 PF·주선 규모를 개별 대주에 배분하지 않음", "비공개 금액은 null('미공개')",
                       "약정·실행·잔액·한도·도급액을 합산하지 않음", "같은 프로젝트 참여만으로 기업끼리 직접 연결하지 않음",
                       "계약 방향과 충격 전파 방향을 별도 필드(stress_direction)로 둠"],
        "counts": {"projects_confirmed": sum(1 for p in projects.values() if p.get("research_v6")),
                   "relations_v6": len(rel_rows), "nodes_added": len(log["added_nodes"]),
                   "nodes_hidden": len(hidden), "edges_replaced": len(log["replaced_edges"])},
    }
    net["meta"]["disclaimer"] = (net["meta"].get("disclaimer", "") + " v6: 국내 DC 관계는 DART 감사보고서·공시 우선. "
                                 "주선·신탁업자·자산관리 역할은 보유 익스포저가 아님. 코어위브↔국내 PF 직접 계약 없음.")
    pj["projects"] = list(projects.values())
    pj["as_of"] = TODAY

    OUT.mkdir(parents=True, exist_ok=True)
    net["kr_dc_issues"] = L.OPEN_ISSUES
    json.dump(net, open(OUT / "network.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(pj, open(OUT / "projects.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    cols = ["id", "project_id", "project_name", "source", "target", "relationship_type", "financing_stage", "seniority",
            "relationship_status_ko", "participation_directness", "participation_path", "amount_krw_eok", "amount_type",
            "drawn_krw_eok", "amount_as_of", "rate", "maturity", "contingent_obligation", "obligation_trigger",
            "evidence_kind", "evidence_status", "source_status", "source_title", "source_publisher", "source_date",
            "rcept_no", "source_url", "evidence_quote", "verification_date", "verification_gap"]
    name = {i: (n.get("name_ko") or n["name"]) for i, n in nodes.items()}
    with open(OUT / "kr_dc_relationships.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(cols[:5] + ["source_name", "target_name"] + cols[5:])
        for e in rel_rows:
            w.writerow([e.get(c) for c in cols[:5]] + [name.get(e["source"]), name.get(e["target"])] + [e.get(c) for c in cols[5:]])
    json.dump({"as_of": TODAY, "relationships": rel_rows, "sources": [src_by_id[s] for s in L.SOURCES]},
              open(OUT / "kr_dc_relationships.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    scol = ["id", "name_ko", "group", "entity_type", "research_status", "relations", "live_financial_or_equity",
            "evidence_kinds", "note", "added_in", "aliases"]
    with open(OUT / "kr_dc_entity_status.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=scol); w.writeheader(); [w.writerow(r) for r in status_rows]
    json.dump({"as_of": TODAY, "entities": status_rows}, open(OUT / "kr_dc_entity_status.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump({"as_of": TODAY, "issues": L.OPEN_ISSUES}, open(OUT / "kr_dc_open_issues.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump({"as_of": TODAY, **log}, open(OUT / "kr_dc_changelog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(net["meta"]["kr_dc_research"]["counts"], ensure_ascii=False))
    print("nodes", len(net["nodes"]), "edges", len(edges), "hidden", len(hidden), "projects", len(projects))


if __name__ == "__main__":
    main()
