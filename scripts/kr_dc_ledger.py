"""
국내 AI 데이터센터 개발사업 — 조사 원장 (v6)

이 파일은 사람이 검토할 수 있는 '사실 원장'이다. 빌드 스크립트
(scripts/build_kr_dc_v6.py)가 이 원장을 읽어 network.json / projects.json 에
반영하고, 조사 현황표·관계 CSV를 출력한다.

원칙
- 금액 단위: 억원(KRW 100,000,000). 비공개는 None (0으로 두지 않음).
- amount_type: 금액의 성격 (약정/실행/잔액/한도/도급액 …) — 서로 합산하지 않는다.
- evidence: "공시"(DART 감사보고서·공시) / "언론"(기사) / "공식발표"(회사·기관 보도자료)
- status: review | mou | committed | funded | operating | repaid | terminated | unknown
- 방향(source→target)은 '계약상 제공 방향'(돈·보증·공사·운영을 제공하는 쪽 → 받는 쪽)이다.
  충격 전파 방향과 같지 않다.
"""
from __future__ import annotations

SOURCES: dict[str, dict] = {}
ENTITIES: dict[str, dict] = {}
PROJECTS: dict[str, dict] = {}
RELS: list[dict] = []
ENTITY_STATUS: dict[str, dict] = {}   # 기업별 조사 현황 메모 (빌드 시 자동 판정과 병합)
OPEN_ISSUES: list[dict] = []


def S(sid, kind, title, publisher, date, url, rcept_no=None, section=None):
    SOURCES[sid] = dict(id=sid, kind=kind, title=title, publisher=publisher,
                        date=date, url=url, rcept_no=rcept_no, section=section)


def E(eid, name_ko, etype, group, name_en=None, note=None, parent=None, aliases=None, listed=False):
    """새 기업·기관·펀드·SPC 등록 (기존 노드면 빌드 시 무시하고 기존 것 사용)."""
    ENTITIES[eid] = dict(id=eid, name_ko=name_ko, entity_type=etype, group=group,
                         name_en=name_en or name_ko, note=note, parent=parent,
                         aliases=aliases or [], listed=listed)


def P(pid, **kw):
    PROJECTS.setdefault(pid, {"id": pid}).update(kw)


def R(rid, src, dst, rtype, project, *, stage=None, role=None, amt=None, amt_type=None,
      drawn=None, as_of=None, seniority=None, rate=None, maturity=None,
      status="unknown", direct=True, path=None, evidence="공시", sources=(),
      quote=None, note=None, contingent=False, trigger=None, verified="2026-10-21",
      conflict=None):
    RELS.append(dict(
        id=rid, source=src, target=dst, relationship_type=rtype, project_id=project,
        financing_stage=stage, role=role, amount_krw_eok=amt, amount_type=amt_type,
        drawn_krw_eok=drawn, amount_as_of=as_of, seniority=seniority, rate=rate,
        maturity=maturity, relationship_status=status,
        participation_directness="direct" if direct else "indirect",
        participation_path=path, evidence_kind=evidence, source_ids=list(sources),
        evidence_quote=quote, note=note, contingent_obligation=contingent,
        obligation_trigger=trigger, verification_date=verified, conflict=conflict,
    ))


def ISSUE(project, kind, text):
    OPEN_ISSUES.append(dict(project_id=project, kind=kind, text=text))


# ════════════════════════════════════════════════════════════════════
# 공통 기관 (조사 중 새로 발견된 참여 기관)
# ════════════════════════════════════════════════════════════════════
E("pfv_kaam2_fund", "KAAM일반사모부동산투자신탁제2호", "fund", "kr_am",
  note="한국대체투자자산운용 운용 · 신탁업자 농협은행")
E("hk_life", "흥국생명", "insurer", "kr_insurance", "Heungkuk Life", listed=False)
E("military_mutual", "군인공제회", "mutual_aid", "kr_cooperative", "Military Mutual Aid Association")
E("kb_ins", "KB손해보험", "insurer", "kr_insurance", "KB Insurance")
E("db_life", "DB생명보험", "insurer", "kr_insurance", "DB Life")
E("kdb_life", "KDB생명보험", "insurer", "kr_insurance", "KDB Life")
E("db_capital", "DB캐피탈", "nbFI", "kr_bank", "DB Capital")
E("ok_capital", "OK캐피탈", "nbFI", "kr_bank", "OK Capital")
E("bluecorner_capital", "블루코너캐피탈", "nbFI", "kr_bank", "Blue Corner Capital")
E("db_savings", "DB저축은행", "savings_bank", "kr_savings", "DB Savings Bank")
E("woori_savings", "우리저축은행", "savings_bank", "kr_savings", "Woori Savings Bank (non-group)")
E("jinju_savings", "진주저축은행", "savings_bank", "kr_savings", "Jinju Savings Bank")
E("osb_savings", "OSB저축은행", "savings_bank", "kr_savings", "OSB Savings Bank")
E("goryo_savings", "고려저축은행", "savings_bank", "kr_savings", "Goryo Savings Bank")
E("pureun_savings", "푸른저축은행", "savings_bank", "kr_savings", "Pureun Savings Bank")
E("hb_savings", "HB저축은행", "savings_bank", "kr_savings", "HB Savings Bank")
E("kiwoom_yes_savings", "키움예스저축은행", "savings_bank", "kr_savings", "Kiwoom Yes Savings Bank")
E("kiwoom_savings", "키움저축은행", "savings_bank", "kr_savings", "Kiwoom Savings Bank")
E("hanwha_savings", "한화저축은행", "savings_bank", "kr_savings", "Hanwha Savings Bank")
E("daishin_savings", "대신저축은행", "savings_bank", "kr_savings", "Daishin Savings Bank")
E("baro_savings", "바로저축은행", "savings_bank", "kr_savings", "Baro Savings Bank")
E("lotte_card", "롯데카드", "nbFI", "kr_bank", "Lotte Card")
E("seoul_guarantee", "서울보증보험", "insurer", "kr_insurance", "SGI Seoul Guarantee")


# ════════════════════════════════════════════════════════════════════
# 1. 캄스퀘어 안산 데이터센터 (안산 단원구 성곡동 670-4) — camsquare_ansan
# ════════════════════════════════════════════════════════════════════
S("D_CAMSQ_ANSAN_AR2025", "공시", "캄스퀘어안산데이터센터피에프브이 감사보고서 (2025.12)", "DART · 삼도회계법인",
  "2026-04-13", "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260413002070",
  rcept_no="20260413002070", section="주석 1(주주), 5(차입금), 9(우발부채·약정·담보신탁), 10(특수관계자)")
S("D_CAMSQ_ANSAN_AR2024", "공시", "캄스퀘어안산데이터센터피에프브이 감사보고서 (2024.12)", "DART · 지암회계법인",
  "2025-04-07", "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20250404004127", rcept_no="20250404004127")
P("camsquare_ansan", name_ko="캄스퀘어 안산 데이터센터", address="경기도 안산시 단원구 성곡동 670-4 일원",
  borrower="camsquare_pfv", dc_class="ai_ready_hyperscale",
  financing_summary="본PF 총 약정한도 9,700억원(Tr.A 7,100 · Tr.B 700 · Tr.C 540 · 일반자금 1,360) / 2025말 실행 2,711억원",
  stage="공사 중", sources=["D_CAMSQ_ANSAN_AR2025"])

A = "D_CAMSQ_ANSAN_AR2025"
AS = "2025-12-31"
# 출자 (주주)
R("ka_eq_kaam2", "pfv_kaam2_fund", "camsquare_pfv", "EQUITY_INVESTMENT", "camsquare_ansan", stage="equity",
  amt=1050, amt_type="equity_paid_in", as_of=AS, status="funded", sources=[A],
  role="보통주 99.06% (신탁업자 농협은행 명의)",
  quote="농협은행㈜(KAAM일반사모부동산투자신탁제2호의 신탁업자) 보통주 21,000,000주 99.06%")
R("ka_eq_kaam_am", "korea_alt_am", "camsquare_pfv", "EQUITY_INVESTMENT", "camsquare_ansan", stage="equity",
  amt=20, amt_type="equity_paid_in", as_of=AS, status="funded", sources=[A],
  role="보통주 0.94% + 2종종류주 28.57% · 자산관리회사(AMC)",
  quote="한국대체투자자산운용㈜ 보통주 200,000주(0.94%), 2종종류주 200,000주(28.57%)")
R("ka_amc_kaam", "korea_alt_am", "camsquare_pfv", "ASSET_MANAGER", "camsquare_ansan", status="operating",
  sources=[A], role="자산관리업무 위탁계약", quote="자산관리업무 위탁계약 — 한국대체투자자산운용㈜")
R("ka_eq_eugene", "eugene_inv_sec", "camsquare_pfv", "EQUITY_INVESTMENT", "camsquare_ansan", stage="equity",
  amt=15, amt_type="equity_paid_in", as_of=AS, status="funded", sources=[A],
  role="2종종류주 42.86% (연 15% 누적적 우선배당)", quote="유진투자증권㈜ 2종종류주 300,000주 42.86%")
R("ka_eq_hk", "hk_life", "camsquare_pfv", "EQUITY_INVESTMENT", "camsquare_ansan", stage="equity",
  amt=10, amt_type="equity_paid_in", as_of=AS, status="funded", sources=[A], direct=False,
  path="흥국생명(주식형특정금전신탁250502 신탁업자) → PFV 2종종류주", role="2종종류주 28.57% (신탁 명의)",
  quote="흥국생명보험㈜(주식형특정금전신탁250502의 신탁업자) 2종종류주 200,000주 28.57%",
  note="신탁 명의 보유 — 실질 위탁자는 공시상 미확인")
R("ka_eq_daehan", "daehan_re_trust", "camsquare_pfv", "EQUITY_INVESTMENT", "camsquare_ansan", stage="equity",
  amt=45, amt_type="equity_paid_in", as_of=AS, status="funded", sources=[A],
  role="1종종류주 100% (연 7% 우선배당)", quote="대한토지신탁㈜ 1종종류주 900,000주 100.00%")
R("ka_trust_daehan", "daehan_re_trust", "camsquare_pfv", "TRUST_SERVICES", "camsquare_ansan", status="operating",
  sources=[A], role="부동산 담보신탁 수탁자 · 자금관리 대리사무",
  quote="부동산 담보신탁계약에 따라 대한토지신탁 주식회사를 수탁자로 하여 … 신탁")
# 대출 — Tr.A (선순위, 6.37%, 만기 2028-06-24)
_TA = [
    ("camsquare_first_spc", 1240, 200.8), ("hyundai_capital", 1000, 162.0), ("kb_ins", 700, 113.4),
    ("military_mutual", 700, 113.4), ("db_life", 500, 81.0), ("yk_ansan_d1", 230, 37.3),
    ("kb_capital", 300, 48.6), ("woori_fin_capital", 300, 48.6), ("hyundai_commercial", 300, 48.6),
    ("fund_ks_ansan_idc", 300, 48.6), ("hana_capital", 200, 32.4), ("fund_kyobo_aim_ansan", 200, 32.4),
    ("welcome_savings", 120, 19.5), ("shinhan_capital", 100, 16.2), ("fund_kbimm_newstar2", 100, 16.2),
    ("db_savings", 100, 16.2), ("kis_savings", 100, 16.2), ("bluecorner_capital", 50, 8.1),
    ("woori_savings", 40, 6.4), ("jinju_savings", 20, 3.2), ("osb_savings", 50, 8.1),
    ("db_capital", 50, 8.1), ("kdb_life", 300, 48.6), ("ok_capital", 100, 16.2),
]
for lid, commit, drawn in _TA:
    R(f"ka_trA_{lid}", lid, "camsquare_pfv", "PROJECT_LOAN", "camsquare_ansan", stage="main_pf",
      amt=commit, amt_type="institution_commitment", drawn=drawn, as_of=AS, seniority="선순위(Tr.A)",
      rate="6.37%", maturity="2028-06-24", status="funded", sources=[A],
      quote=f"Tr.A 차입약정 한도 {commit*100:,.0f}백만원 · 대출실행 {drawn*100:,.0f}백만원 (2025말)")
_TB = [("military_mutual", 300, 48.6), ("kb_capital", 200, 32.4), ("camsquare_second_spc", 100, 16.2),
       ("hana_capital", 100, 16.2)]
for lid, commit, drawn in _TB:
    R(f"ka_trB_{lid}", lid, "camsquare_pfv", "PROJECT_LOAN", "camsquare_ansan", stage="main_pf",
      amt=commit, amt_type="institution_commitment", drawn=drawn, as_of=AS, seniority="중순위(Tr.B)",
      rate="8.00%", maturity="2028-06-24", status="funded", sources=[A],
      quote=f"Tr.B 차입약정 한도 {commit*100:,.0f}백만원 · 실행 {drawn*100:,.0f}백만원")
_TC = [("camsquare_third_spc", 240, 38.9), ("fund_kbimm_newstar1", 200, 32.4), ("fund_kbimm_newstar2", 100, 16.2)]
for lid, commit, drawn in _TC:
    R(f"ka_trC_{lid}", lid, "camsquare_pfv", "PROJECT_LOAN", "camsquare_ansan", stage="main_pf",
      amt=commit, amt_type="institution_commitment", drawn=drawn, as_of=AS, seniority="후순위(Tr.C)",
      rate="9.15%", maturity="2028-06-24", status="funded", sources=[A],
      quote=f"Tr.C 차입약정 한도 {commit*100:,.0f}백만원 · 실행 {drawn*100:,.0f}백만원")
R("ka_gen_kaam2", "pfv_kaam2_fund", "camsquare_pfv", "PROJECT_LOAN", "camsquare_ansan", stage="equity",
  amt=1360, amt_type="institution_commitment", drawn=1360, as_of=AS, seniority="일반자금(최후순위 성격 · 5순위 우선수익)",
  rate="12%", maturity="2030-09-07", status="funded", sources=[A],
  quote="일반자금 농협은행㈜(KAAM일반사모부동산투자신탁제2호의 신탁업자) 136,000,000,000 · 12% · 2030-09-07")
# 유동화 SPC ← 증권사 신용보강
E("camsquare_second_spc", "캄스퀘어제이차", "spv", "project_finance", "Camsquare 2nd SPC",
  note="Tr.B 대주 유동화 SPC (PFV 감사보고서상 기타특수관계자 · 삼성증권과 함께 기재)")
E("camsquare_third_spc", "캄스퀘어제삼차", "spv", "project_finance", "Camsquare 3rd SPC",
  note="Tr.C 대주 유동화 SPC")
E("yk_ansan_d1", "와이케이안산디원", "spv", "project_finance", "YK Ansan D1",
  note="Tr.A 대주로 기재된 SPC — 유동화 구조·신용보강 제공자 공개자료 미확인")
E("fund_ks_ansan_idc", "케이에스안산IDC일반사모부동산투자신탁", "fund", "kr_am", note="운용사 공시상 미기재")
E("fund_kyobo_aim_ansan", "교보AIM안산데이터센터일반사모부동산투자신탁", "fund", "kr_am",
  note="신탁업자 NH투자증권 (우선수익자 표기)")
E("fund_kbimm_newstar1", "케이비아이엠엠뉴스타부동산제일호사모투자합자회사", "fund", "kr_am", note="PEF형 투자기구")
E("fund_kbimm_newstar2", "케이비아이엠엠뉴스타부동산제이호사모투자합자회사", "fund", "kr_am", note="PEF형 투자기구")
R("ka_rel_samsung_spc2", "samsung_sec", "camsquare_second_spc", "ABS_SPONSOR", "camsquare_ansan",
  stage="securitization", status="unknown", sources=[A], contingent=True,
  role="PFV 특수관계자로 유동화 SPC와 함께 기재 · 2024년 지급수수료 238억원",
  quote="기타 특수관계자: 캄스퀘어제일차㈜ 캄스퀘어제이차㈜ 캄스퀘어제삼차㈜ 삼성증권㈜",
  note="제이차·제삼차에 대한 삼성증권 신용보강 여부는 공시 주석에 명시 없음 — 관계 성격 미확정")
R("ka_rel_samsung_spc3", "samsung_sec", "camsquare_third_spc", "ABS_SPONSOR", "camsquare_ansan",
  stage="securitization", status="unknown", sources=[A], contingent=True,
  role="PFV 특수관계자로 유동화 SPC와 함께 기재",
  quote="기타 특수관계자: … 캄스퀘어제삼차㈜ 삼성증권㈜", note="신용보강 구조 미확인")
R("ka_fee_samsung", "samsung_sec", "camsquare_pfv", "ARRANGER", "camsquare_ansan", stage="main_pf",
  amt=238.05, amt_type="fee_paid", as_of="2024-12-31", status="committed", sources=[A],
  role="금융주선 (2024년 지급수수료 238.05억원)", quote="삼성증권㈜ 지급수수료 전기 23,805,000,000원",
  note="주선 수수료 — 보유 익스포저 아님")
# 시공·책임준공
R("ka_epc_hdec_ru", "hyundai_enc", "camsquare_pfv", "COMPLETION_GUARANTEE", "camsquare_ansan",
  stage="construction", status="committed", sources=[A], contingent=True,
  trigger="시공사 책임준공 미이행 시 (원리금 지급보증 아님)",
  role="책임준공 · 시공권·유치권 포기 약정", quote="책임준공 — 현대건설㈜: 시공사는 본건 시설을 책임준공의무")
R("ka_epc_hdec_lien", "hyundai_enc", "camsquare_pfv", "EPC_CONTRACT", "camsquare_ansan", stage="construction",
  amt=7328.616, amt_type="priority_beneficiary_limit", as_of=AS, status="committed", sources=[A],
  seniority="4순위 우선수익권 (공사도급금액 담보)",
  quote="4순위 현대건설㈜ 732,861,600,000 공사도급금액 담보",
  note="우선수익권 한도는 도급액 담보 한도이며 미수공사비가 아님")
# 우선수익자 중 대출표에 개별 기재되지 않은 기관 (공동1순위·2·3순위)
_PB = [("shinhan_savings", 120, "공동1순위"), ("goryo_savings", 96, "공동1순위"), ("pureun_savings", 120, "공동1순위"),
       ("kb_savings", 36, "공동1순위"), ("hb_savings", 120, "공동1순위"), ("kiwoom_yes_savings", 36, "공동1순위"),
       ("lotte_card", 240, "공동1순위"), ("acuon_savings", 60, "공동1순위"), ("daishin_savings", 120, "공동1순위"),
       ("hanwha_savings", 60, "공동1순위"), ("kiwoom_savings", 60, "공동1순위"), ("baro_savings", 120, "2순위"),
       ("thek_savings", 120, "3순위")]
for lid, lim, rank in _PB:
    R(f"ka_pb_{lid}", lid, "camsquare_pfv", "PRIORITY_BENEFICIARY", "camsquare_ansan", stage="main_pf",
      amt=lim, amt_type="priority_beneficiary_limit", as_of=AS, seniority=rank, status="unknown",
      sources=[A], direct=False, path="담보신탁 우선수익권 → (대출약정 담보) · 대출 경로 미공개",
      quote=f"{rank} 우선수익권 한도 {lim*100:,.0f}백만원 · 대출약정금 담보",
      note="차입금 표에 이 기관 명의 대출이 없음 → 유동화 SPC(캄스퀘어제일~삼차) 투자자 또는 약정 후 양도 가능성. 경로 미확정")
ISSUE("camsquare_ansan", "자료 상충",
      "언론(아시아경제 2024-11)은 대한지방행정공제회 1,300억 '에쿼티'로 보도. 2025 감사보고서 주주명부에 행정공제회 직접 지분 없음 — "
      "KAAM2호 펀드(보통주 1,050억 + 일반자금 1,360억) 수익자로 참여했을 가능성. 펀드 수익자 명단 비공개 → 투자 경로 미공개로 표시.")
ISSUE("camsquare_ansan", "자료 상충",
      "언론(딜사이트TV 2024-12)은 본PF 8,340억·삼성증권 신용보강 6,800억 보도. 감사보고서 약정한도 합계 9,700억(일반자금 1,360 포함)과 "
      "본PF(Tr.A~C) 8,340억은 일치. 삼성증권 신용보강 6,800억은 유동화 SPC 대상 한도로 보이나 캄스퀘어제일차의 Tr.A 약정은 1,240억뿐 — 대상 범위 미확인.")
ISSUE("camsquare_ansan", "과거 관계",
      "기존 데이터의 '현대건설 지분 50억'은 2025말 주주명부에 없음 → 과거 관계(현재 미보유)로 상태 변경.")


# ════════════════════════════════════════════════════════════════════
# 2. 케이스퀘어 가산 데이터센터 (서울 금천구 가산동 319-19) — casequare_gasan
# ════════════════════════════════════════════════════════════════════
S("D_CASEQ_AR2025", "공시", "케이스퀘어데이터센터피에프브이 감사보고서 (2025.12)", "DART · 내일회계법인",
  "2026-04-09", "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260409001042",
  rcept_no="20260409001042", section="주석 1(주주), 12(장기차입금 당기·전기), 18(우발부채·약정)")
P("casequare_gasan", name_ko="케이스퀘어 가산 데이터센터", address="서울특별시 금천구 가산동 319-19",
  borrower="casequare_pfv", dc_class="colocation_ai_ready", stage="운영 중 (2025 준공·운영 개시)",
  financing_summary="2025 리파이낸싱: Tr.A 3,450억·Tr.B 350억 약정(합계 3,800억) / 2025말 실행 3,746억. "
                    "종전 본PF(2024말 잔액 1,880억)는 상환",
  sources=["D_CASEQ_AR2025"])
C = "D_CASEQ_AR2025"
AS = "2025-12-31"
# 주주
for sid, eq, role, direct, path in [
    ("lf_corp", 970, "보통주 370만주 + 3종 200만주 + 4종 400만주 (66.90%) · 지배기업", True, None),
    ("koramco_trust", 80, "1종·2종 종류주 (5.52%)", True, None),
    ("koramco_am", 40, "1종 종류주 (2.76%) · 자산관리회사", True, None),
    ("db_ins", 110, "3종 종류주 (7.59%)", True, None),
    ("fund_pinetree9", 150, "3종 종류주 (9-1·9-2·9-3호 합계 10.35%) · 신탁업자 한국증권금융", True, None),
    ("fund_hanwha_opp1", 100, "3종 종류주 (6.90%) · 신탁업자 한국증권금융", True, None),
]:
    R(f"cq_eq_{sid}", sid, "casequare_pfv", "EQUITY_INVESTMENT", "casequare_gasan", stage="equity",
      amt=eq, amt_type="equity_paid_in", as_of=AS, status="funded", sources=[C], role=role, direct=direct, path=path,
      quote=f"주주현황 — {role}")
E("fund_pinetree9", "파인트리전문투자형사모투자신탁9호(9-1·9-2·9-3)", "fund", "kr_am",
  note="파인트리자산운용 계열 펀드로 추정되나 운용사 공시상 미기재 · 신탁업자 한국증권금융")
E("fund_hanwha_opp1", "한화기회추구일반사모부동산투자신탁1호", "fund", "kr_am",
  note="한화자산운용 운용 추정(펀드명) · 신탁업자 한국증권금융")
R("cq_amc_koramco", "koramco_am", "casequare_pfv", "ASSET_MANAGER", "casequare_gasan", status="operating",
  sources=[C], role="자산관리업무위탁계약 (연 12억 운용보수)", quote="주식회사 코람코자산운용과 자산관리업무위탁계약")
R("cq_trust_koramco", "koramco_trust", "casequare_pfv", "TRUST_SERVICES", "casequare_gasan", status="operating",
  sources=[C], role="부동산담보신탁 수탁자 · 자금관리업무 수탁", quote="주식회사코람코자산신탁과 부동산담보 신탁계약")
R("cq_pledge_lf", "lf_corp", "casequare_pfv", "SHARE_PLEDGE", "casequare_gasan", status="committed",
  sources=[C], contingent=True, trigger="대출 기한이익상실 시 대주가 LF 보유 PFV 주식 처분 가능 (LF 원리금 보증 아님)",
  role="보유주식 근질권 제공 (Tr.A 1순위·Tr.B 2순위, 약정금 120%)",
  quote="주식회사 엘에프는 Tranche A 대주를 제 1순위 근질권자 … 주식근질권설정계약")
# 2025 리파이낸싱 대주 (현재)
for lid, commit, drawn, tr in [
    ("kyobo_life", 1000, 984, "A"), ("hana_bank", 300, 296, "A"), ("samsung_fire", 850, 836, "A"),
    ("hanwha_life", 1000, 983, "A"), ("thek_savings", 100, 99, "A"), ("shinhan_capital", 200, 198, "A"),
    ("bluecorner_capital", 50, 50, "B"), ("kw_tg4_spc", 300, 300, "B"),
]:
    R(f"cq_refi_{lid}", lid, "casequare_pfv", "PROJECT_LOAN", "casequare_gasan", stage="refinancing",
      amt=commit, amt_type="institution_commitment", drawn=drawn, as_of=AS,
      seniority="선순위(Tr.A)" if tr == "A" else "후순위(Tr.B)", rate="5.50%" if tr == "A" else "7.00%",
      status="funded", sources=[C],
      note="교보생명은 일반계정 500억 + 특별계정 500억 합계" if lid == "kyobo_life" else None,
      quote=f"Tranche {tr} 약정한도 {commit*100:,.0f}백만원 · 실행 {drawn*100:,.0f}백만원")
E("kw_tg4_spc", "케이더블유투금제사차", "spv", "project_finance", "KW TG 4th SPC",
  note="Tr.B 300억 대주로 기재된 유동화 SPC. 명칭상 키움증권 관련 SPC로 추정되나 신용보강 제공자 공시 미확인")
R("cq_refi_kiwoom_spc", "kiwoom_sec", "kw_tg4_spc", "ABS_SPONSOR", "casequare_gasan", stage="refinancing",
  status="unknown", evidence="언론", sources=["S_CASEQUARE_KIWOOM_REFIN"], direct=False, contingent=True,
  path="키움증권(리파이낸싱 3,800억 총액인수 보도) → 케이더블유투금제사차(Tr.B) → PFV",
  note="SPC명(KW)과 키움 3,800억 인수 보도의 일치로 추정한 경로 — INFERRED")
# 종전 본PF 대주 (2024말 잔액 → 2025 상환)
for lid, bal, tr in [
    ("hyundai_capital", 129, "A"), ("woori_fin_capital", 86, "A"), ("tongyang_life", 300, "A"),
    ("mountain_rich", 108, "A"), ("woori_inv_sec", 87, "A"), ("kb_capital", 128, "A"),
    ("fund_aip_digital_frontier1", 172, "A"), ("hyundai_commercial", 86, "A"),
    ("thek_savings", 42, "A"), ("shinhan_capital", 42, "A"), ("korea_inv_sec", 700, "B"),
]:
    R(f"cq_old_{lid}", lid, "casequare_pfv", "PROJECT_LOAN", "casequare_gasan", stage="main_pf",
      amt=bal, amt_type="historical_outstanding", as_of="2024-12-31",
      seniority="선순위(Tr.A)" if tr == "A" else "후순위(Tr.B)", status="repaid", sources=[C],
      quote=f"전기말(2024) Tranche {tr} 잔액 {bal*100:,.0f}백만원 → 당기말 '-'",
      note="2025 리파이낸싱으로 상환(당기말 잔액 없음). 현재 익스포저 아님")
E("fund_aip_digital_frontier1", "에이아이파트너스디지털프런티어일반사모투자신탁1호", "fund", "kr_am",
  note="신탁업자 농협은행. 기존 데이터의 'NH농협은행 직접 대출'은 이 펀드의 신탁업자 명의였음")
R("cq_epc_hdec", "hyundai_enc", "casequare_pfv", "EPC_CONTRACT", "casequare_gasan", stage="construction",
  status="terminated", sources=[C], seniority="3순위 우선수익권(공사도급금액 120%) — 준공·인수인계로 소멸",
  quote="준공 및 사용승인서가 발급되고 … 현대건설 주식회사의 제3순위 우선수익권 및 우선수익자 지위는 소멸",
  note="원문 날짜 표기 '2026년 06월 25일'(2025 사업연도 보고서) — 표기 오류 가능성, 준공 시점 교차확인 필요")
R("cq_ins_pledge_kt", "kt", "casequare_pfv", "INSURANCE_PLEDGE", "casequare_gasan", status="committed",
  sources=[C], contingent=True, role="보험금채권 근질권 제공 (현대건설·KT)",
  quote="현대건설 주식회사 및 주식회사 케이티는 … 보험금채권 근질권설정계약")
ISSUE("casequare_gasan", "자료 상충",
      "딜사이트(2024-07) 대주별 금액(동양생명 70억 등)과 2024말 감사보고서 잔액(동양생명 300억 등)이 다름 — "
      "보도는 일부 트랜치 또는 특정 시점 기준으로 보임. 감사보고서 수치를 우선 표시, 기사 수치는 과거 보도치로 보존.")
ISSUE("casequare_gasan", "날짜 확인", "감사보고서의 준공·사용승인일 '2026-06-25' 표기 확인 필요(2025년 감가상각 개시와 불일치).")
ISSUE("casequare_gasan", "미확인", "케이더블유투금제사차의 신용보강(매입확약) 제공자 · 투자자 공시 미확인.")


# ════════════════════════════════════════════════════════════════════
# 3. 마그나 고양 덕이 데이터센터 (고양 일산서구 덕이동 309-56) — magna_deogi
# ════════════════════════════════════════════════════════════════════
S("D_MAGNA_AR2025", "공시", "마그나피에프브이 감사보고서 (2025.12)", "DART · 도영회계법인", "2026-04-06",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260406003595", rcept_no="20260406003595",
  section="주석 1(주주), 5(장기차입금 당기·전기), 10(우발채무·약정), 11(특수관계자·도급)")
P("magna_deogi", name_ko="마그나 고양 덕이 데이터센터", address="경기도 고양시 일산서구 덕이동 309-56 일원",
  borrower="magna_pfv", dc_class="colocation_ai_ready", stage="공사 중",
  financing_summary="2025-08-29 리파이낸싱: Tr.A-1·A-2 약정 2,730억 / 2025말 실행 908억 (만기 2027-06-05). "
                    "종전 대주단 약정 2,730억(2024말 실행 215억)은 전액 상환",
  sources=["D_MAGNA_AR2025"])
M = "D_MAGNA_AR2025"; AS = "2025-12-31"
for sid, sh, pct in [("gs_enc", 925000, "51.39%"), ("k1_premier_reit", 750000, "41.67%"),
                     ("hana_sec", 125000, "6.94%"), ("korealand_trust", 25, "0.00%")]:
    R(f"mg_eq_{sid}", sid, "magna_pfv", "EQUITY_INVESTMENT", "magna_deogi", stage="equity", amt=None,
      amt_type="equity_paid_in", as_of=AS, status="funded", sources=[M], role=f"보통주 {sh:,}주 ({pct})",
      quote=f"주주구성 — {sh:,}주 {pct}",
      note="자본금 90억 + 주식발행초과금 629.5억(합계 719.5억). 주주별 납입액은 미공개 — 지분율만 표시")
for lid, commit, drawn, tr, rate in [
    ("nh_bank", 250, 83, "A-1", "4.50%"), ("shinhan_capital", 100, 34, "A-2", "5.06%"),
    ("kb_bank", 300, 99, "A-2", "5.06%"), ("shinhan_bank", 400, 134, "A-2", "5.06%"),
    ("hana_bank", 250, 83, "A-2", "5.06%"), ("ibk_bank", 300, 99, "A-2", "5.06%"),
    ("hanwha_life", 700, 232, "A-2", "5.06%"), ("hyundai_capital", 430, 144, "A-2", "5.06%")]:
    R(f"mg_refi_{lid}", lid, "magna_pfv", "PROJECT_LOAN", "magna_deogi", stage="refinancing", amt=commit,
      amt_type="institution_commitment", drawn=drawn, as_of=AS, seniority=f"선순위(Tr.{tr})", rate=rate,
      maturity="2027-06-05", status="funded", sources=[M],
      quote=f"Tranche {tr} 한도 {commit*100:,.0f}백만원 · 실행 {drawn*100:,.0f}백만원 · 만기 2027-06-05")
for lid, commit, drawn, tr, note in [
    ("db_life", 400, None, "A", None), ("ibk_bank", 300, None, "A", "CD+가산금리"), ("kb_capital", 200, None, "A", None),
    ("kb_bank", 300, None, "A", None), ("nh_bank", 250, None, "A", None), ("shinhan_bank", 400, None, "A", None),
    ("fund_shinhan_dc_dev", 150, None, "A", "신탁업자 중소기업은행 명의"), ("shinhan_capital", 100, None, "A", None),
    ("hana_bank", 250, None, "A", None), ("nh_capital", 100, None, "A", None),
    ("fund_shinhan_dc_dev", 130, 100, "B", "신탁업자 중소기업은행 명의 · 9%"), ("blue_dragon7_spc", 150, 115, "B", "9%")]:
    R(f"mg_old_{lid}_{tr}_{commit}", lid, "magna_pfv", "PROJECT_LOAN", "magna_deogi", stage="main_pf",
      amt=commit, amt_type="historical_commitment", drawn=drawn, as_of="2024-12-31",
      seniority=f"{'선순위' if tr=='A' else '후순위'}(Tr.{tr})", maturity="2027-06-05", status="repaid", sources=[M],
      quote=f"전기 Tranche {tr} 한도 {commit*100:,.0f}백만원" + (f" · 실행 {drawn*100:,.0f}백만원" if drawn else " · 실행 -"),
      note=("2025-08-29 리파이낸싱으로 전액 상환. " + (note or "")).strip())
E("fund_shinhan_dc_dev", "신한데이타센터개발일반사모혼합자산투자신탁", "fund", "kr_am",
  note="신한자산운용 운용 추정(펀드명) · 신탁업자 중소기업은행")
E("blue_dragon7_spc", "블루드래곤제칠차", "spv", "project_finance", note="마그나 종전 Tr.B 대주 유동화 SPC · 신용보강 제공자 미확인")
E("nh_capital", "NH농협캐피탈", "nbFI", "kr_bank", "NH Nonghyup Capital")
R("mg_epc_gs", "gs_enc", "magna_pfv", "EPC_CONTRACT", "magna_deogi", stage="construction", amt=1783.15,
  amt_type="construction_contract_value", as_of="2024-11-29", status="committed", sources=[M],
  role="신축공사 도급 (GMP 총액보증한도) · 별도 전력인입공사 444.4억",
  quote="공사도급계약 178,315,000천원 (GMP 총액보증한도금액) · 전력인입공사 계약 44,440,000천원")
R("mg_ru_gs", "gs_enc", "magna_pfv", "COMPLETION_GUARANTEE", "magna_deogi", stage="construction", status="committed",
  sources=[M], contingent=True, trigger="책임준공 기한 내 미준공 시 (원리금 지급보증 아님)",
  amt=2353.758, amt_type="priority_beneficiary_limit", seniority="담보신탁 2순위 수익권",
  quote="시공사인 지에스건설(주)는 … 대주에게 책임준공을 확약 … 235,375,800천원을 한도로 하는 2순위 수익권")
R("mg_trust_kyobo", "kyobo_asset_trust", "magna_pfv", "TRUST_SERVICES", "magna_deogi", status="operating", sources=[M],
  role="부동산담보신탁 수탁자 · 자금관리사무 수탁", quote="교보자산신탁 주식회사를 수탁자로 부동산담보신탁계약")
R("mg_amc_klt", "korealand_trust", "magna_pfv", "ASSET_MANAGER", "magna_deogi", status="operating", sources=[M],
  amt=13.8, amt_type="fee_paid", as_of=AS, role="자산관리위탁계약 (2025 지급수수료 13.8억)",
  quote="한국토지신탁 주식회사와 자산관리위탁계약")
R("mg_lease_dcbridge", "dc_bridge", "magna_pfv", "TENANT_LEASE", "magna_deogi", stage="operations",
  status="committed", sources=[M], role="데이터센터 임차 후 제3자 전대 (임대차계약 2024-11-29)",
  quote="디씨브릿지 주식회사와 … 데이타센터를 임차하고 제3자가 데이타센터를 사용하도록 하는 임대차계약",
  note="임대료·기간 공시 미기재")
R("mg_arranger_hana", "hana_sec", "magna_pfv", "ARRANGER", "magna_deogi", stage="refinancing", status="committed",
  evidence="언론", sources=["S_MAGNA_THEBELL_REFIN"], role="리파이낸싱 주선 (보도)",
  note="2024~2025 하나증권 건설중인자산 계상 수수료 51.9억(감사보고서) — 주선 수수료로 보이며 보유 익스포저 아님")


# ════════════════════════════════════════════════════════════════════
# 4. 부천 삼정동 AI 데이터센터 (부천 오정구 삼정동 48-59) — bucheon_samjeong_ai  (유진그룹)
# ════════════════════════════════════════════════════════════════════
S("D_DCB_PLEDGE_20260512", "공시", "디씨아이티와이부천피에프브이 특수관계인으로부터받은담보", "DART (공정거래법 제26조)",
  "2026-05-12", "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260512000740", rcept_no="20260512000740")
S("D_DCB_CAPINC_20260408", "공시", "디씨아이티와이부천피에프브이 특수관계인의유상증자참여", "DART", "2026-04-08",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260408001372", rcept_no="20260408001372")
S("D_DCB_LAND_20260121", "공시", "디씨아이티와이부천피에프브이 특수관계인으로부터부동산매수", "DART", "2026-01-21",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260121000453", rcept_no="20260121000453")
P("bucheon_samjeong_ai", name_ko="부천 삼정 AI 데이터센터", address="경기도 부천시 오정구 삼정동 48-59, 48-61",
  borrower="dcity_bucheon_pfv", dc_class="ai_dedicated", stage="착공 전·PF 약정",
  financing_summary="PF 대출약정 1,590억 (하나은행·경남은행·하나캐피탈·기업은행), 최초 인출 예정 2026-05-15 · 상환예정 2029-05-15",
  sources=["D_DCB_PLEDGE_20260512"])
B = "D_DCB_PLEDGE_20260512"
for lid in ["hana_bank", "bnk_kyongnam", "hana_capital", "ibk_bank"]:
    R(f"dcb_pf_{lid}", lid, "dcity_bucheon_pfv", "PROJECT_LOAN", "bucheon_samjeong_ai", stage="main_pf",
      amt=None, amt_type="institution_commitment", as_of="2026-05-12", status="committed", sources=[B],
      maturity="2029-05-15",
      quote="채권자 (주)하나은행, (주)경남은행, 하나캐피탈(주), 중소기업은행 · PF대출 약정금(159,000 백만원)",
      note="총 PF 약정 1,590억 — 기관별 배분 미공개 (총액을 각 대주에 배분하지 않음)")
R("dcb_eq_dongyang", "dongyang", "dcity_bucheon_pfv", "EQUITY_INVESTMENT", "bucheon_samjeong_ai", stage="equity",
  amt=495.5, amt_type="equity_book_value", as_of="2026-05-12", status="funded", sources=[B, "D_DCB_CAPINC_20260408"],
  role="보통주 195.5만주 + 3종 종류주 30만주 (2026-04 증자 후 지분율 92.1%)",
  quote="(주)동양이 보유한 당사 주식 2,255,000주 … 담보금액 49,550 (보유 주식 장부가액)")
R("dcb_pledge_dongyang", "dongyang", "dcity_bucheon_pfv", "SHARE_PLEDGE", "bucheon_samjeong_ai", stage="main_pf",
  amt=1908, amt_type="pledge_limit", as_of="2026-05-15", status="committed", sources=[B], contingent=True,
  trigger="PF 기한이익상실 시 대주가 동양 보유 PFV 주식 처분 (동양의 원리금 보증 아님)",
  quote="주식근질권설정계약 … 담보한도 190,800 (PF대출 약정금 159,000의 120%) · 기간 2026.05.15~2029.05.15")
R("dcb_land_yoo", "dongyang", "dcity_bucheon_pfv", "PARENT_AFFILIATE", "bucheon_samjeong_ai", status="funded",
  sources=["D_DCB_LAND_20260121"], role="유진그룹 계열 PFV (기업집단 '유진')",
  quote="기업집단명 유진 · 토지 매수 상대방 유재필(동일인 등) 32,000백만원", note="토지 매도인은 동일인(개인) — 노드로 만들지 않음")

# 4-b. 인천 구월 AI 데이터센터 (인천 남동구 구월동 1128-4) — 유진그룹 (신규 발견)
S("D_DCI_CAPINC_20260121", "공시", "디씨아이티와이인천피에프브이 특수관계인의유상증자참여", "DART", "2026-01-21",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260121000450", rcept_no="20260121000450")
S("D_DCI_LAND_20260121", "공시", "디씨아이티와이인천피에프브이 특수관계인으로부터부동산매수", "DART", "2026-01-21",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260121000457", rcept_no="20260121000457")
E("dcity_incheon_pfv", "디씨아이티와이인천피에프브이", "spv", "project_finance", "DCITY Incheon PFV",
  note="유진그룹 계열 PFV · 인천 구월동 AI 데이터센터 개발")
E("eugene_dlab", "유진디랩", "company", "kr_operator", "Eugene D-Lab", note="유진그룹 계열 · 토지 매도인")
P("incheon_guwol_ai", name_ko="인천 구월 AI 허브센터", address="인천광역시 남동구 구월동 1128-4, 1128-5",
  borrower="dcity_incheon_pfv", dc_class="ai_dedicated", stage="토지 매입·인허가 (PF 미확인)",
  financing_summary="동양 출자 55억(지분 93.1%) · PF 약정 공시 없음", sources=["D_DCI_CAPINC_20260121"],
  permit_match="kr_permit_1000000000000000845805")
R("dci_eq_dongyang", "dongyang", "dcity_incheon_pfv", "EQUITY_INVESTMENT", "incheon_guwol_ai", stage="equity",
  amt=55, amt_type="equity_paid_in", as_of="2026-01-21", status="funded", sources=["D_DCI_CAPINC_20260121"],
  role="보통주 55만주 (증자 후 지분율 93.1%)", quote="(주)동양 출자금액 5,500 · 출자 후 지분율 93.1")
R("dci_land_dlab", "eugene_dlab", "dcity_incheon_pfv", "ASSET_SALE", "incheon_guwol_ai", amt=340,
  amt_type="asset_sale_price", as_of="2026-01-23", status="committed", sources=["D_DCI_LAND_20260121"],
  quote="거래상대방 주식회사 유진디랩 · 토지 인천 남동구 구월동 1128-4, 1128-5 · 34,000", role="사업부지 매도(계열사 간 거래)")


# ════════════════════════════════════════════════════════════════════
# 5. 케펠 안산 데이터센터 (안산 단원구 원시동 726-4, 구 '다올데이터센터1호PFV') — keppel_ansan  (신규 프로젝트 식별)
# ════════════════════════════════════════════════════════════════════
S("D_KEPPEL_ANSAN_AR2025", "공시", "다올데이터센터1호피에프브이(현 케펠데이터센터안산피에프브이) 감사보고서 (2025.12)", "DART",
  "2026-03-30", "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260330000663", rcept_no="20260330000663",
  section="주석 1(주주), 6(담보), 7(차입금), 12(약정), 13(특수관계자·연대보증)")
S("D_KEPPEL_ANSAN_CAPINC", "공시", "케펠데이터센터안산피에프브이 유상증자결정 (제3자배정)", "DART", "2026-06-10",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260610000269", rcept_no="20260610000269")
E("keppel_ansan_pfv", "케펠데이터센터안산피에프브이", "spv", "project_finance", "Keppel Data Centre Ansan PFV",
  aliases=["다올데이터센터1호피에프브이"], note="구 다올데이터센터1호PFV(2022 설립) · 신영그룹 계열 → 2026 케펠 펀드 증자")
E("daol_dmirune", "다올드미루네", "company", "kr_operator", note="PFV 주주 12%")
E("daol_am", "다올자산운용", "asset_manager", "kr_am", "Daol Asset Management")
E("keppel_am_kr", "케펠자산운용", "asset_manager", "kr_am", "Keppel Asset Management Korea")
E("fund_keppel_dc1", "케펠데이터센터일반사모부동산투자신탁제1호", "fund", "kr_am", note="신탁업자 한국투자증권 · 운용 케펠자산운용(펀드명 기반)")
E("gapyeong_coop_group", "가평군농협 외 7개 지역농협(대주단)", "cooperative", "kr_cooperative",
  note="개별 지역농협 명단 공시상 '외 7곳'으로만 기재 — NH농협은행과 다른 법인")
P("keppel_ansan", name_ko="케펠 안산 원시동 데이터센터", address="경기도 안산시 단원구 원시동 726-4",
  borrower="keppel_ansan_pfv", dc_class="ai_ready_hyperscale", stage="브릿지 단계 (본PF 전)",
  financing_summary="2025말 브릿지 310억(지역농협 대주단 200·신한캐피탈 50·신한투자증권 60, 만기 2026-09-29) + 신영 주주대여 210억. "
                    "2026-06 제3자배정 증자 682억(케펠 펀드·현대건설·NH투자증권)",
  sources=["D_KEPPEL_ANSAN_AR2025", "D_KEPPEL_ANSAN_CAPINC"], permit_match="kr_permit_1000000000000000331375")
K = "D_KEPPEL_ANSAN_AR2025"; KC = "D_KEPPEL_ANSAN_CAPINC"; AS = "2025-12-31"
for sid, role in [("shinyoung", "보통주 156,001 + 우선주 24,000 (60%) · 단기차입금 310억 연대보증"),
                  ("daol_dmirune", "보통주 36,000 (12%)"), ("daol_am", "보통주 24,000 (8%) · 용역수수료"),
                  ("shinhan_sec", "보통주 59,999 (20%)")]:
    R(f"kp_eq_{sid}", sid, "keppel_ansan_pfv", "EQUITY_INVESTMENT", "keppel_ansan", stage="equity", amt=None,
      amt_type="equity_paid_in", as_of=AS, status="funded", sources=[K], role=role, quote=f"주요 주주현황 — {role}",
      note="액면 5만원 기준 자본금 150억 중 지분율만 공개 — 2026-06 증자 후 지분율 변동")
for sid, amt, role in [("fund_keppel_dc1", 481.2, "2종 종류주 243,522주 × 197,600원"),
                       ("keppel_am_kr", 1.0, "1종 종류주 2,000주 × 50,000원"),
                       ("hyundai_enc", 100.0, "1종 24,000주 + 2종 44,534주"),
                       ("nh_inv_sec", 100.0, "1종 24,000주 + 2종 44,534주")]:
    R(f"kp_capinc_{sid}", sid, "keppel_ansan_pfv", "EQUITY_INVESTMENT", "keppel_ansan", stage="equity", amt=amt,
      amt_type="equity_subscription", as_of="2026-06-05", status="funded", sources=[KC], role=role,
      quote=f"제3자배정 대상 — {role} (납입일 2026-06-05)",
      note="금액 = 배정주식수 × 발행가(보통 197,600원·우선 50,000원)로 산출")
R("kp_fund_trustee", "korea_inv_sec", "fund_keppel_dc1", "TRUST_SERVICES", "keppel_ansan", status="operating",
  sources=[KC], role="펀드 신탁업자(자산보관) — 자기 익스포저 아님",
  quote="한국투자증권(주) (케펠데이터센터일반사모부동산 투자신탁제1호의 신탁업자)")
R("kp_fund_mgr", "keppel_am_kr", "fund_keppel_dc1", "ASSET_MANAGER", "keppel_ansan", status="operating",
  sources=[KC], evidence="공시", note="펀드명·동시 배정으로 추정한 운용 관계 (INFERRED)")
for lid, amt, rate in [("gapyeong_coop_group", 200, "6.5%"), ("shinhan_capital", 50, "8.00%"), ("shinhan_sec", 60, "9.00%")]:
    R(f"kp_bridge_{lid}", lid, "keppel_ansan_pfv", "PROJECT_LOAN", "keppel_ansan", stage="bridge", amt=amt,
      amt_type="institution_commitment", drawn=amt, as_of=AS, rate=rate, maturity="2026-09-29", status="funded",
      sources=[K], seniority="브릿지 (토지·주식 근질권, 신영 연대보증)",
      quote=f"단기 차입 {amt*100:,.0f}백만원 · {rate} · 만기 2026.09.29 · 약정한도=실행금액",
      note="브릿지 만기 2026-09-29 경과 — 본PF 전환·연장 여부 미확인 (현재 상태 미확인)")
R("kp_sh_loan_shinyoung", "shinyoung", "keppel_ansan_pfv", "SHAREHOLDER_LOAN", "keppel_ansan", stage="bridge",
  amt=210, amt_type="outstanding", as_of=AS, rate="4.60%", maturity="본PF 대출 기표일", status="funded", sources=[K],
  quote="장기 주식회사 신영 4.60% 본개발사업 PF대출기표일 21,000,000천원")
R("kp_guar_shinyoung", "shinyoung", "keppel_ansan_pfv", "LOAN_GUARANTEE", "keppel_ansan", stage="bridge",
  amt=310, amt_type="guarantee_amount", as_of=AS, status="committed", contingent=True, sources=[K],
  trigger="PFV의 브릿지 차입금 미상환 시 신영이 연대보증 이행",
  quote="주식회사 신영은 단기차입금 31,000,000천원에 대해 연대보증을 제공")
ISSUE("keppel_ansan", "현재 상태 미확인", "브릿지 만기(2026-09-29) 이후 본PF 약정·대주단 공시 미확인. 2026-06 케펠 펀드 증자로 최대주주 변경 추정.")
ISSUE("keppel_ansan", "프로젝트 식별", "dc.namepf 인허가 'Arclight'(원시동 726-4)와 주소 일치 → 동일 사업장으로 연결.")

# ════════════════════════════════════════════════════════════════════
# 6. 브룩필드(코람코시화) 안산 성곡동 712 데이터센터 — koramco_siheung_dc (신규 프로젝트 식별)
# ════════════════════════════════════════════════════════════════════
S("D_KRSH_AR2025", "공시", "코람코시화데이터센터피에프브이 감사보고서 (2025.12)", "DART", "2026-04-13",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260413002815", rcept_no="20260413002815",
  section="주석 1(주주), 11(차입부채), 20(특수관계자), 21(약정)")
E("koramco_siheung_pfv", "코람코시화데이터센터피에프브이", "spv", "project_finance", "Koramco Sihwa Data Center PFV",
  note="안산 단원구 성곡동 712 데이터센터 · 2025 브룩필드 지배기업 편입")
E("brookfield_apac_dc", "Brookfield Asia Pacific DC Korea Holdings", "company", "financial",
  "BROOKFIELD ASIA PACIFIC DC KOREA HOLDINGS PTE. LTD.", note="싱가포르 법인 · 브룩필드 계열")
E("dcn_partners", "디씨앤파트너스", "company", "kr_operator", "DC&Partners")
E("goyang_livestock_coop", "고양축산업협동조합", "cooperative", "kr_cooperative")
P("koramco_siheung_dc", name_ko="안산 성곡동 712 데이터센터 (브룩필드·코람코시화PFV)", address="경기도 안산시 단원구 성곡동 712",
  borrower="koramco_siheung_pfv", dc_class="hyperscale_dev", stage="개발 (차입금 전액 상환·지분 투자 단계)",
  financing_summary="2025 유상증자 367억으로 기존 대출 150억 상환 · 2025말 차입금 없음",
  sources=["D_KRSH_AR2025"])
KS = "D_KRSH_AR2025"
for sid, sh, pct, cls in [("brookfield_apac_dc", 4212644, "64.62%", "보통주 · 지배기업"),
                          ("ibk_bank", 1335861, "20.49%", "보통주 · 유의적 영향력"),
                          ("dcn_partners", 457310, "7.01%", "보통주"), ("koramco_trust", 344000, "5.28%", "1종 종류주(7% 누적우선)"),
                          ("nh_bank", 125000, "1.92%", "2종 종류주(5.5% 누적우선)"), ("koramco_am", 44529, "0.68%", "보통주")]:
    R(f"ks_eq_{sid}", sid, "koramco_siheung_pfv", "EQUITY_INVESTMENT", "koramco_siheung_dc", stage="equity",
      amt=round(sh * 5000 / 1e8, 1), amt_type="equity_par_value", as_of="2025-12-31", status="funded", sources=[KS],
      role=f"{cls} {sh:,}주 ({pct})", quote=f"{sh:,}주 {pct}",
      note="금액은 액면(5,000원) 기준 자본금 — 주식발행초과금 포함 실제 납입액은 주주별 미공개")
R("ks_amc", "koramco_am", "koramco_siheung_pfv", "ASSET_MANAGER", "koramco_siheung_dc", status="operating", sources=[KS],
  quote="㈜코람코자산운용과 자산관리업무위탁계약")
R("ks_trust", "koramco_trust", "koramco_siheung_pfv", "TRUST_SERVICES", "koramco_siheung_dc", status="operating", sources=[KS],
  quote="㈜코람코자산신탁과 자금관리대리사무계약")
for lid, amt in [("nh_bank", 50), ("suhyup_bank", 100)]:
    R(f"ks_old_{lid}", lid, "koramco_siheung_pfv", "PROJECT_LOAN", "koramco_siheung_dc", stage="bridge", amt=amt,
      amt_type="historical_outstanding", as_of="2024-12-31", rate="6.00%", maturity="2025-10-31", status="repaid",
      sources=[KS], quote=f"전기말 장기차입금 {amt*100:,.0f}백만원 → 당기말 -", note="2025 중 전액 상환")
ISSUE("koramco_siheung_dc", "자료 상충",
      "감사보고서 차입금 표는 NH농협은행 50억·SH수협은행 100억, 약정 주석은 '고양축산업협동조합 등과 150억 대출약정'으로 기재 — "
      "대주 명칭 불일치. 상환 완료된 과거 관계로만 표시.")
ISSUE("koramco_siheung_dc", "프로젝트 식별", "기존 연구 대기열의 '안산 코람코·DCI' 클러스터. 캄스퀘어 안산(성곡동 670-4)과 다른 필지 — 병합 금지.")


# ════════════════════════════════════════════════════════════════════
# 7. 가산 STT Seoul 1 (가산동 345-26, 가산랜드마크데이터센터PFV) — gasan_stt_seoul1 (신규 연결)
# ════════════════════════════════════════════════════════════════════
S("D_GLM_AR2025", "공시", "가산랜드마크데이터센터피에프브이 감사보고서 (2025.12, 9개월)", "DART", "2026-04-06",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260406003009", rcept_no="20260406003009",
  section="주석 1(주주), 4(도급), 5(차입금), 7(특수관계자), 13(대출약정·Master Lease)")
E("gasan_landmark_pfv", "가산랜드마크데이터센터피에프브이", "spv", "project_finance", "Gasan Landmark Data Center PFV",
  note="가산동 345-26 구조고도화사업 IDC · dc.namepf 'STT Seoul 1'과 주소 일치")
E("fund_samsung_sra85", "삼성SRA일반사모부동산투자신탁제85호", "fund", "kr_am", note="운용 삼성SRA자산운용 · 신탁업자 KB증권")
E("fund_koramco130", "코람코일반사모투자신탁제130호", "fund", "kr_am", note="운용 코람코자산운용 · 신탁업자 농협은행")
E("samsung_sra_am", "삼성SRA자산운용", "asset_manager", "kr_am", "Samsung SRA Asset Management")
E("savills_korea", "세빌스코리아", "company", "kr_am", "Savills Korea")
E("im_bank", "iM뱅크", "bank", "kr_bank")
P("gasan_stt_seoul1", name_ko="가산 STT Seoul 1 데이터센터", address="서울특별시 금천구 가산동 345-26 (가산디지털2로 54)",
  borrower="gasan_landmark_pfv", dc_class="colocation", stage="운영 중 (2025 준공, 100% 책임임차 20+20년)",
  financing_summary="2025 리파이낸싱 대출약정 2,300억(A-1 2,000 · A-2 300) / 2025말 실행 2,000억. 종전 대주(DB손보·한화생명·농협은행) 1,275억 상환",
  sources=["D_GLM_AR2025"], permit_match="kr_permit_1019100086399")
G = "D_GLM_AR2025"; AS = "2025-12-31"
for sid, sh, pct, role, path in [
    ("fund_samsung_sra85", 1820833, "68.96%", "보통주·2종 (지배기업 · 신탁업자 KB증권 명의)", "삼성SRA 85호 펀드(신탁업자 KB증권) → PFV"),
    ("nh_inv_sec", 283333, "10.73%", "보통주·2종 (이사 1인 지명권)", None),
    ("savills_korea", 10000, "0.38%", "1종 종류주 · 자산관리회사", None),
    ("fund_koramco130", 526315, "19.93%", "3종 상환전환형 종류주 (신탁업자 농협은행 명의)", "코람코 130호 펀드(신탁업자 농협은행) → PFV")]:
    R(f"glm_eq_{sid}", sid, "gasan_landmark_pfv", "EQUITY_INVESTMENT", "gasan_stt_seoul1", stage="equity",
      amt=None, amt_type="equity_paid_in", as_of=AS, status="funded", sources=[G], role=f"{sh:,}주 {pct} · {role}",
      path=path, quote=f"{sh:,}주 {pct}", note="납입자본금 132억 — 주주별 실제 납입액 미공개")
R("glm_mgr_ssra", "samsung_sra_am", "fund_samsung_sra85", "ASSET_MANAGER", "gasan_stt_seoul1", status="operating", sources=[G],
  quote="집합투자업자인 삼성에스알에이자산운용 주식회사가 모집하기로 한 납입자본")
R("glm_trustee_kb", "kb_sec", "fund_samsung_sra85", "TRUST_SERVICES", "gasan_stt_seoul1", status="operating", sources=[G],
  quote="케이비증권(주) — 삼성SRA일반사모부동산투자신탁제85호의 신탁업자 지위", note="신탁업자 명의 보유 — KB증권 자기 익스포저 아님")
R("glm_trustee_nh", "nh_bank", "fund_koramco130", "TRUST_SERVICES", "gasan_stt_seoul1", status="operating", sources=[G],
  quote="농협은행(주) — 코람코일반사모투자신탁제130호의 신탁업자 지위", note="신탁업자 명의 — 농협은행 자기 익스포저 아님")
R("glm_mgr_koramco130", "koramco_am", "fund_koramco130", "ASSET_MANAGER", "gasan_stt_seoul1", status="operating", sources=[G],
  quote="코람코일반사모투자신탁제130호 · ㈜코람코자산운용(이사 지명권)")
for lid, commit, drawn, tr, rate in [("kdb", 1000, 1000, "A-1", "3.68%"), ("im_bank", 300, 300, "A-1", "3.85%"),
                                     ("kb_bank", 200, 200, "A-1", "3.95%"), ("bnk_kyongnam", 200, 200, "A-1", "3.85%"),
                                     ("hana_bank", 200, 200, "A-1", "3.95%"), ("suhyup_bank", 100, 100, "A-1", "3.95%"),
                                     ("kb_bank", 300, None, "A-2", None)]:
    R(f"glm_refi_{lid}_{tr}", lid, "gasan_landmark_pfv", "PROJECT_LOAN", "gasan_stt_seoul1", stage="refinancing",
      amt=commit, amt_type="institution_commitment", drawn=drawn, as_of=AS, seniority=f"선순위(Tr.{tr})", rate=rate,
      status="funded" if drawn else "committed", sources=[G],
      quote=f"Tranche {tr} 대출약정액 {commit*100:,.0f}백만원" + (f" · 장기차입금 {drawn*100:,.0f}백만원" if drawn else " · 미인출"))
R("glm_arr_kdb", "kdb", "gasan_landmark_pfv", "ARRANGER", "gasan_stt_seoul1", stage="refinancing", amt=8.1, amt_type="fee_paid",
  status="committed", sources=[G], quote="한국산업은행 금융주선수수료 600백만원 · 금융자문수수료 210백만원")
R("glm_arr_kb", "kb_bank", "gasan_landmark_pfv", "ARRANGER", "gasan_stt_seoul1", stage="refinancing", amt=4.5, amt_type="fee_paid",
  status="committed", sources=[G], quote="(주)국민은행 담보대출 금융주선수수료 450백만원")
for lid, bal in [("db_ins", 576.79), ("hanwha_life", 576.79), ("nh_bank", 121.43)]:
    R(f"glm_old_{lid}", lid, "gasan_landmark_pfv", "PROJECT_LOAN", "gasan_stt_seoul1", stage="main_pf", amt=bal,
      amt_type="historical_outstanding", as_of="2025-03-31", status="repaid", sources=[G],
      quote=f"전기말(2025.3) 단기+장기 차입금 {bal:,.2f}억", note="2025 리파이낸싱으로 상환")
R("glm_epc_dl", "dl_enc", "gasan_landmark_pfv", "EPC_CONTRACT", "gasan_stt_seoul1", stage="construction", amt=1336.68,
  amt_type="construction_contract_value", status="operating", sources=[G],
  quote="디엘이앤씨(주)와 체결한 133,668백만원 상당의 신축공사 도급계약 … 수급인은 2023년 9월 15일부로 (주)포스코이앤씨에서 디엘이앤씨(주)로 변경")
R("glm_epc_posco_hist", "posco_enc", "gasan_landmark_pfv", "EPC_CONTRACT", "gasan_stt_seoul1", stage="construction",
  status="terminated", sources=[G], quote="수급인은 2023년 9월 15일부로 (주)포스코이앤씨에서 디엘이앤씨(주)로 변경", note="과거 시공사(2023-09 교체)")
R("glm_amc_savills", "savills_korea", "gasan_landmark_pfv", "ASSET_MANAGER", "gasan_stt_seoul1", status="operating", sources=[G],
  quote="세빌스코리아 주식회사와 … 자산관리업무위탁계약")
R("glm_trust_koramco", "koramco_trust", "gasan_landmark_pfv", "TRUST_SERVICES", "gasan_stt_seoul1", status="operating", sources=[G],
  quote="(주)코람코자산신탁과 부동산 담보신탁계약 · 자금관리사무")
ISSUE("gasan_stt_seoul1", "미확인", "100% 책임임차(Master Lease, 20+20년, Triple Net) 임차인 명칭이 감사보고서에 없음. "
      "STT GDC(효성 합작) 추정은 공시로 미확인 — 임차 관계 미등록.")

# ════════════════════════════════════════════════════════════════════
# 8. 부산 에코델타시티 데이터센터 (강서구 명지동 산업20·22-4블록) — busan_ecodelta_dc (신규)
# ════════════════════════════════════════════════════════════════════
S("D_BEDG_AR2025", "공시", "부산에코델타그린데이터센터피에프브이 감사보고서 (2025.12)", "DART", "2026-04-10",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260410003722", rcept_no="20260410003722")
E("busan_ecodelta_pfv", "부산에코델타그린데이터센터피에프브이", "spv", "project_finance", "Busan Eco Delta Green DC PFV")
E("daesungmun", "대성문", "company", "kr_operator", "Daesungmun", note="PFV 지배기업 · 시행 AMC")
E("busan_ilbo", "부산일보", "company", "kr_operator")
E("metheus_am", "메테우스자산운용", "asset_manager", "kr_am")
E("ibk_capital", "IBK캐피탈", "nbFI", "kr_bank")
P("busan_ecodelta_dc", name_ko="부산 에코델타시티 데이터센터", address="부산광역시 강서구 명지동 에코델타시티 산업20·산업22-4 블록",
  borrower="busan_ecodelta_pfv", dc_class="general_dc", stage="토지 매입 단계 (본PF 전)",
  financing_summary="토지 중도금 대출 IBK캐피탈 202억 (2024 NH투자증권 약정 → 2025 IBK캐피탈) · 연면적 100,090㎡ 7개동",
  sources=["D_BEDG_AR2025"])
BE = "D_BEDG_AR2025"
for sid, sh, role in [("daesungmun", 1390000, "보통 985,282 + 1종 193,422 + 2종 211,296 · 지배기업"),
                      ("busan_ilbo", 525000, "보통주"), ("ibk_sec", 335000, "보통 205,426 + 1종 129,574"),
                      ("ibk_bank", 200000, "1종 종류주"), ("metheus_am", 50000, "1종 종류주 · 자산관리")]:
    R(f"bed_eq_{sid}", sid, "busan_ecodelta_pfv", "EQUITY_INVESTMENT", "busan_ecodelta_dc", stage="equity",
      amt=round(sh * 5000 / 1e8, 2), amt_type="equity_par_value", as_of="2025-12-31", status="funded", sources=[BE],
      role=role, quote=f"주주현황 {sh:,}주 (액면 5,000원)")
R("bed_loan_ibkcap", "ibk_capital", "busan_ecodelta_pfv", "PROJECT_LOAN", "busan_ecodelta_dc", stage="bridge", amt=202.14,
  amt_type="institution_commitment", drawn=202.14, as_of="2025-12-31", rate="4.42%~5.20%", maturity="2027", status="funded",
  sources=[BE], seniority="토지대금 반환채권 신탁 1종 수익권",
  quote="기업자금대출 (주)IBK캐피탈 약정한도 20,213,728,000 · 실행 20,213,728,000")
R("bed_loan_nhis_hist", "nh_inv_sec", "busan_ecodelta_pfv", "PROJECT_LOAN", "busan_ecodelta_dc", stage="bridge", amt=202.14,
  amt_type="historical_commitment", drawn=101.07, as_of="2024-12-31", status="repaid", sources=[BE],
  quote="전기말 엔에이치투자증권 기업자금대출 약정 20,213,728,000 · 실행 10,106,864,000",
  note="2025말 대주는 IBK캐피탈 — 대출 양도/대환 여부 미기재")
R("bed_trust_nhis", "nh_inv_sec", "busan_ecodelta_pfv", "TRUST_SERVICES", "busan_ecodelta_dc", status="operating", sources=[BE],
  quote="토지매매대금 반환채권에 대하여 엔에이치투자증권(주)를 수탁자로 하여 신탁(양도)")
R("bed_trust_woori", "woori_asset_trust", "busan_ecodelta_pfv", "TRUST_SERVICES", "busan_ecodelta_dc", status="operating",
  sources=[BE], quote="우리자산신탁 주식회사와 자금의 관리에 관한 위탁계약")

# ════════════════════════════════════════════════════════════════════
# 9. 인천 원창동 데이터센터 (서구 원창동 381-73, 청라아이디씨PFV) — incheon_wonchang_dc
# ════════════════════════════════════════════════════════════════════
S("D_CNIDC_AR2025", "공시", "청라아이디씨피에프브이 감사보고서 (2025.12)", "DART", "2026-04-13",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260413000174", rcept_no="20260413000174",
  section="주석 1(주주), 8(담보), 11(단기차입금), 21(특수관계자·보증)")
E("j2tech", "제이투테크", "company", "kr_operator"); E("hc_corp", "에이치씨", "company", "kr_operator")
E("ewha_am", "이화자산운용", "asset_manager", "kr_am"); E("mugunghwa_trust", "무궁화신탁", "trust_company", "kr_trust")
E("ido_capital_am", "이도캐피탈자산운용", "asset_manager", "kr_am")
E("wonchang_idc", "원창아이디씨", "company", "kr_operator", note="브릿지 대주(11%) — 성격 미확인")
E("gps23_spc", "쥐피에스23제일차", "spv", "project_finance", note="브릿지 유동화 SPC · 신용보강 제공자 미확인")
E("seoul_livestock_mg", "서울축산새마을금고", "cooperative", "kr_cooperative",
  note="개별 새마을금고 (새마을금고중앙회와 별개 법인)")
E("kiwoom_fni", "키움에프앤아이", "nbFI", "kr_bank")
E("ido_club_d", "이도클럽디대구·해운대·거창", "company", "kr_operator", note="이도 계열 — 추가 담보 제공")
P("incheon_wonchang_dc", name_ko="인천 원창동 데이터센터 (청라 IDC)", address="인천광역시 서구 원창동 381-73 일원",
  borrower="cheongna_idc_pfv", dc_class="hyperscale_dev", stage="브릿지 단계 (본PF 전)",
  financing_summary="2025말 브릿지 900억(원창아이디씨 100·쥐피에스23제일차 310·신한캐피탈 290·신한투자증권 200·이도 후순위 50) + 이도 주주차입 232억",
  sources=["D_CNIDC_AR2025"], permit_match="kr_permit_1000000000000000351547")
CN = "D_CNIDC_AR2025"; AS = "2025-12-31"
for sid, sh, pct, cls in [("j2tech", 430000, "43%", "보통주"), ("ido", 230000, "23%", "보통 210,000 + 2종 20,000"),
                          ("hc_corp", 200000, "20%", "보통주"), ("ewha_am", 10000, "1%", "보통주"),
                          ("mugunghwa_trust", 50000, "5%", "1종 종류주"), ("ido_capital_am", 80000, "8%", "2종 종류주")]:
    R(f"cn_eq_{sid}", sid, "cheongna_idc_pfv", "EQUITY_INVESTMENT", "incheon_wonchang_dc", stage="equity",
      amt=round(sh * 5000 / 1e8, 1), amt_type="equity_par_value", as_of=AS, status="funded", sources=[CN],
      role=f"{cls} ({pct})", quote=f"{sh:,}주 {pct}")
for lid, amt, rate, sen in [("wonchang_idc", 100, "11.00%", "선순위"), ("gps23_spc", 310, "11.00%", "선순위(일부 후순위 전환)"),
                            ("shinhan_capital", 290, "11.20%", "선순위"), ("shinhan_sec", 200, "11.50%", "선순위"),
                            ("ido", 50, "11.70%", "후순위(2025 전환)")]:
    R(f"cn_bridge_{lid}", lid, "cheongna_idc_pfv", "PROJECT_LOAN", "incheon_wonchang_dc", stage="bridge", amt=amt,
      amt_type="outstanding", as_of=AS, rate=rate, seniority=sen, status="funded", sources=[CN],
      quote=f"브릿지론 {amt*100:,.0f}백만원 · {rate}")
R("cn_shloan_ido", "ido", "cheongna_idc_pfv", "SHAREHOLDER_LOAN", "incheon_wonchang_dc", stage="bridge", amt=232.4,
  amt_type="outstanding", as_of=AS, rate="4.60%", status="funded", sources=[CN], quote="주주차입금 ㈜이도 4.60% 23,239,604천원")
R("cn_guar_ido", "ido", "cheongna_idc_pfv", "LOAN_GUARANTEE", "incheon_wonchang_dc", stage="bridge", status="committed",
  contingent=True, sources=[CN], trigger="PFV 브릿지 이자 미지급 시 (원금 보증 아님)",
  quote="차입금에 대한 이자지급과 … 주주인 ㈜이도로부터 연대보증을 제공받고 있습니다")
R("cn_coll_idoclub", "ido_club_d", "cheongna_idc_pfv", "COLLATERAL_PROVIDED", "incheon_wonchang_dc", stage="bridge",
  amt=1170, amt_type="collateral_limit", status="committed", contingent=True, sources=[CN],
  quote="이도클럽디대구㈜ 이도클럽디해운대㈜ 이도클럽디거창㈜ 토지·건물 담보설정 533억(서울축산새마을금고·쥐피에스23제일차)·377억(신한캐피탈)·260억(신한투자증권)")
R("cn_pb_seoullivestock", "seoul_livestock_mg", "cheongna_idc_pfv", "PRIORITY_BENEFICIARY", "incheon_wonchang_dc",
  stage="bridge", status="funded", direct=False, sources=[CN], amt=None, amt_type="collateral_limit",
  path="서울축산새마을금고 → (쥐피에스23제일차 경유 추정) → PFV",
  quote="담보권자 서울축산새마을금고 키움에프앤아이㈜ 신한캐피탈㈜ 신한투자증권㈜ ㈜이도",
  note="차입금 표에 직접 대주로 없음 — 유동화 SPC 투자자 또는 공동담보권자로 보임 (경로 미확정)")
R("cn_pb_kiwoomfni", "kiwoom_fni", "cheongna_idc_pfv", "PRIORITY_BENEFICIARY", "incheon_wonchang_dc", stage="bridge",
  status="funded", direct=False, sources=[CN], quote="담보권자 … 키움에프앤아이㈜", note="차입금 표에 직접 대주 아님 — 경로 미확정")
R("cn_trust_mgh", "mugunghwa_trust", "cheongna_idc_pfv", "TRUST_SERVICES", "incheon_wonchang_dc", status="operating",
  sources=[CN], quote="당사의 용지는 주식회사 무궁화신탁에 신탁")
ISSUE("incheon_wonchang_dc", "미확인", "연구 대기열의 '신한은행·현대엔지니어링' 참여는 감사보고서에서 확인되지 않음 — 미등록.")

# 검토 후 제외 (DC 아님)
ISSUE(None, "제외", "천안제이디씨피에프브이: 감사보고서상 천안테크노파크 '물류센터' 개발사업, 2024-03 용지계약 해제·조기청산 예정 → 데이터센터 아님, 미등록.")


# ════════════════════════════════════════════════════════════════════
# 10. 부천 삼정동 13-15 데이터센터 (퍼시픽피치PFV) — bucheon_peach_dc (기존 인허가 'PEACH PFV DATA CENTER')
# ════════════════════════════════════════════════════════════════════
S("D_PEACH_AR2025", "공시", "퍼시픽피치피에프브이 감사보고서 (2025.12)", "DART", "2026-04-01",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260401001191", rcept_no="20260401001191",
  section="주석 1(사업개요), 5(차입금·약정), 10(주주), 11(약정), 12(담보), 14(특수관계자)")
E("peach_pfv", "퍼시픽피치피에프브이", "spv", "project_finance", "Pacific Peach PFV", note="부천 삼정동 13-15 데이터센터 개발 시행사")
E("mir_planning", "미르플래닝", "company", "kr_operator"); E("mir_invest", "미르인베스트먼트", "company", "kr_operator")
E("mir_dnd", "미르디앤디", "company", "kr_operator"); E("fine_partners", "화인파트너스", "company", "kr_operator")
E("bucheon_space1_spc", "부천공간제일차", "spv", "project_finance", note="B종 종류주 보유 SPC — 실질 투자자 미공개")
E("fund_shinhan_one_flagship1", "신한One플래그쉽부동산개발1호일반사모투자신탁", "fund", "kr_am", note="신한자산운용 추정(펀드명) · 신탁업자 우리은행")
E("fund_pacific43_2", "퍼시픽전문투자형사모부동산투자신탁제43-2호", "fund", "kr_am", note="퍼시픽자산운용 운용(펀드명) · 신탁업자 신한은행")
E("heungkuk_fire", "흥국화재", "insurer", "kr_insurance", "Heungkuk Fire & Marine")
E("bc_card", "비씨카드", "nbFI", "kr_bank", "BC Card")
E("jb_woori_capital", "JB우리캐피탈", "nbFI", "kr_bank", "JB Woori Capital")
E("shinhan_asset_trust", "신한자산신탁", "trust_company", "kr_trust")
P("bucheon_peach_dc", name_ko="부천 삼정동(13-15) 데이터센터 — 퍼시픽피치", address="경기도 부천시 오정구 삼정동 13-15",
  borrower="peach_pfv", dc_class="ai_ready_hyperscale", stage="공사 중 (연면적 76,429㎡ · 지하4~지상6층)",
  financing_summary="본PF 약정 5,900억 (선순위A 5,250 · 후순위B 650) / 2025말 실행 3,047억 · 만기 2026-10-20",
  sources=["D_PEACH_AR2025"], permit_match="kr_permit_1097100076386")
PC = "D_PEACH_AR2025"; AS = "2025-12-31"
_PA = [("ibk_bank", 500, 258.3), ("hyundai_capital", 300, 155.0), ("hana_capital", 50, 25.8), ("db_ins", 400, 206.6),
       ("heungkuk_fire", 250, 129.1), ("kdb", 500, 258.3), ("kb_capital", 100, 51.7), ("bc_card", 100, 51.7),
       ("kyobo_life", 1500, 774.8), ("mg_federation", 1550, 800.7)]
for lid, c, d in _PA:
    R(f"pc_A_{lid}", lid, "peach_pfv", "PROJECT_LOAN", "bucheon_peach_dc", stage="main_pf", amt=c,
      amt_type="institution_commitment", drawn=d, as_of=AS, seniority="선순위(대출약정 A)", rate="7.40%",
      maturity="2026-10-20", status="funded", sources=[PC],
      note="교보생명 일반계정 750 + 특별계정 750 합계" if lid == "kyobo_life" else None,
      quote=f"대출약정 A 약정한도 {c*100:,.0f}백만원 · 당기말 {d*100:,.0f}백만원 · 7.40% · 만기 2026-10-20")
_PB2 = [("hyundai_capital", 150, 77.3), ("hana_capital", 50, 25.8), ("kb_capital", 50, 25.8), ("bc_card", 150, 77.3),
        ("shinhan_capital", 50, 25.8), ("jb_woori_capital", 100, 51.5), ("shinhan_sec", 100, 51.5)]
for lid, c, d in _PB2:
    R(f"pc_B_{lid}", lid, "peach_pfv", "PROJECT_LOAN", "bucheon_peach_dc", stage="main_pf", amt=c,
      amt_type="institution_commitment", drawn=d, as_of=AS, seniority="후순위(대출약정 B)", rate="9.50%",
      maturity="2026-10-20", status="funded", sources=[PC],
      quote=f"대출약정 B 약정한도 {c*100:,.0f}백만원 · 당기말 {d*100:,.0f}백만원 · 9.50%")
for sid, sh, pct, path in [
    ("fund_pacific43_2", 11200000, "35.00%", "퍼시픽 43-2호(신탁업자 신한은행) → PFV (2023 후순위대출 출자전환)"),
    ("bucheon_space1_spc", 5190000, "16.22%", None),
    ("fund_shinhan_one_flagship1", 5055424, "15.80%", "신한One플래그쉽1호(신탁업자 우리은행) → PFV"),
    ("fund_pinetree9", 7107925, "22.22%", "파인트리 9-1·9-2·9-3호(신탁업자 한국증권금융) → PFV"),
    ("shinhan_sec", 2209999, "6.91%", None), ("fine_partners", 606651, "1.90%", None),
    ("mir_planning", 280000, "0.88%", None), ("mir_invest", 140000, "0.44%", None), ("mir_dnd", 140000, "0.44%", None),
    ("pacific_am", 70001, "0.22%", None)]:
    R(f"pc_eq_{sid}", sid, "peach_pfv", "EQUITY_INVESTMENT", "bucheon_peach_dc", stage="equity",
      amt=round(sh * 5000 / 1e8, 1), amt_type="equity_par_value", as_of=AS, status="funded", sources=[PC],
      role=f"{sh:,}주 ({pct})", path=path, quote=f"주주 현황 합계 {sh:,}주 {pct}",
      note="액면 5,000원 기준 — 실제 납입가 미공개")
R("pc_amc_pacific", "pacific_am", "peach_pfv", "ASSET_MANAGER", "bucheon_peach_dc", status="operating", sources=[PC],
  amt=12, amt_type="fee_paid", as_of=AS, quote="주식회사 퍼시픽자산운용과 자산관리위탁계약 · 자산관리수수료 1,200,000천원")
R("pc_mgr_pac43", "pacific_am", "fund_pacific43_2", "ASSET_MANAGER", "bucheon_peach_dc", status="operating", sources=[PC],
  note="펀드명 기반 운용 관계")
R("pc_trust_shinhan", "shinhan_asset_trust", "peach_pfv", "TRUST_SERVICES", "bucheon_peach_dc", status="operating",
  sources=[PC], quote="신한자산신탁 주식회사와 자금관리사무위탁계약 · PF 계좌 신탁")
ISSUE("bucheon_peach_dc", "만기 도래", "본PF 만기 2026-10-20 (2025말 전액 유동성대체). 연장·리파이낸싱 여부 공시 미확인 — 현재 상태 미확인.")
ISSUE("bucheon_peach_dc", "미확인", "시공사·임차인이 감사보고서에 기재되지 않음. 정관 목적은 '물류센터 및 기타' 이나 사업개요는 '데이터센터 개발사업'.")
ISSUE("bucheon_peach_dc", "프로젝트 식별", "부천 삼정동 48-59(유진 디씨아이티와이부천PFV)와 13-15(퍼시픽피치PFV)는 별개 사업 — 병합 금지.")


# ════════════════════════════════════════════════════════════════════
# 11. 영등포 Y-eDC (영등포동2가 94-144, 엣지코어PFV) — yeongdeungpo_yedc
# ════════════════════════════════════════════════════════════════════
S("D_EDGE_AR2025", "공시", "엣지코어피에프브이 감사보고서 (2025.12)", "DART", "2026-04-03",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260403003710", rcept_no="20260403003710",
  section="주석 1(주주), 5(차입금·담보), 8(특수관계자), 13(약정)")
S("D_EDGE_PLEDGE_20250924", "공시", "엣지코어피에프브이 특수관계인으로부터받은담보 ((주)한화 주식 근질권)", "DART", "2025-09-24",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20250924000440", rcept_no="20250924000440")
S("D_EDGE_EPC_20250930", "공시", "엣지코어피에프브이 동일인등출자계열회사와의상품ㆍ용역거래 (건설공사 도급)", "DART", "2025-09-30",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20250930000490", rcept_no="20250930000490")
E("msedc1_spc", "엠에스이디씨제일차", "spv", "project_finance", note="Tr.A 대주 유동화 SPC — 신용보강 제공자 공시 미확인")
E("msedc2_spc", "엠에스이디씨제이차", "spv", "project_finance", note="Tr.B 대주 유동화 SPC (500억, 4.5%)")
E("kis_re_trust", "한국투자부동산신탁", "trust_company", "kr_trust")
E("hyundai_marine", "현대해상화재보험", "insurer", "kr_insurance", "Hyundai Marine & Fire")
E("gaon_haeje5_spc", "가온해제오차", "spv", "project_finance", note="2024말 단기차입 410억 대주(브릿지) — 2025 상환")
P("yeongdeungpo_yedc", name_ko="영등포 Y-eDC 데이터센터", address="서울특별시 영등포구 영등포동2가 94-144 일원",
  borrower="edgecore_pfv", dc_class="edge_ai_ready", stage="공사 중",
  financing_summary="본PF 약정 2,200억 (Tr.A 1,700 · Tr.B 500) / 2025말 실행 820억 · 만기 2029-09-30. 2024 브릿지 410억 상환",
  sources=["D_EDGE_AR2025"], permit_match="kr_permit_1000000000000000586260")
ED = "D_EDGE_AR2025"; AS = "2025-12-31"
for sid, sh, role in [("hanwha_corp", 900000, "보통주 90%"), ("mastern_am", 50000, "보통주 5% · 자산관리회사"),
                      ("kis_re_trust", 50000, "1종 우선주 5% · 자금관리")]:
    R(f"ed_eq_{sid}", sid, "edgecore_pfv", "EQUITY_INVESTMENT", "yeongdeungpo_yedc", stage="equity",
      amt=round(sh * 5000 / 1e8, 1), amt_type="equity_par_value", as_of=AS, status="funded", sources=[ED],
      role=role, quote=f"주주현황 {sh:,}주")
for lid, c, d, tr, rate in [("msedc1_spc", 200, 37, "A", "5.2%"), ("kb_ins", 1100, 207, "A", "5.2%"),
                            ("hyundai_marine", 400, 76, "A", "5.2%"), ("msedc2_spc", 500, 500, "B", "4.5%")]:
    R(f"ed_pf_{lid}", lid, "edgecore_pfv", "PROJECT_LOAN", "yeongdeungpo_yedc", stage="main_pf", amt=c,
      amt_type="institution_commitment", drawn=d, as_of=AS, seniority=f"Tr.{tr}", rate=rate, maturity="2029-09-30",
      status="funded", sources=[ED], quote=f"Tr.{tr} {c*100:,.0f}백만원 약정 · 실행 {d*100:,.0f}백만원")
for lid, c in [("kb_ins", 300), ("shinhan_capital", 200)]:
    R(f"ed_pb2_{lid}", lid, "edgecore_pfv", "PRIORITY_BENEFICIARY", "yeongdeungpo_yedc", stage="main_pf", amt=c,
      amt_type="institution_commitment", as_of=AS, seniority="공동 2순위 우선수익권", status="funded", direct=False,
      path=f"{'KB손해보험' if lid=='kb_ins' else '신한캐피탈'} → 엠에스이디씨제이차(Tr.B 500억) → PFV (추정)", sources=[ED],
      quote=f"공동 2순위 우선수익권 — 차입약정한도 {c*100:,.0f}백만원",
      note="2순위 우선수익자 약정 합계(500억)가 Tr.B(엠에스이디씨제이차 500억)와 일치 — SPC 경유 투자로 추정")
R("ed_old_gaon", "gaon_haeje5_spc", "edgecore_pfv", "PROJECT_LOAN", "yeongdeungpo_yedc", stage="bridge", amt=410,
  amt_type="historical_outstanding", as_of="2024-12-31", status="repaid", sources=[ED],
  quote="단기차입금 가온해제오차 주식회사 전기말 41,000,000천원", note="본PF 전환 시 상환")
R("ed_pledge_hanwha", "hanwha_corp", "edgecore_pfv", "SHARE_PLEDGE", "yeongdeungpo_yedc", stage="main_pf", amt=2860,
  amt_type="pledge_limit", status="committed", contingent=True, sources=["D_EDGE_PLEDGE_20250924"],
  trigger="PF 기한이익상실 시 대주가 (주)한화 보유 PFV 주식 처분 — 원리금 보증 아님",
  quote="담보한도 286,000 (PF약정금액 2,200억원의 130%) · (주)한화가 보유한 엣지코어피에프브이(주) 주식 근질권")
R("ed_epc_hanwha", "hanwha_corp", "edgecore_pfv", "EPC_CONTRACT", "yeongdeungpo_yedc", stage="construction", amt=268.26,
  amt_type="construction_billing_period", as_of="2025-12-31", status="committed", sources=["D_EDGE_EPC_20250930"],
  quote="건설공사 도급계약 · 공사용역 · 신축공사 26,826 (2025년 4분기 거래예정)",
  note="분기 거래예정액이며 총 도급금액 아님. 2025 연간 매입 246.6억(감사보고서)")
R("ed_amc_mastern", "mastern_am", "edgecore_pfv", "ASSET_MANAGER", "yeongdeungpo_yedc", status="operating", sources=[ED],
  amt=19.8, amt_type="fee_paid", as_of=AS, quote="마스턴투자운용㈜과 자산관리위탁계약 · 지급수수료 1,980,000천원")
R("ed_trust_kisre", "kis_re_trust", "edgecore_pfv", "TRUST_SERVICES", "yeongdeungpo_yedc", status="operating", sources=[ED],
  quote="한국투자부동산신탁㈜과 자금관리사무위탁계약 · 부동산담보신탁")
ISSUE("yeongdeungpo_yedc", "자료 상충", "기존 데이터의 '하나증권 주선'(아시아경제 2024-11)은 2025 감사보고서에서 확인되지 않음 — 언론 보도로만 유지.")

# ════════════════════════════════════════════════════════════════════
# 12. 한화그룹 제2데이터센터 (안성 양성면 추곡리 179, 알이씨데이터센터) — anseong_rec_dc
# ════════════════════════════════════════════════════════════════════
S("D_REC_PLEDGE_20260730", "공시", "(주)알이씨데이터센터 특수관계인으로부터받은담보 (한화솔루션 주식 근질권)", "DART", "2026-07-30",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260730000054", rcept_no="20260730000054")
S("D_REC_EPC_20260930", "공시", "(주)알이씨데이터센터 동일인등출자계열회사와의상품ㆍ용역거래변경 (한화시스템 전기공사)", "DART",
  "2026-09-30", "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260930000069", rcept_no="20260930000069")
E("hanwha_systems", "한화시스템", "company", "kr_construction", "Hanwha Systems", listed=True)
P("anseong_rec_dc", name_ko="안성 한화그룹 제2데이터센터 (알이씨데이터센터)", address="경기도 안성시 양성면 추곡리 179",
  borrower="rec_datacenter", dc_class="corporate_group_dc", stage="공사 중 · PF 약정(2026-07-29)",
  financing_summary="PF 약정 1,500억 (우리은행·국민은행 등 대주단), 최초인출 후 27개월", sources=["D_REC_PLEDGE_20260730"],
  permit_match="kr_permit_1000000000000000767459")
RC = "D_REC_PLEDGE_20260730"
for lid in ["woori_bank", "kb_bank"]:
    R(f"rec_pf_{lid}", lid, "rec_datacenter", "PROJECT_LOAN", "anseong_rec_dc", stage="main_pf", amt=None,
      amt_type="institution_commitment", as_of="2026-07-29", status="committed", sources=[RC],
      quote="채권자 우리은행, 국민은행 등 대주단 · PF약정 금액(1,500억원)",
      note="대주단 일부만 공개('등') — 기관별 배분 미공개, 총액을 개별 대주에 배분하지 않음")
R("rec_pledge_hsol", "hanwha_solutions", "rec_datacenter", "SHARE_PLEDGE", "anseong_rec_dc", stage="main_pf", amt=1800,
  amt_type="pledge_limit", status="committed", contingent=True, sources=[RC],
  trigger="PF 기한이익상실 시 대주가 한화솔루션 출자 주식 처분 — 원리금 보증 아님",
  quote="한화솔루션 출자 보통주 190,000주 · 담보한도 180,000 (PF약정 1,500억원의 120%)")
R("rec_epc_hsys", "hanwha_systems", "rec_datacenter", "EPC_CONTRACT", "anseong_rec_dc", stage="construction",
  amt=None, amt_type="construction_contract_value", status="committed", sources=["D_REC_EPC_20260930"],
  quote="한화그룹 제2데이터센터 신축공사 중 전기공사 · 한화시스템(주) · 수의계약", note="총 계약금액 미공시(분기 거래예정 16억 → 감소)")
ISSUE("anseong_rec_dc", "분류", "한화그룹 자체 데이터센터 — 그룹 계열 시행법인의 PF(주식 근질권)로 조달. 외부 임차형 AIDC 여부 미확인.")
ISSUE("anseong_rec_dc", "미확인", "대주단 전체 명단·주관사·시공사(건축) 공시 미확인.")


# ════════════════════════════════════════════════════════════════════
# 7-b. 가산 STT Seoul 1 — 임차인 효성에스티티지디씨 (시설자금 대출)
# ════════════════════════════════════════════════════════════════════
S("D_HSTT_AR2025", "공시", "효성에스티티지디씨 감사보고서 (2025.12)", "DART", "2026-04-06",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260406002356", rcept_no="20260406002356",
  section="주석 1(주주), 8(차입금), 12(약정), 13(담보)")
E("hyosung_stt_gdc", "효성에스티티지디씨", "company", "kr_operator", "Hyosung STT GDC", aliases=["에브리쇼"],
  note="STT Korea DC 60% · 효성중공업 40% 합작 데이터센터 운영사")
E("stt_korea_dc", "STT Korea DC Pte. Ltd.", "company", "financial", "STT Korea DC", note="ST Telemedia Global Data Centres 계열(싱가포르)")
E("mizuho_bank", "미즈호은행", "bank", "financial", "Mizuho Bank")
E("ca_cib", "크레디아그리콜 CIB", "bank", "financial", "Crédit Agricole CIB")
E("ubob_seoul", "대화은행 서울지점", "bank", "financial", "UOB Seoul Branch")
E("kdb_capital", "산은캐피탈", "nbFI", "kr_bank", "KDB Capital")
HS = "D_HSTT_AR2025"
for sid, sh, pct in [("stt_korea_dc", 7254170, "60%"), ("hyosung_heavy", 4836113, "40%")]:
    R(f"hs_eq_{sid}", sid, "hyosung_stt_gdc", "EQUITY_INVESTMENT", "gasan_stt_seoul1", stage="equity", amt=None,
      amt_type="equity_paid_in", as_of="2025-12-31", status="funded", sources=[HS], role=f"보통주 {sh:,}주 ({pct})",
      quote=f"{sh:,}주 {pct}", note="자본금 604.5억 + 주식발행초과금 294억 — 주주별 납입액 미공개")
for lid, drawn, tr, spread in [("mizuho_bank", 151.62, "1", "3M CD+2.20%"), ("ca_cib", 151.62, "1", "3M CD+2.20%"),
                               ("ubob_seoul", 86.64, "1", "3M CD+2.20%"), ("kb_sec", 64.98, "2", "3M CD+2.85%"),
                               ("kdb_capital", 108.30, "2", "3M CD+2.85%"), ("ibk_capital", 86.64, "2", "3M CD+2.85%")]:
    R(f"hs_loan_{lid}", lid, "hyosung_stt_gdc", "CORPORATE_LOAN", "gasan_stt_seoul1", stage="main_pf", amt=None,
      amt_type="institution_commitment", drawn=drawn, as_of="2025-12-31", seniority=f"Tranche {tr}", rate=spread,
      maturity="2030-10-02", status="funded", sources=[HS],
      quote=f"Tranche {tr} {spread} 만기 2030-10-02 · 당기말 {drawn*100:,.0f}백만원",
      note="시설자금대출 한도 총 3,000억(미즈호 등) — 기관별 한도 미공개. 임차인(운영사) 대상 기업 대출이며 PFV 대출 아님")
R("hs_lease_glm", "hyosung_stt_gdc", "gasan_landmark_pfv", "TENANT_LEASE", "gasan_stt_seoul1", stage="operations",
  status="operating", sources=[G, HS], evidence="공시", direct=True,
  role="100% 책임임차(Master Lease) 20+20년 · Triple Net — 임차인·주주사 연대보증 (추정 매칭)",
  quote="(PFV) 100% 책임임차 · 임차인과 임차인의 주주사는 각각 책임임차에 대한 연대 보증 / (효성STT) 가산데이터센터 건설 목적 예금 · 리스자산 원가 자본화",
  note="두 감사보고서 모두 상대방 명칭을 직접 쓰지 않음 — 가산 소재·임차구조·주주사 보증 일치로 추정(INFERRED)")
for sid in ["stt_korea_dc", "hyosung_heavy"]:
    R(f"hs_leaseguar_{sid}", sid, "gasan_landmark_pfv", "LEASE_GUARANTEE", "gasan_stt_seoul1", stage="operations",
      status="operating", contingent=True, sources=[G], evidence="공시",
      trigger="임차인(효성STT GDC 추정)이 임대료 등 책임임차 의무 불이행 시",
      quote="임차인의 의무에 대하여 임차인과 임차인의 주주사는 각각 책임임차에 대한 연대 보증을 제공",
      note="주주사 명칭은 효성STT GDC 감사보고서 주주명부로 추정 (INFERRED)")

# ════════════════════════════════════════════════════════════════════
# 13. 가산 DCI SEL1 → 브룩필드·대림 (가산동 459-2, 가산디씨제이브이) — gasan_dci_sel1
# ════════════════════════════════════════════════════════════════════
S("D_GDJV_AR2025", "공시", "가산디씨제이브이 감사보고서 (2025.12)", "DART", "2026-04-06",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260406000434", rcept_no="20260406000434")
S("D_GDSL1_SALE_2021", "공시", "가산디씨에스엘원 비유동자산처분결정 (가산동 459-2 → 가산디씨제이브이)", "DART", "2021-12-29",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20211229000601", rcept_no="20211229000601")
E("gasan_dc_jv", "가산디씨제이브이", "company", "project_finance", "Gasan DC JV", note="데이터센터 개발·운영 법인 (브룩필드 65%·대림 35%)")
E("gasan_dc_sl1", "가산디씨에스엘원", "company", "project_finance", note="DL그룹 계열 · 2022 부지 매각 후 2025-09 해산")
E("daelim_corp", "대림", "holding", "kr_construction", "Daelim Corp (DL holding)")
E("bnp_paribas", "BNP파리바", "bank", "financial"); E("mufg", "MUFG은행", "bank", "financial")
E("ing_bank", "ING은행", "bank", "financial"); E("socgen", "소시에테제네랄", "bank", "financial")
E("ocbc", "OCBC은행", "bank", "financial"); E("natixis", "나티시스", "bank", "financial")
E("fund_kiamco_ind1", "KIAMCO산업단지환경개선사모투자신탁제1호", "fund", "kr_am", note="신탁업자 중소기업은행")
P("gasan_dci_sel1", name_ko="가산 DCI SEL1 데이터센터", address="서울특별시 금천구 가산동 459-2",
  borrower="gasan_dc_jv", dc_class="colocation", stage="운영 중 (2025 준공·코로케이션 개시)",
  financing_summary="2025 리파이낸싱 3,000억 (NH투자증권 1,350·크레디아그리콜 650·BNP 500·MUFG 500, CD+1.6%, 2030-11). 종전 외국계 은행단 1,750억 상환. "
                    "향후 운용리스 수취 예정액 3,919억",
  sources=["D_GDJV_AR2025"], permit_match="kr_permit_1019100080439")
GJ = "D_GDJV_AR2025"
for sid, sh, pct in [("brookfield_apac_dc", 6215625, "65%"), ("daelim_corp", 3346875, "35%")]:
    R(f"gj_eq_{sid}", sid, "gasan_dc_jv", "EQUITY_INVESTMENT", "gasan_dci_sel1", stage="equity",
      amt=None, amt_type="equity_paid_in", as_of="2025-12-31", status="funded", sources=[GJ],
      role=f"보통주 {sh:,}주 ({pct}) · 차입금 담보로 주식 전부 근질권", quote=f"{sh:,}주 {pct}",
      note="자본금 95.6억 + 주발초 352억 — 주주별 납입액 미공개")
for lid, amt in [("bnp_paribas", 500), ("mufg", 500), ("ca_cib", 650), ("nh_inv_sec", 1350)]:
    R(f"gj_loan_{lid}", lid, "gasan_dc_jv", "PROJECT_LOAN", "gasan_dci_sel1", stage="refinancing", amt=amt,
      amt_type="outstanding", as_of="2025-12-31", rate="CD91+1.6%", maturity="2030-11", status="funded", sources=[GJ],
      seniority="담보부(투자부동산·계좌·보험·주식 근질권)", quote=f"일반자금대출 {amt*100:,.0f}백만원 · CD91일물+1.6 · 30년 11월")
for lid, amt in [("ing_bank", 428.19), ("socgen", 428.19), ("ocbc", 428.19), ("fund_kiamco_ind1", 220.02), ("natixis", 245.08)]:
    R(f"gj_old_{lid}", lid, "gasan_dc_jv", "PROJECT_LOAN", "gasan_dci_sel1", stage="main_pf", amt=amt,
      amt_type="historical_outstanding", as_of="2024-12-31", status="repaid", sources=[GJ],
      quote=f"전기말 {amt*100:,.0f}백만원 → 당기말 -", note="2025 리파이낸싱으로 상환")
R("gj_land_sl1", "gasan_dc_sl1", "gasan_dc_jv", "ASSET_SALE", "gasan_dci_sel1", amt=566, amt_type="asset_sale_price",
  as_of="2022-01-06", status="terminated", sources=["D_GDSL1_SALE_2021"],
  quote="처분 목적물 가산동 459-2 대지 3,530㎡ · 처분가액 56,600,000,000 · 거래상대방 가산디씨제이브이")
R("gj_sl1_parent", "daelim_corp", "gasan_dc_sl1", "PARENT_AFFILIATE", "gasan_dci_sel1", status="terminated",
  sources=["D_GDSL1_SALE_2021"], quote="기업집단명 DL · 가산디씨에스엘원 (2025-09-25 해산 결의)")
ISSUE("gasan_dci_sel1", "미확인", "코로케이션 임차인(운용리스 3,919억) 명칭 공시 미기재.")

# ════════════════════════════════════════════════════════════════════
# 14. 군산 비응도 데이터센터 (OCI·SGC) — gunsan_sgc_dc (신규)
# ════════════════════════════════════════════════════════════════════
S("D_SGCAI_SALE_20260929", "공시", "에스지씨에이아이인프라 비유동자산처분결정 (군산 비응도동 토지)", "DART", "2026-09-29",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260929000640", rcept_no="20260929000640")
S("D_SGCAI_EPC_20260819", "공시", "에스지씨에이아이인프라 동일인등출자계열회사와의상품ㆍ용역거래 (데이터센터 60MW 부지조성)", "DART",
  "2026-08-19", "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260819000321", rcept_no="20260819000321")
E("sgc_ai_infra", "에스지씨에이아이인프라", "company", "kr_operator", "SGC AI Infra", note="OCI 기업집단 계열")
E("sgc_enc", "SGC이앤씨", "company", "kr_construction", listed=True)
E("fund_sgc_kis1", "에스지씨한국투자제1호사모투자합자회사", "fund", "kr_am", note="PEF — 업무집행사원 공시 미확인")
P("gunsan_sgc_dc", name_ko="군산 비응도 데이터센터 (SGC, 60MW)", address="전북특별자치도 군산시 비응도동 36-33",
  borrower="sgc_ai_infra", dc_class="ai_dedicated", stage="부지조성 (토지 PEF 매각·리스백 구조 추정)",
  financing_summary="토지 98.7억 PEF 매각(2026-09) · 부지조성·가설공사 35억 (SGC이앤씨)", sources=["D_SGCAI_SALE_20260929"],
  permit_match="kr_permit_1000000000000001015792")
R("sgc_land_pef", "sgc_ai_infra", "fund_sgc_kis1", "ASSET_SALE", "gunsan_sgc_dc", amt=98.7, amt_type="asset_sale_price",
  as_of="2026-09-29", status="committed", sources=["D_SGCAI_SALE_20260929"],
  quote="군산시 비응도동 36-33 토지 47,000㎡ 처분가액 9,870,000,000 · 거래상대방 에스지씨한국투자제1호사모투자 합자회사")
R("sgc_epc", "sgc_enc", "sgc_ai_infra", "EPC_CONTRACT", "gunsan_sgc_dc", stage="construction", amt=35,
  amt_type="construction_billing_period", status="committed", sources=["D_SGCAI_EPC_20260819"],
  quote="데이터센터 60MW 부지조성 및 가설공사 · 에스지씨이앤씨(주) · 3,500 (2026년 3분기)")
ISSUE("gunsan_sgc_dc", "미확인", "PEF(에스지씨한국투자제1호) 출자자·GP, 본공사 금융조달 공시 미확인.")

# ════════════════════════════════════════════════════════════════════
# 15. GS 동해 AIDC (동해에이아이제3캠퍼스) — donghae_gs_aidc (신규)
# ════════════════════════════════════════════════════════════════════
S("D_GSAI_ACQ_20261019", "공시", "지에스에이아이인프라 비유동자산취득결정 (GS 동해시 AIDC 송변전공사)", "DART", "2026-10-19",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20261019000203", rcept_no="20261019000203")
S("D_GSAI_INV_20260929", "공시", "지에스에이아이인프라 특수관계인에대한출자 (동해에이아이제3캠퍼스)", "DART", "2026-09-29",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260929000055", rcept_no="20260929000055")
E("gs_ai_infra", "지에스에이아이인프라", "company", "kr_operator", "GS AI Infra", note="GS 기업집단 신설법인(2026)")
E("donghae_ai_campus3", "동해에이아이제3캠퍼스", "company", "project_finance", "Donghae AI 3rd Campus", note="지에스에이아이인프라 100% 자회사")
P("donghae_gs_aidc", name_ko="GS 동해 AIDC", address="강원특별자치도 동해시", borrower="donghae_ai_campus3",
  dc_class="ai_dedicated", stage="전력인프라 공사 계약 (2028 준공 예정)",
  financing_summary="송변전공사 2,479억 (GS건설, 자기자본 조달) · 동해에이아이제3캠퍼스 누적 출자 445억", sources=["D_GSAI_ACQ_20261019"])
R("gsai_epc_gsenc", "gs_enc", "gs_ai_infra", "EPC_CONTRACT", "donghae_gs_aidc", stage="construction", amt=2479.16,
  amt_type="construction_contract_value", as_of="2026-10-14", status="committed", sources=["D_GSAI_ACQ_20261019"],
  quote="GS 동해시 AIDC 송변전공사 · 취득가액 247,916,499,000 · 거래상대방 지에스건설 · 자본조달 자기자본",
  note="공사도급 가계약 기준 — 본계약 시 정정 예정")
R("gsai_eq_campus3", "gs_ai_infra", "donghae_ai_campus3", "EQUITY_INVESTMENT", "donghae_gs_aidc", stage="equity", amt=445,
  amt_type="equity_paid_in", as_of="2026-09-22", status="funded", sources=["D_GSAI_INV_20260929"],
  quote="(주)동해에이아이제3캠퍼스 보통주 출자금액 41,000 · 총출자액 44,500 (지분 100%)")
ISSUE("donghae_gs_aidc", "분류", "자기자본 조달 — PF 사업 아님. 임차인·외부 금융 미확인.")


# ════════════════════════════════════════════════════════════════════
# 16. 장성 파인데이터센터 (장성 남면 삼태리 412-17, 파인디씨PFV) — gwangju_fine_dc
# ════════════════════════════════════════════════════════════════════
S("D_DWEC_GUAR_FINE", "공시", "대우건설 타인에대한채무보증결정 (파인디씨피에프브이)", "DART/KIND", "2025-12-15",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20251215800003", rcept_no="20251215800003")
S("D_DWEC_EPC_FINE", "공시", "대우건설 단일판매ㆍ공급계약체결 (장성파인데이터센터 신축공사, 변경계약)", "DART/KIND", "2026-05-22",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260522800424", rcept_no="20260522800424")
S("N_BIZWATCH_FINE", "언론", "대우건설, 데이터센터 '개발 주체'로…전남 장성 첫 선", "비즈니스워치", "2025-12-16",
  "https://news.bizwatch.co.kr/article/real_estate/2025/12/16/0033")
P("gwangju_fine_dc", name_ko="장성 파인데이터센터", address="전라남도 장성군 남면 삼태리 412-17 일원 (광주연구개발특구 첨단3지구)",
  borrower="fine_dc_pfv", dc_class="ai_ready", stage="공사 중 (2027-12 준공 예정, 수전 26MW / IT 16.7MW)",
  financing_summary="PF 2,959억 (Tr.A 1,959 · B 500 · C 500; 하나은행·KB국민은행 등) · 총사업비 3,959억 · 대우건설 책임준공 미이행 시 채무인수",
  sources=["D_DWEC_GUAR_FINE", "D_DWEC_EPC_FINE"], permit_match="kr_permit_1000000000000000563731")
R("fine_dwec_assume", "daewoo_enc", "fine_dc_pfv", "DEBT_ASSUMPTION", "gwangju_fine_dc", stage="main_pf", amt=2959,
  amt_type="guarantee_limit", status="committed", contingent=True, sources=["D_DWEC_GUAR_FINE"],
  trigger="대우건설 책임준공 미이행 시 PFV 대출채무 인수 (Tr.A·B 30개월, Tr.C 60개월)",
  quote="채권자 하나은행, KB은행 등 · 채무보증금액 295,900,000,000 · 책임준공 미이행시 채무인수",
  note="기존 엣지 pf_daewoo_fine_guar(언론)를 공시 근거로 대체")
R("fine_dwec_epc", "daewoo_enc", "fine_dc_pfv", "EPC_CONTRACT", "gwangju_fine_dc", stage="construction", amt=2525,
  amt_type="construction_contract_value", as_of="2026-05-21", status="committed", sources=["D_DWEC_EPC_FINE"],
  quote="장성파인데이터센터 신축공사 · 계약금액 252,500,000,000 (부가세 제외) · 2025-12-24~2027-12-23",
  note="최초 계약(2025-12-08)은 공시 기준 미달, 2026-05 변경계약으로 공시")
R("fine_dwec_eq", "daewoo_enc", "fine_dc_pfv", "EQUITY_INVESTMENT", "gwangju_fine_dc", stage="equity", amt=None,
  amt_type="equity_paid_in", status="funded", evidence="언론", sources=["N_BIZWATCH_FINE"], role="지분 약 5%",
  quote="대우건설 지분율은 5% 수준이다")
ISSUE("gwangju_fine_dc", "미확인", "파인디씨PFV 감사보고서 DART 미검색(외감 대상 전). 하나은행·KB국민은행 외 대주('등')와 기관별 금액 미공개.")

# ════════════════════════════════════════════════════════════════════
# 17. 용인 지곡 데이터센터 (기흥구 지곡동 236-6 외, 캄스퀘어용인PFV) — camsquare_yongin  (금액 정정)
# ════════════════════════════════════════════════════════════════════
S("N_DEALBOOK_YONGIN", "언론", "한대체, 6일 용인 지곡동 데이터센터부지 소유권 이전 클로징", "딜북뉴스", "2026-02-06",
  "https://www.dealbook.co.kr/handaece-6il-yongin-jigogdong-deiteosenteobuji-soyugweon-ijeon-keulrojing/comments")
P("camsquare_yongin", name_ko="용인 지곡 데이터센터 (캄스퀘어 용인)", address="경기도 용인시 기흥구 지곡동 236-6 외 2필지",
  borrower="camsquare_yongin_pfv", dc_class="hyperscale_dev", stage="토지 매입·브릿지 (수전 60MW)",
  financing_summary="브릿지 600억 (선순위 530 · 후순위 70, 대출기간 1년) — 한화투자증권 SPC 380(선순위)·SK증권 SPC 70(후순위), 선순위 잔여 150억 대주 미공개",
  sources=["N_DEALBOOK_YONGIN"])
E("hanwha_sec_spc_yongin", "한화투자증권 SPC(명칭 미공개)", "spv", "project_finance", note="용인 지곡 선순위 브릿지 380억 — SPC명 비공개")
E("sk_sec_spc_yongin", "SK증권 SPC(명칭 미공개)", "spv", "project_finance", note="용인 지곡 후순위 브릿지 70억 — SPC명 비공개")
R("cy_br_hanwha_spc", "hanwha_sec_spc_yongin", "camsquare_yongin_pfv", "PROJECT_LOAN", "camsquare_yongin", stage="bridge",
  amt=380, amt_type="institution_commitment", as_of="2026-02-06", seniority="선순위", status="funded", evidence="언론",
  sources=["N_DEALBOOK_YONGIN"], quote="선순위에는 한화투자증권 SPC가 380억원을")
R("cy_br_sk_spc", "sk_sec_spc_yongin", "camsquare_yongin_pfv", "PROJECT_LOAN", "camsquare_yongin", stage="bridge",
  amt=70, amt_type="institution_commitment", as_of="2026-02-06", seniority="후순위", status="funded", evidence="언론",
  sources=["N_DEALBOOK_YONGIN"], quote="후순위에는 SK증권 SPC가 70억원을 각각 참여했다")
R("cy_sponsor_hanwha", "hanwha_inv_sec", "hanwha_sec_spc_yongin", "ABS_SPONSOR", "camsquare_yongin", stage="bridge",
  status="funded", evidence="언론", sources=["N_DEALBOOK_YONGIN"], contingent=True, direct=False,
  path="한화투자증권 → (SPC 신용보강/매입약정 추정) → SPC → PFV", quote="한화투자증권 SPC",
  note="SPC 투자자·신용보강 조건 비공개 — 한화투자증권 보유 익스포저 규모 미확인")
R("cy_sponsor_sk", "sk_sec", "sk_sec_spc_yongin", "ABS_SPONSOR", "camsquare_yongin", stage="bridge", status="funded",
  evidence="언론", sources=["N_DEALBOOK_YONGIN"], contingent=True, direct=False,
  path="SK증권 → (SPC) → PFV", quote="SK증권 SPC", note="SPC 구조 비공개")
ISSUE("camsquare_yongin", "자료 상충",
      "기존 데이터(딜사이트)는 한화투자증권 530억·SK증권 70억 직접 대출로 표시. 딜북(2026-02-06)은 '한화투자증권 SPC 380억(선순위)·SK증권 SPC 70억(후순위)', "
      "선순위 총 530억 중 150억 대주 미공개 → 기존 직접대출 엣지는 SPC 경유 관계로 대체하고 '선순위 잔여 150억 대주 미공개'로 기록.")


# ════════════════════════════════════════════════════════════════════
# 18. 하남 풍산 데이터센터 (풍산동 607-2·607-3, 그린디지털인프라 — MKIF) — hanam_mkif_dc (신규 연결)
# ════════════════════════════════════════════════════════════════════
S("D_GDI_AR2025", "공시", "그린디지털인프라 감사보고서 (2025.12)", "DART · 삼일회계법인", "2026-04-02",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260402001874", rcept_no="20260402001874", section="주석 4(담보신탁), 7(차입금)")
S("O_MKIF_HANAM", "공식발표", "하남 데이터센터 (자산 소개)", "맥쿼리한국인프라투융자회사", "2026-10-21",
  "https://www.mkif.com/ko/assets/hanam-data-center.html")
E("green_digital_infra", "그린디지털인프라", "company", "project_finance", "Green Digital Infra", note="MKIF 100% 투자목적회사 · 하남 데이터센터 소유")
P("hanam_mkif_dc", name_ko="하남 풍산 데이터센터 (MKIF·LG CNS 임차)", address="경기도 하남시 풍산동 607-2, 607-3",
  borrower="green_digital_infra", dc_class="hyperscale_colocation", stage="운영 중 (2023-11 준공, 수전 40MW / IT 25.44MW)",
  financing_summary="인수금융 4,950억 (Tr.A 4,000 · Tr.B 950; 국민·교보생명·신한·현대해상·KB손보) + 신용공여 200 + MKIF 후순위 4,000 (8.5%)",
  sources=["D_GDI_AR2025", "O_MKIF_HANAM"], permit_match="kr_permit_1115100098904")
GD = "D_GDI_AR2025"; AS = "2025-12-31"
for lid, a, b in [("kb_bank", 800, 200), ("kyobo_life", 1500, 500), ("shinhan_bank", 1000, None),
                  ("hyundai_marine", 300, 150), ("kb_ins", 400, 100)]:
    R(f"gd_trA_{lid}", lid, "green_digital_infra", "ACQUISITION_LOAN", "hanam_mkif_dc", stage="refinancing", amt=a,
      amt_type="institution_commitment", drawn=a, as_of=AS, seniority="선순위 인수금융 Tr.A", rate="4.95%", status="funded",
      sources=[GD], quote=f"인수금융 Tr.A 약정액 {a*100:,.0f}백만원 · 당기말 {a*100:,.0f}백만원 · 4.95%")
    if b:
        R(f"gd_trB_{lid}", lid, "green_digital_infra", "ACQUISITION_LOAN", "hanam_mkif_dc", stage="refinancing", amt=b,
          amt_type="institution_commitment", drawn=b, as_of=AS, seniority="선순위 인수금융 Tr.B", rate="3.75%",
          status="funded", sources=[GD], quote=f"인수금융 Tr.B 약정액 {b*100:,.0f}백만원 · 당기말 {b*100:,.0f}백만원")
R("gd_rcf_kb", "kb_bank", "green_digital_infra", "REVOLVER", "hanam_mkif_dc", stage="refinancing", amt=200,
  amt_type="institution_commitment", drawn=0, as_of=AS, status="committed", sources=[GD],
  quote="단기차입금 신용공여대출 국민은행 약정액 20,000,000 · 당기말 -")
R("gd_sub_mkif", "mkif", "green_digital_infra", "SHAREHOLDER_LOAN", "hanam_mkif_dc", stage="equity", amt=4000,
  amt_type="outstanding", as_of=AS, rate="8.5%", seniority="후순위", status="funded", sources=[GD, "O_MKIF_HANAM"],
  quote="후순위차입금 맥쿼리한국인프라투융자회사 8.5% 400,000,000 / 후순위대출 4,000억원")
R("gd_eq_mkif", "mkif", "green_digital_infra", "EQUITY_INVESTMENT", "hanam_mkif_dc", stage="equity", amt=230,
  amt_type="equity_paid_in", status="funded", evidence="공식발표", sources=["O_MKIF_HANAM"], role="지분 100%",
  quote="MKIF는 그린디지털인프라(주)의 100% 주주 … 지분증권 230억원")
R("gd_lease_lgcns", "lg_cns", "green_digital_infra", "TENANT_LEASE", "hanam_mkif_dc", stage="operations",
  status="operating", evidence="공식발표", sources=["O_MKIF_HANAM"], role="건물 전체 임차 후 이용자와 데이터센터 이용계약",
  quote="본건 데이터센터의 임차인은 (주)엘지씨엔에스입니다. 임차인은 본건 데이터센터 전체에 관한 임대차계약을 체결")
R("gd_trust_kbre", "kb_re_trust", "green_digital_infra", "TRUST_SERVICES", "hanam_mkif_dc", status="operating", sources=[GD],
  quote="KB부동산신탁㈜와의 부동산담보신탁계약 상 우선수익권(대출약정금액의 120%)")
ISSUE("hanam_mkif_dc", "프로젝트 식별", "하남 풍산동에는 607-2(MKIF), 610(IBK 하남), 595(용도변경 AI DC), 하남엣지센터PFV(물류센터 전환) 등 복수 사업 — 주소별로 분리 유지.")

# ════════════════════════════════════════════════════════════════════
# 19. 용인 죽전 퍼시픽써니 데이터센터 — 언론·회사 발표 보강
# ════════════════════════════════════════════════════════════════════
S("O_HDEC_JUKJEON_2022", "공식발표", "국내 최대 규모 망중립 데이터센터 착공 (용인 죽전 퍼시픽써니)", "현대건설 뉴스룸", "2022-03-23",
  "https://www.hdec.kr/kr/newsroom/news_view.aspx?NewsSeq=516&NewsType=CULTURE&NewsListType=news_list")
P("yongin_jukjeon_pacific", name_ko="용인 죽전 퍼시픽써니 데이터센터", address="경기도 용인시 수지구 죽전동 1358 (대지로)",
  dc_class="hyperscale_colocation", stage="운영 중 (IT 64MW / 수전 100MW, LG CNS 운영)",
  financing_summary="퍼시픽자산운용이 CPP Investments·신한금융투자 등으로부터 8,280억 투자 유치(2022, 회사 발표). 대주단·SPC 감사보고서 미확인",
  sources=["O_HDEC_JUKJEON_2022"], permit_match="kr_permit_1116100375068")
ISSUE("yongin_jukjeon_pacific", "미확인", "시행 SPC 법인명 DART 미확인('퍼시픽써니관련시행SPC'는 기존 데이터의 가칭) — 8,280억의 지분/대출 구분·대주단 미공개.")


# ════════════════════════════════════════════════════════════════════
# 20. 부평 데이터센터 (청천동, Digital Edge SEL2/SEL3 — 디씨케이원) — bupyeong_digital_edge (신규 연결)
# ════════════════════════════════════════════════════════════════════
S("D_DCK1_AR2025", "공시", "디씨케이원 감사보고서 (2025.12)", "DART · 삼일회계법인", "2026-04-10",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260410002975", rcept_no="20260410002975", section="주석 1, 11(차입금), 담보")
S("D_DEK_AR2025", "공시", "디지털엣지코리아 감사보고서 (2025.12)", "DART · 삼일회계법인", "2026-04-10",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260410002982", rcept_no="20260410002982")
S("N_DEALSITE_BUPYEONG_2023", "언론", "'디벨로퍼 변신' SK에코, 부평 데이터센터PF 완료", "딜사이트", "2023-06-27",
  "https://dealsite.co.kr/articles/105937")
S("N_THEGURU_SEL3", "언론", "SK에코플랜트, 부평 데이터센터 2단계 사업비 8000억 조달 성공", "더구루", "2025-07-11",
  "https://www.theguru.co.kr/news/article.html?no=89250")
E("dck1", "디씨케이원", "company", "project_finance", "DCK One", note="Digital Edge (Developments) Pte. Ltd. 100% · 부평 청천동 데이터센터 시행·차주")
E("digital_edge_dev", "Digital Edge (Developments) Pte. Ltd.", "company", "financial", note="싱가포르 · 최상위 DEA TopCo LP")
E("fund_ssra_kr_pf2", "삼성SRA국내PF대출일반사모부동산투자신탁제2호", "fund", "kr_am", note="신탁업자 KB증권")
P("bupyeong_digital_edge", name_ko="부평 데이터센터 (Digital Edge SEL2·SEL3)", address="인천광역시 부평구 청천동 422 일원 (국가산업단지)",
  borrower="dck1", dc_class="hyperscale_colocation", stage="1단계 운영·2단계(Phase II-1) 공사",
  financing_summary="2025-06-30 PF 8,000억 (Tr.1 4,400 · Tr.2 1,600 · Tr.3 2,000, 만기 2029-07-14) / 2025말 실행 5,020억(장부금액 4,937억). 2023 PF 4,400억은 상환",
  sources=["D_DCK1_AR2025", "N_THEGURU_SEL3"], permit_match="kr_permit_1000000000000000803502")
DK = "D_DCK1_AR2025"; AS = "2025-12-31"
_DK = {  # lender: (Tr1, Tr2, Tr3, drawn_total)
    "ibk_bank": (1100, 400, 500, 1255), "kdb": (1100, 400, 500, 1255), "db_ins": (715, 260, 325, 816),
    "hyundai_marine": (275, 100, 125, 314), "kb_ins": (247.5, 90, 112.5, 282.5), "kb_bank": (192.5, 70, 87.5, 219.5),
    "ibk_capital": (137.5, 50, 62.5, 156.5), "ing_bank": (357.5, 130, 162.5, 407.5), "ca_cib": (275, 100, 125, 314)}
for lid, (t1, t2, t3, dr) in _DK.items():
    R(f"dk_pf_{lid}", lid, "dck1", "PROJECT_LOAN", "bupyeong_digital_edge", stage="refinancing", amt=t1 + t2 + t3,
      amt_type="institution_commitment", drawn=dr, as_of=AS, seniority="Tranche 1·2·3 (동순위 대주)",
      rate="5.20% (ING·CA-CIB: CD91+2.1%)", maturity="2029-07-14", status="funded", sources=[DK],
      quote=f"Tranche 1 {t1*100:,.0f} · Tranche 2 {t2*100:,.0f} · Tranche 3 {t3*100:,.0f} 백만원 약정 (2025-06-30 대출약정)",
      note="Tranche별 약정 합산치. 2025말 실행액은 Tr.1 전액 + Tr.2 일부")
for lid, amt, tr in [("tongyang_life", 730, "A"), ("db_ins", 730, "A"), ("fund_ssra_kr_pf2", 730, "A"),
                     ("ibk_bank", 1080, "B·C"), ("ing_bank", 650, "B·C"), ("ca_cib", 380, "B·C"), ("hyundai_marine", 100, "B")]:
    R(f"dk_old_{lid}", lid, "dck1", "PROJECT_LOAN", "bupyeong_digital_edge", stage="main_pf", amt=amt,
      amt_type="historical_commitment", as_of="2024-12-31", seniority=f"Tranche {tr}", maturity="2028-06-27",
      status="repaid", sources=[DK, "N_DEALSITE_BUPYEONG_2023"],
      quote=f"(2023 PF) Tranche {tr} 약정 {amt*100:,.0f}백만원 → 당기말 -",
      note="2023 1단계 PF(4,400억) — 2025 리파이낸싱으로 상환" + (" · KB증권은 삼성SRA국내PF대출 2호 신탁업자 명의" if lid == "fund_ssra_kr_pf2" else ""))
R("dk_trustee_kb", "kb_sec", "fund_ssra_kr_pf2", "TRUST_SERVICES", "bupyeong_digital_edge", status="repaid", sources=[DK],
  quote="케이비증권 주식회사는 삼성SRA국내PF대출일반사모부동산투자신탁제2호의 신탁자 지위")
R("dk_mgr_ssra", "samsung_sra_am", "fund_ssra_kr_pf2", "ASSET_MANAGER", "bupyeong_digital_edge", status="repaid", sources=[DK],
  note="펀드명 기반 운용 관계")
R("dk_eq_de", "digital_edge_dev", "dck1", "EQUITY_INVESTMENT", "bupyeong_digital_edge", stage="equity", amt=36.51,
  amt_type="equity_par_value", as_of=AS, status="funded", sources=[DK], role="100%",
  quote="보통주 자본금은 3,651백만원 … Digital Edge (Developments) Pte. Ltd.에서 100% 보유")
R("dk_jv_skep", "sk_ecoplant", "dck1", "EQUITY_INVESTMENT", "bupyeong_digital_edge", stage="equity", amt=None,
  amt_type="equity_paid_in", status="unknown", evidence="언론", sources=["N_DEALSITE_BUPYEONG_2023"], direct=False,
  path="SK에코플랜트 → (지분 경로 미공개) → 디씨케이원", role="공동개발 지분 49% (보도)",
  quote="SK에코플랜트와 디지털엣지의 지분율은 49대 51",
  note="디씨케이원 감사보고서상 직접 주주는 Digital Edge (Developments) 100% — SK에코플랜트 지분은 상위 지주/해외법인 경유로 추정, 경로 미공개")
R("dk_trust_kisre", "kis_re_trust", "dck1", "TRUST_SERVICES", "bupyeong_digital_edge", status="operating", sources=[DK],
  quote="토지 및 건물은 … 대주단을 수익자로 하여 한국투자부동산신탁 주식회사에 신탁")
ISSUE("bupyeong_digital_edge", "자료 상충", "언론의 'SK에코플랜트 49 : 디지털엣지 51' 지분과 디씨케이원 주주명부(Digital Edge Developments 100%)가 다름 — 상위 단계 지분으로 추정.")
ISSUE("bupyeong_digital_edge", "미확인", "SK에코플랜트 시공·책임준공 여부 감사보고서 미기재. 부평 'ESR/STACK' 별도 사업과 병합하지 않음.")

# 20-b. Digital Edge SEL1 (구 세종텔레콤 데이터센터 양수)
R("dek_sel1_sejong", "sejong_telecom", "digital_edge_kr", "ASSET_SALE", None, status="terminated", sources=["D_DEK_AR2025"],
  quote="세종텔레콤과 텔스트라네트워크앤비즈니스서비스코리아 간에 체결되어 있던 약정을 세종텔레콤으로부터 데이터센터 양수 시 이전",
  note="SEL1 데이터센터 사업 양수(과거 거래). SEL1 건물은 운용리스로 임차 운영")

# ════════════════════════════════════════════════════════════════════
# 21. 고양 삼송 데이터센터 (덕양구 오금동 690, 이지스) — goyang_samsong_dc
# ════════════════════════════════════════════════════════════════════
S("N_DNEWS_SAMSONG", "언론", "이지스운용, 80㎿ 규모 고양 삼송 데이터센터 준공", "대한경제", "2026-07-15",
  "https://www.dnews.co.kr/uhtml/view.jsp?idxno=202607151340213350300")
S("N_BABYTIMES_SAMSONG", "언론", "우리은행·이지스자산운용 데이터센터 주민피해 심각", "베이비타임즈", "2024",
  "https://www.babytimes.co.kr/news/articleView.html?idxno=70348")
P("goyang_samsong_dc", name_ko="고양 삼송 데이터센터 (이지스)", address="경기도 고양시 덕양구 오금동 690 일대",
  dc_class="hyperscale_colocation", stage="준공 (2026-07 사용승인, 80MW)",
  financing_summary="이지스자산운용 개발(펀드) · 우리은행(신탁업자 명의 건축주 추정) · 시공 한화건설 · 운영 LG CNS. 대주단 미공개",
  sources=["N_DNEWS_SAMSONG"], permit_match="kr_permit_1104100087534")
E("igis_samsong_fund", "이지스 삼송 데이터센터 펀드(명칭 미공개)", "fund", "kr_am", note="이지스자산운용 운용 · 우리은행 명의 건축주로 보도")
R("ss_mgr_igis", "igis_am", "igis_samsong_fund", "ASSET_MANAGER", "goyang_samsong_dc", status="operating", evidence="언론",
  sources=["N_DNEWS_SAMSONG"], quote="이지스자산운용이 경기 고양시에서 개발해 온 80㎿ 규모의 ‘삼송 데이터센터’를 준공")
R("ss_trustee_woori", "woori_bank", "igis_samsong_fund", "TRUST_SERVICES", "goyang_samsong_dc", status="operating",
  evidence="언론", sources=["N_BABYTIMES_SAMSONG"], quote="우리은행과 이지스자산운용이 건축주인 … 고양 삼송 이지스데이터센터",
  note="은행이 펀드 신탁업자 명의로 건축주가 되는 구조로 추정 — 우리은행 자기 익스포저 아님(INFERRED)")
R("ss_epc_hanwha", "hanwha_corp", "igis_samsong_fund", "EPC_CONTRACT", "goyang_samsong_dc", stage="construction",
  status="terminated", evidence="언론", sources=["N_DNEWS_SAMSONG"], quote="삼송 데이터센터 시공은 한화건설이 맡았고",
  note="한화건설은 2022년 (주)한화에 합병(건설부문) — 공사 완료")
R("ss_ops_lgcns", "lg_cns", "igis_samsong_fund", "FACILITY_OPERATION", "goyang_samsong_dc", stage="operations",
  status="operating", evidence="언론", sources=["N_DNEWS_SAMSONG"], quote="LG CNS가 위탁운영사로 참여한다")
ISSUE("goyang_samsong_dc", "미확인", "펀드명·대주단·출자자 공시 미확인 (연구 대기열의 '네이버클라우드' 참여 근거 미발견).")


# ════════════════════════════════════════════════════════════════════
# 22. 포항 AI Factory 데이터센터 (남구 오천읍 광명일반산단) — pohang_ai_factory
# ════════════════════════════════════════════════════════════════════
S("N_TRACKER_POHANG", "언론", "우리금융, 6000억 포항 AI데이터센터 PF…계열사 총출동", "더트래커", "2026-09-23",
  "https://thetracker.co.kr/View.aspx?No=4239556")
S("N_YNA_POHANG", "언론", "우리금융 \"포항 AI 데이터센터에 생산적 금융 공급\"", "연합뉴스", "2026-09-23",
  "https://www.yna.co.kr/view/AKR20260923071800002")
E("pohang_aif_spc", "포항 AI Factory 시행법인(명칭 미공개)", "spv", "project_finance", note="시행 SPC 명칭 보도·공시 미확인")
P("pohang_ai_factory", name_ko="포항 AI Factory 데이터센터", address="경상북도 포항시 남구 오천읍 광명일반산업단지 (광명리)",
  borrower="pohang_aif_spc", dc_class="ai_dedicated", stage="PF 약정 체결 (2026-09-23), 2027말 준공 목표 · 수전 40MW / IT 32MW",
  financing_summary="총사업비 6,000억 = 자기자본 1,500 + PF 4,500 (우리은행·KB국민은행 공동주선, 우리은행 대리은행). 대주별 금액 미공개",
  sources=["N_TRACKER_POHANG", "N_YNA_POHANG"], permit_match="kr_permit_1000000000000000883218")
PT = "N_TRACKER_POHANG"
for sid, rtype, role, q in [
    ("woori_bank", "ARRANGER", "공동 금융주선 · 대리은행", "우리은행은 KB국민은행과 공동 금융주선기관으로 참여하면서 대리은행 역할"),
    ("kb_bank", "ARRANGER", "공동 금융주선", "우리은행은 KB국민은행과 공동 금융주선기관으로 참여"),
    ("woori_inv_sec", "FINANCIAL_ADVISOR", "공동 금융자문", "우리투자증권은 현대차증권과 공동 금융자문을 담당"),
    ("hyundai_motor_sec", "FINANCIAL_ADVISOR", "공동 금융자문", "우리투자증권은 현대차증권과 공동 금융자문을 담당"),
    ("woori_am", "ASSET_MANAGER", "사업 발굴 · AMC", "우리자산운용은 초기 사업 발굴과 자산관리회사(AMC) 업무"),
    ("woori_asset_trust", "TRUST_SERVICES", "담보신탁 · 자금관리대리사무", "우리자산신탁은 담보신탁과 자금관리대리사무를 맡는다"),
]:
    R(f"ph_{sid}_{rtype.lower()}", sid, "pohang_aif_spc", rtype, "pohang_ai_factory", stage="main_pf", status="committed",
      evidence="언론", sources=[PT], role=role, quote=q,
      note="주선·자문·관리 역할 — 대출 보유액 아님" if rtype in ("ARRANGER", "FINANCIAL_ADVISOR") else None)
R("ph_pf_woori_cap", "woori_fin_capital", "pohang_aif_spc", "PROJECT_LOAN", "pohang_ai_factory", stage="main_pf", amt=None,
  amt_type="institution_commitment", status="committed", evidence="언론", sources=[PT],
  quote="우리금융캐피탈도 PF 금융에 참여한다", note="PF 4,500억 중 배분액 미공개")
R("ph_lease_nhn", "nhn_cloud", "pohang_aif_spc", "TENANT_LEASE", "pohang_ai_factory", stage="operations", status="committed",
  evidence="언론", sources=[PT], role="IT 32MW 중 16MW 사전임차확약 · 준공 후 운영",
  quote="NHN클라우드는 전체 IT 부하 32MW 가운데 16MW에 대해 사전임차확약을 제공했다. 준공 이후에는 데이터센터 운영도 맡는다")
R("ph_epc_hdec", "hyundai_enc", "pohang_aif_spc", "COMPLETION_GUARANTEE", "pohang_ai_factory", stage="construction",
  status="committed", contingent=True, evidence="언론", sources=[PT], trigger="책임준공 기한 내 미준공 시 (원리금 보증 아님)",
  quote="시공사는 현대건설이다. 현대건설이 책임준공확약을 제공")
ISSUE("pohang_ai_factory", "미확인", "시행 SPC 명칭·출자자(자기자본 1,500억)·대주단 전체 명단·기관별 금액 미공개. 우리은행·KB국민은행의 대출 참여액 미공개(주선만 확인).")

# ════════════════════════════════════════════════════════════════════
# 23. 용인 덕성리 데이터센터 (처인구 이동읍 덕성리 448-5, 용인덕성데이터센터PFV) — yongin_deokseong_dc
# ════════════════════════════════════════════════════════════════════
S("N_EDAILY_DEOKSEONG", "언론", "사업비 1.4조 '용인 AI 데이터센터' 다음달 첫삽…7100억 본PF 조달", "이데일리 마켓in", "2026-04-28",
  "https://marketin.edaily.co.kr/News/ReadE?newsId=05756406645420712")
E("yongin_deokseong_pfv", "용인덕성데이터센터피에프브이", "spv", "project_finance", "Yongin Deokseong DC PFV")
E("warburg_pincus", "워버그핀커스", "company", "financial", "Warburg Pincus")
E("mdm_am", "엠디엠자산운용", "asset_manager", "kr_am", "MDM Asset Management")
P("yongin_deokseong_dc", name_ko="용인 덕성리 AI 데이터센터", address="경기도 용인시 처인구 이동읍 덕성리 448-5 일원",
  borrower="yongin_deokseong_pfv", dc_class="ai_dedicated", stage="본PF 기표 예정→착공 (2026-05), 수전 80MW",
  financing_summary="총사업비 약 1.4조 · 본PF 약 7,100억(3년, 만기 2029-05) — 엠디엠자산운용·유진투자증권 주선. 대주별 명단·금액 미공개",
  sources=["N_EDAILY_DEOKSEONG"], permit_match="kr_permit_1000000000000000382383")
DS = "N_EDAILY_DEOKSEONG"
for sid in ["mdm_am", "eugene_inv_sec"]:
    R(f"ds_arr_{sid}", sid, "yongin_deokseong_pfv", "ARRANGER", "yongin_deokseong_dc", stage="main_pf", amt=None,
      amt_type="facility_total_context", status="committed", evidence="언론", sources=[DS],
      quote="엠디엠자산운용과 유진투자증권이 약 7100억원 규모 본PF를 주선했다", note="주선 규모는 보유 익스포저 아님")
for sid in ["warburg_pincus", "widecreek_am"]:
    R(f"ds_eq_{sid}", sid, "yongin_deokseong_pfv", "EQUITY_INVESTMENT", "yongin_deokseong_dc", stage="equity", amt=None,
      amt_type="equity_paid_in", status="funded", evidence="언론", sources=[DS],
      quote="글로벌 사모펀드 워버그핀커스가 관심을 보이면서 와이드크릭자산운용과 함께 지분을 인수했다",
      note="지분율·투자기구(펀드) 미공개")
R("ds_epc_samsung", "samsung_cnt", "yongin_deokseong_pfv", "EPC_CONTRACT", "yongin_deokseong_dc", stage="construction",
  status="committed", evidence="언론", sources=[DS], quote="시공은 삼성물산이 담당한다", note="도급액·책임준공 조건 미공개")
ISSUE("yongin_deokseong_dc", "미확인", "국민연금·교직원공제회 투자, KT클라우드 선임차 보도는 신뢰도 확인이 어려운 매체 — 미등록(추가 확인 대상).")
ISSUE("yongin_deokseong_dc", "미확인", "케이클라비스용인덕성피에프브이제25호(DART 법인)와의 관계 미확인 — 별도 사업 가능성.")


# ════════════════════════════════════════════════════════════════════
# 24. 진행 중 본PF 주선 (대한경제 2026-10-13) — 원창동·도화동·케펠 안산
# ════════════════════════════════════════════════════════════════════
S("N_DNEWS_PF_SEC_20261013", "언론", "국내 데이터센터 PF조달 전면에 나선 증권사", "대한경제", "2026-10-14",
  "https://m.dnews.co.kr/m_home/view.jsp?idxno=202610131019475400305")
S("N_IBT_IBK_DOHWA", "언론", "[IB토마토] IBK투자증권, PF 리스크 겹겹이…우발채무 늘고 회수는 늦어져", "IB토마토", "2026",
  "https://www.newstomato.com/readnews.aspx?no=1305284")
NS = "N_DNEWS_PF_SEC_20261013"
R("wc_arr_shinhan", "shinhan_sec", "cheongna_idc_pfv", "ARRANGER", "incheon_wonchang_dc", stage="main_pf", amt=None,
  amt_type="facility_total_context", status="review", evidence="언론", sources=[NS],
  quote="신한투자증권은 ‘인천 원창동 데이터센터 신축 사업’ PF 대표주선기관으로 참여 … PF 규모는 7000억원 이상으로 알려졌다",
  note="본PF 미종결(주선 진행 중) — 금액은 보도 추정치")
R("kp_arr_nhis", "nh_inv_sec", "keppel_ansan_pfv", "ARRANGER", "keppel_ansan", stage="main_pf", amt=None,
  amt_type="facility_total_context", status="review", evidence="언론", sources=[NS],
  quote="케펠 안산 데이터센터 PF 조달은 NH투자증권이 이끌고 있다 … PF 규모는 8000억원 수준", note="본PF 미종결")
E("kdb_infra_dohwa_fund", "키암코인천도화동데이터센터일반부동산사모투자회사", "fund", "kr_am",
  note="산은인프라자산운용 운용 · 도화동 데이터센터 사업주체(보도)")
P("incheon_dohwa_dc", name_ko="인천 도화동 데이터센터 (산은인프라)", address="인천광역시 미추홀구 도화동 765-18 일원",
  borrower="kdb_infra_dohwa_fund", dc_class="hyperscale_dev", stage="브릿지(2차 연장) · 본PF 주선 중 (80MW, 지상 7층)",
  financing_summary="본PF 약 8,000억 IBK투자증권 대표주선(2026-12 종결 목표, 보도). 브릿지 대주·금액 미공개",
  sources=[NS, "N_IBT_IBK_DOHWA"], permit_match="kr_permit_1000000000000000275031")
R("dh_mgr_kdbinfra", "kdb_infra_am", "kdb_infra_dohwa_fund", "ASSET_MANAGER", "incheon_dohwa_dc", status="operating",
  evidence="언론", sources=[NS, "N_IBT_IBK_DOHWA"], quote="인천 도화동 데이터센터는 산은인프라자산운용이 추진하고 있는 사업")
R("dh_arr_ibkis", "ibk_sec", "kdb_infra_dohwa_fund", "ARRANGER", "incheon_dohwa_dc", stage="main_pf", amt=None,
  amt_type="facility_total_context", status="review", evidence="언론", sources=[NS],
  quote="IBK투자증권은 인천 도화동 데이터센터 PF 조달에 대표주선기관으로 … PF 규모는 8000억원 수준")
ISSUE("incheon_dohwa_dc", "미확인", "IB토마토는 IBK투자증권의 도화동 관련 우발채무(브릿지 매입확약 등)를 다뤘으나 금액·구조는 기사 원문 확인 필요. "
      "하나증권·현대차증권 공동주관설은 검색 발췌로만 확인 → 미등록.")

# ════════════════════════════════════════════════════════════════════
# 25. 하남 풍산동 595 엣지 데이터센터 (하남엣지센터PFV, 물류센터 전환) — hanam_edge_dc
# ════════════════════════════════════════════════════════════════════
S("N_EDAILY_HANAM_EDGE", "언론", "“수도권 데이터센터, 크게 짓기 어렵다”…하남 물류센터의 ‘작은 변신’", "이데일리 마켓in", "2026-09-22",
  "https://marketin.edaily.co.kr/News/Read?newsId=04605126645582744")
E("hanam_edge_pfv", "하남엣지센터피에프브이", "spv", "project_finance", "Hanam Edge Center PFV")
E("cj_logistics", "CJ대한통운", "company", "kr_construction", "CJ Logistics (건설부문)", listed=True)
E("kyobo_sec", "교보증권", "securities", "kr_securities", "Kyobo Securities", listed=True)
P("hanam_edge_dc", name_ko="하남 풍산 엣지 데이터센터 (물류센터 용도변경)", address="경기도 하남시 풍산동 595 일원",
  borrower="hanam_edge_pfv", dc_class="edge", stage="공사 중 (2027-08 준공 목표, 10MW 이하)",
  financing_summary="브릿지 440억(2026-02) → 본PF 1,620억(2026-07; Tr.A 1,420 = 한도 1,000 + 일시 420, Tr.B 200), 교보증권 주관. 대주 명단 미공개",
  sources=["N_EDAILY_HANAM_EDGE"], permit_match="kr_permit_1000000000000000829406")
R("he_arr_kyobo", "kyobo_sec", "hanam_edge_pfv", "ARRANGER", "hanam_edge_dc", stage="main_pf", amt=None,
  amt_type="facility_total_context", status="committed", evidence="언론", sources=["N_EDAILY_HANAM_EDGE"],
  quote="1620억원 규모 본PF는 선순위인 트랜치A 1420억원과 후순위인 트랜치B 200억원으로 구성됐다. 주관사는 교보증권이 맡았다")
R("he_epc_cj", "cj_logistics", "hanam_edge_pfv", "EPC_CONTRACT", "hanam_edge_dc", stage="construction", status="committed",
  evidence="언론", sources=["N_EDAILY_HANAM_EDGE"], quote="시공은 CJ대한통운 건설 부문이 맡았다")
ISSUE("hanam_edge_dc", "미확인", "삼성생명·삼성SRA자산운용 사업주체설은 유료 기사 발췌로만 확인 → 미등록. 대주단·책임준공 조건 미공개.")


# ════════════════════════════════════════════════════════════════════
# 26. 인천 원창동 — 북항아이디씨PFV (청라아이디씨PFV와 별개 사업) — incheon_bukhang_idc (신규)
# ════════════════════════════════════════════════════════════════════
S("D_BHIDC_AR2025", "공시", "북항아이디씨피에프브이 감사보고서 (2025.12)", "DART · 삼덕회계법인", "2026-04-08",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260408000471", rcept_no="20260408000471", section="주석 1(주주), 6(차입금), 7(담보·약정)")
S("N_DNEWS_BRIDGE_20260713", "언론", "데이터센터 개발 브릿지론 공급하는 증권사", "대한경제", "2026-07-13",
  "https://www.dnews.co.kr/uhtml/view.jsp?idxno=202607131102301460891")
E("bukhang_idc_pfv", "북항아이디씨피에프브이", "spv", "project_finance", "Bukhang IDC PFV", note="인천 서구 원창동 토지 · 2023-06 설립")
E("hj_heavy", "HJ중공업", "company", "kr_construction", "HJ Heavy Industries", listed=True, note="북항IDC PFV 최대주주")
E("shinwon_dnd", "신원디앤디", "company", "kr_operator"); E("star_dnd", "스타디앤디", "company", "kr_operator", note="AMC")
E("meritz_fire", "메리츠화재", "insurer", "kr_insurance", "Meritz Fire & Marine", listed=True)
E("meritz_capital", "메리츠캐피탈", "nbFI", "kr_bank", "Meritz Capital")
E("acuon_capital", "애큐온캐피탈", "nbFI", "kr_bank", "Acuon Capital")
E("a1_breeze", "에이원브리즈", "spv", "project_finance", note="공동1순위 우선수익자(154.8억) — 성격 미확인(유동화 SPC 추정)")
E("a1_living", "에이원리빙", "spv", "project_finance", note="공동3순위 우선수익자")
E("artic_nh_lp", "합자조합 ARTIC NORTH HARBOUR", "fund", "kr_am", note="12% 후순위 성격 차입")
E("icecream_media", "아이스크림미디어", "company", "kr_operator", listed=True, note="공동2순위 우선수익자 60억")
E("theym_korea", "더와이엠코리아", "company", "kr_operator")
E("daol_sec", "다올투자증권", "securities", "kr_securities", "Daol Investment & Securities", listed=True)
E("shinwoo_cu", "신우신협", "cooperative", "kr_cooperative", note="개별 신협(신협중앙회와 별개)")
P("incheon_bukhang_idc", name_ko="인천 원창동 데이터센터 (북항아이디씨PFV)", address="인천광역시 서구 원창동 (토지 — 지번 공시 미기재)",
  borrower="bukhang_idc_pfv", dc_class="hyperscale_dev", stage="브릿지 (토지 확보, 도시계획변경·전력 확보 조건부)",
  financing_summary="2025말 단기차입 1,288억(메리츠화재·메리츠캐피탈 각 258 등) · 2026-07 브릿지 750억 리파이낸싱(메리츠 650, 메리츠·다올투자증권 주선, 보도)",
  sources=["D_BHIDC_AR2025", "N_DNEWS_BRIDGE_20260713"])
BH = "D_BHIDC_AR2025"; AS = "2025-12-31"
for lid, amt, rate in [("meritz_fire", 258, "7.0%"), ("meritz_capital", 258, "7.0%"), ("jt_savings", 30, "7.0%"),
                       ("daol_savings", 100, "9.0%"), ("artic_nh_lp", 50, "12.0%"), ("acuon_savings", 40, "9.0%"),
                       ("acuon_capital", 40, "9.0%")]:
    R(f"bh_br_{lid}", lid, "bukhang_idc_pfv", "PROJECT_LOAN", "incheon_bukhang_idc", stage="bridge", amt=amt,
      amt_type="outstanding", as_of=AS, rate=rate, status="funded", sources=[BH],
      quote=f"단기차입금 {amt*100:,.0f}백만원 · {rate} · 부동산신탁 우선수익권")
for lid, lim, rank in [("a1_breeze", 154.8, "공동1순위"), ("icecream_media", 60, "공동2순위"), ("theym_korea", 6, "공동2순위"),
                       ("a1_living", 96, "공동3순위")]:
    R(f"bh_pb_{lid}", lid, "bukhang_idc_pfv", "PRIORITY_BENEFICIARY", "incheon_bukhang_idc", stage="bridge", amt=lim,
      amt_type="priority_beneficiary_limit", as_of=AS, seniority=rank, status="funded", sources=[BH],
      quote=f"{rank} 우선수익권 {lim*100:,.0f}백만원",
      note="차입금 표 일부 행만 확인 — 우선수익권 보유는 대출 담보 목적(대출 약정 존재 추정, 금액은 한도)")
for lid, amt in [("shinwoo_cu", 16), ("suhyup_bank", 160), ("acuon_capital", 30), ("daol_savings", 110.1)]:
    R(f"bh_old_{lid}_{int(amt)}", lid, "bukhang_idc_pfv", "PROJECT_LOAN", "incheon_bukhang_idc", stage="bridge", amt=amt,
      amt_type="historical_outstanding", as_of="2024-12-31", status="repaid", sources=[BH],
      quote=f"(전기 차입금 표) {amt*100:,.0f}백만원", note="전기 브릿지 대주 — 2025 대환으로 상환 추정")
R("bh_eq_klt", "korealand_trust", "bukhang_idc_pfv", "EQUITY_INVESTMENT", "incheon_bukhang_idc", stage="equity", amt=75,
  amt_type="equity_par_value", as_of=AS, status="funded", sources=[BH], role="종류주 1,500,000주 (5%) · AMC",
  quote="(주)한국토지신탁 1,500,000 5.00% 종류주식")
R("bh_eq_hj", "hj_heavy", "bukhang_idc_pfv", "EQUITY_INVESTMENT", "incheon_bukhang_idc", stage="equity", amt=None,
  amt_type="equity_paid_in", as_of=AS, status="funded", sources=[BH], role="최대주주 (보유주식 전부 대주에 근질권)",
  quote="최대주주인 (주)에이치제이중공업 보유주식 전부 … 근질권 … 채권최고액은 77,400백만원")
R("bh_pledge_hj", "hj_heavy", "bukhang_idc_pfv", "SHARE_PLEDGE", "incheon_bukhang_idc", stage="bridge", amt=774,
  amt_type="pledge_limit", status="committed", contingent=True, sources=[BH], trigger="브릿지 기한이익상실 시 주식 처분",
  quote="근질권자는 메리츠화재해상보험(주), 메리츠캐피탈(주), 에이원브리즈(주)로서 채권최고액은 77,400백만원")
R("bh_eq_shinwon", "shinwon_dnd", "bukhang_idc_pfv", "EQUITY_INVESTMENT", "incheon_bukhang_idc", stage="equity", amt=None,
  amt_type="equity_paid_in", status="funded", sources=[BH], quote="신원디앤디(주) 보유 종류주식 1주에 대하여 근질권")
R("bh_amc", "korealand_trust", "bukhang_idc_pfv", "ASSET_MANAGER", "incheon_bukhang_idc", status="operating", sources=[BH],
  quote="(주)한국토지신탁 및 스타디앤디(주)와 … 자산관리 위탁계약")
R("bh_trust_mgh", "mugunghwa_trust", "bukhang_idc_pfv", "TRUST_SERVICES", "incheon_bukhang_idc", status="operating", sources=[BH],
  quote="(주)무궁화신탁과 … 자금관리 대리사무계약")
R("bh_arr_meritz", "meritz_sec", "bukhang_idc_pfv", "ARRANGER", "incheon_bukhang_idc", stage="bridge", amt=650,
  amt_type="institution_commitment", as_of="2026-07-13", status="funded", evidence="언론", sources=["N_DNEWS_BRIDGE_20260713"],
  quote="메리츠증권과 다올투자증권이 금융주선기관으로 참여했고, 메리츠증권이 브릿지론 대부분인 650억원을 지원",
  note="'메리츠증권 650억 지원'의 실제 대주 명의는 감사보고서상 메리츠화재·메리츠캐피탈 등 계열사로 보임 — 중복 합산 금지")
R("bh_arr_daol", "daol_sec", "bukhang_idc_pfv", "ARRANGER", "incheon_bukhang_idc", stage="bridge", status="funded",
  evidence="언론", sources=["N_DNEWS_BRIDGE_20260713"], quote="메리츠증권과 다올투자증권이 금융주선기관으로 참여")
ISSUE("incheon_bukhang_idc", "프로젝트 식별", "원창동 청라아이디씨PFV(381-73, 이도)와 북항아이디씨PFV(HJ중공업)는 별개 사업 — 병합 금지.")
ISSUE("incheon_bukhang_idc", "부분 확인", "단기차입금 합계 1,288억 중 감사보고서에서 행 단위로 확인한 대주는 776억 — 나머지 대주 행 재확인 필요.")

# 27. 원창동 청라IDC — 시공사 (언론)
S("N_MK_WONCHANG_EPC", "언론", "현대엔지니어링, 8700억원 규모 인천 데이터센터 공사 수주", "매일경제", "2026-10-07",
  "https://www.mk.co.kr/news/realestate/12170321")
R("wc_epc_hec", "hyundai_eng", "cheongna_idc_pfv", "EPC_CONTRACT", "incheon_wonchang_dc", stage="construction", amt=None,
  amt_type="construction_contract_value", status="committed", evidence="언론", sources=["N_MK_WONCHANG_EPC"],
  quote="이도테라원이 설립한 청라 IDC PFV가 발주했다 … 현대엔지니어링은 건축과 토목, 설비, 조경, 통신 공사를 맡는다",
  note="8,700억은 총사업비 — 도급액 아님")
R("wc_epc_ktc", "kt_cloud", "cheongna_idc_pfv", "EPC_CONTRACT", "incheon_wonchang_dc", stage="construction", amt=None,
  amt_type="construction_contract_value", status="committed", evidence="언론", sources=["N_MK_WONCHANG_EPC"],
  quote="기계·전기·배관 공사는 공동 시공사인 KT클라우드와 함께 수행한다")
R("sgc_epc_hec", "hyundai_eng", "sgc_ai_infra", "EPC_CONTRACT", "gunsan_sgc_dc", stage="construction", status="committed",
  evidence="언론", sources=["N_MK_WONCHANG_EPC"], quote="군산 AI데이터센터에 이어 연속 수주", note="군산 SGC AI DC 수주(기사 부제) — 계약 상대·금액 미확인")

# 28. 가산-eDC (독산동, 마스턴) — dnews 브릿지
P("gasan_edc_mastern", name_ko="가산-eDC (독산동 엣지 데이터센터, 마스턴)", address="서울특별시 금천구 독산동 (지번 미공개)",
  dc_class="edge", stage="브릿지 (9MW)", financing_summary="브릿지 300억 — 한국투자증권 금융주선 (보도). 차주 법인·대주 미공개",
  sources=["N_DNEWS_BRIDGE_20260713"])
E("gasan_edc_spv", "가산-eDC 시행법인(명칭 미공개)", "spv", "project_finance", note="마스턴투자운용 추진")
R("ge_amc_mastern", "mastern_am", "gasan_edc_spv", "ASSET_MANAGER", "gasan_edc_mastern", status="operating", evidence="언론",
  sources=["N_DNEWS_BRIDGE_20260713"], quote="마스턴투자운용이 진행하고 있는 ‘가산-eDC 개발사업’")
R("ge_arr_kis", "korea_inv_sec", "gasan_edc_spv", "ARRANGER", "gasan_edc_mastern", stage="bridge", amt=None,
  amt_type="facility_total_context", status="funded", evidence="언론", sources=["N_DNEWS_BRIDGE_20260713"],
  quote="‘가산-eDC 개발사업’의 브릿지론 300억원은 한국투자증권의 금융주선으로 조달했다")


# ════════════════════════════════════════════════════════════════════
# 29. 구로 개봉동 데이터센터 (개봉동 166-2, 블루리본디벨롭먼트) — guro_gaebong_dc
# ════════════════════════════════════════════════════════════════════
S("N_DEALSITE_GURO", "언론", "롯데건설 시공, 구로 데이터센터 본PF 전환 임박", "딜사이트", "2024-11-11", "https://dealsite.co.kr/articles/131096")
S("D_BLUERIBBON_AR2025", "공시", "블루리본디벨롭먼트 감사보고서 (2025.12)", "DART · 우리회계법인", "2026-04-06",
  "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260406002845", rcept_no="20260406002845")
E("blueribbon_dev", "블루리본디벨롭먼트", "company", "project_finance", "Blue Ribbon Development")
E("ongo_tech", "온고테크", "company", "kr_operator")
P("guro_gaebong_dc", name_ko="구로 개봉동 데이터센터 (블루리본디벨롭먼트)", address="서울특별시 구로구 개봉동 166-2",
  borrower="blueribbon_dev", dc_class="colocation", stage="현재 상태 미확인 (2024 본PF 전환 임박 보도 → 2025 감사보고서상 차입금 상환)",
  financing_summary="2024 보도: 브릿지 차환 반복(단기차입 725억), 롯데건설 지분 25%·자금대여 50억·SPC 차입 180억 조건부 채무인수. "
                    "2025 감사보고서: 특수관계자 차입 전액 상환, 제공받은 보증 없음",
  sources=["N_DEALSITE_GURO", "D_BLUERIBBON_AR2025"], permit_match="kr_permit_1000000000000000205388")
for sid, pct in [("lotte_enc", "25%"), ("korea_inv_sec", "19%"), ("ongo_tech", "11%")]:
    R(f"gr_eq_{sid}", sid, "blueribbon_dev", "EQUITY_INVESTMENT", "guro_gaebong_dc", stage="equity", amt=None,
      amt_type="equity_paid_in", as_of="2024-11-08", status="unknown", evidence="언론", sources=["N_DEALSITE_GURO"],
      role=f"지분 {pct} (2024 보도)", quote="주요 주주는 ▲개인투자 4인 45% ▲롯데건설 25% ▲한국투자증권 19% ▲온고테크 11%",
      note="2025 감사보고서 주주명부와 대조 필요 — 현재 지분 미확인")
R("gr_cda_lotte", "lotte_enc", "blueribbon_dev", "DEBT_ASSUMPTION", "guro_gaebong_dc", stage="bridge", amt=180,
  amt_type="guarantee_limit", as_of="2024-11-08", status="unknown", contingent=True, evidence="언론", sources=["N_DEALSITE_GURO"],
  trigger="조건부 채무인수 (조건 상세 미공개)",
  quote="시행사가 유동화회사(SPC)를 통해 조달한 180억원의 차입금까지 조건부 채무인수 약정",
  note="2025 감사보고서: '타인으로부터 제공받은 지급보증 없음' → 종료 가능성. 현재 상태 미확인")
R("gr_loan_lotte", "lotte_enc", "blueribbon_dev", "SHAREHOLDER_LOAN", "guro_gaebong_dc", stage="bridge", amt=6.25,
  amt_type="historical_outstanding", as_of="2024-12-31", status="repaid", sources=["D_BLUERIBBON_AR2025"],
  quote="(주)롯데건설 단기차입금 전기말 625,000,000 → 당기말 - (자금상환 625,000,000)")
R("gr_epc_lotte", "lotte_enc", "blueribbon_dev", "EPC_CONTRACT", "guro_gaebong_dc", stage="construction", status="unknown",
  evidence="언론", sources=["N_DEALSITE_GURO"], quote="시공은 프로젝트의 지분을 가지고 있는 롯데건설이 맡았다")
ISSUE("guro_gaebong_dc", "현재 상태 미확인", "2025 감사보고서상 이익잉여금 흑자 전환·차입 상환 — 사업지 매각 가능성. 매수자·현재 시행 주체 확인 필요.")
ISSUE("bucheon_samjeong_ai", "자료 상충", "시공사 표기: 이데일리(기존)=DL이앤씨, 서울파이낸스(2026-10)='DL건설 1,268억 수주' — 동일 계약의 법인 표기 차이 확인 필요.")


# ════════════════════════════════════════════════════════════════════
# 30. 세종텔레콤 분당 IDC (용인 수지구 소재, 호스트웨이 임차) — bundang_hostway_idc (소유권 이전 보강)
# ════════════════════════════════════════════════════════════════════
P("bundang_hostway_idc", name_ko="세종텔레콤 분당 IDC (호스트웨이 임차)", address="경기도 용인시 수지구 (보도 기준)",
  borrower="bundang_idc_fund", dc_class="colocation", stage="운영 중 (2025-07 소유권 이전)",
  financing_summary="파인앤파트너스자산운용 매수(매도인 하나대체자산운용) · 매매가·인수금융 미공개", sources=["N_ECONOVILL_BUNDANG"])
S("N_ECONOVILL_BUNDANG", "언론", "알스퀘어, '세종텔레콤 분당 IDC' 매각…중소형 데이터센터 투자 새 장 열다", "이코노믹리뷰", "2025-07-10",
  "https://www.econovill.com/news/articleView.html?idxno=702962")
E("bundang_idc_fund", "파인앤파트너스 분당 IDC 투자기구(명칭 미공개)", "fund", "kr_am", note="매수 주체 펀드명 미공개")
R("bd_buyer_fine", "fine_partners_am", "bundang_idc_fund", "ASSET_MANAGER", "bundang_hostway_idc", status="operating",
  evidence="언론", sources=["N_ECONOVILL_BUNDANG"], role="2025-07 매수(새 소유주로 보도)",
  quote="부동산자산운용사인 파인앤파트너스자산운용이 새로운 주인으로 나섰으며, 매도인은 하나대체자산운용이다")
R("bd_seller_hana_alt", "hana_alt_am", "bundang_idc_fund", "ASSET_SALE", "bundang_hostway_idc", status="terminated",
  evidence="언론", sources=["N_ECONOVILL_BUNDANG"], quote="매도인은 하나대체자산운용이다", note="과거 소유(운용) — 2025-07 매각 완료")
R("bd_lease_hostway", "hostway_kr", "bundang_idc_fund", "TENANT_LEASE", "bundang_hostway_idc", stage="operations",
  status="operating", evidence="언론", sources=["N_ECONOVILL_BUNDANG"], quote="세종텔레콤 분당 IDC (호스트웨이 장기 임차 — v5 데이터)",
  note="임차 조건(2034년 6월까지 전체 임차)은 v5 데이터 출처 기준 — 이번 조사에서 원문 재확인 못함")
ISSUE("bundang_hostway_idc", "프로젝트 식별", "기사상 자산 소재지는 '경기도 용인시 수지구' — 명칭(분당 IDC)과 행정구역이 다름. 매매가·인수금융 대주 미공개.")
