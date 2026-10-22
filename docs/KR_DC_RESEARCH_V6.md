# 국내 AI 데이터센터 개발사업 조사 · 반영 결과 (v6)

기준일 2026-10-21 · 금액 단위 억원 · 이 문서는 `python scripts/report_kr_dc_v6.py`로 빌드 산출물에서 자동 생성됩니다.

## 1. 조사 방법과 범위

- 1차 근거: DART 사업법인(PFV·SPC·시행사) 감사보고서 주석(주주·차입금·약정·담보신탁·특수관계자), 건설사·계열사 공시(채무보증결정·단일판매공급계약·유상증자·담보제공). KIND 거래소 공시 포함.
- 2차 근거: 신뢰 가능한 언론 보도와 회사 공식 발표. 언론만으로 확인한 관계는 `evidence_kind=언론`으로 구분합니다.
- 원칙: MOU를 실행으로 바꾸지 않음 · 신디케이트 총액을 각 대주에 배분하지 않음 · 주선사 딜 규모를 익스포저로 쓰지 않음 · 펀드 자금을 운용사 고유자금으로 쓰지 않음 · 과거 금액을 현재 잔액으로 쓰지 않음 · 도급액을 미수금으로 쓰지 않음 · 미공개는 0이 아니라 null.
- 한계: 유료 기사(더벨 등) 본문은 우회하지 않았습니다. 펀드 수익자·대주단 내부 배분·현재 잔액은 비공개인 경우가 많아 '미공개'로 남겼습니다. '자료 미발견' 70곳은 DART 감사보고서 30여 건의 대주·주주·보증 명부 대조와 이름 검색 결과이며, 기업별 전수 공시 검색을 한 것은 아닙니다.

## 2. 사업별 조사 결과

| 사업 | 차주(SPV) | 단계 | 확인 관계 | 현재 대출 약정(공시 합산) | 실행액 | 근거 |
|---|---|---|---:|---:|---:|---|
| 안성 한화그룹 제2데이터센터 (알이씨데이터센터) | 알이씨데이터센터 | 공사 중 · PF 약정(2026-07-29) | 5 | 미공개 (2건) | 미공개 | 공시 4, 언론 1 |
| 부천 삼정동(13-15) 데이터센터 — 퍼시픽피치 | 퍼시픽피치피에프브이 | 공사 중 (연면적 76,429㎡ · 지하4~지상6층) | 30 | 5,900억 (17건) | 3,047억 | 공시 30 |
| 부천 삼정 AI 데이터센터 | 디씨아이티와이부천피에프브이 | 착공 전·PF 약정 | 9 | 미공개 (4건) | 미공개 | 공시 7, 언론 2 |
| 세종텔레콤 분당 IDC (호스트웨이 임차) | 파인앤파트너스 분당 IDC 투자기구(명칭 미공개) | 운영 중 (2025-07 소유권 이전) | 4 | 미공개 | 미공개 | 언론 3, 기존 데이터 1 |
| 부평 데이터센터 (Digital Edge SEL2·SEL3) | 디씨케이원 | 1단계 운영·2단계(Phase II-1) 공사 | 21 | 8,000억 (9건) | 5,020억 | 공시 20, 언론 1 |
| 부산 에코델타시티 데이터센터 | 부산에코델타그린데이터센터피에프브이 | 토지 매입 단계 (본PF 전) | 9 | 202.1억 (1건) | 202.1억 | 공시 9 |
| 캄스퀘어 안산 데이터센터 | 캄스퀘어안산데이터센터PFV | 공사 중 | 64 | 9,700억 (32건) | 2,711억 | 공시 57, 언론 7 |
| 용인 지곡 데이터센터 (캄스퀘어 용인) | 캄스퀘어용인데이터센터PFV | 토지 매입·브릿지 (수전 60MW) | 6 | 450억 (2건) | 미공개 | 언론 6 |
| 케이스퀘어 가산 데이터센터 | 케이스퀘어데이터센터PFV | 운영 중 (2025 준공·운영 개시) | 35 | 3,800억 (8건) | 3,746억 | 공시 30, 언론 5 |
| GS 동해 AIDC | 동해에이아이제3캠퍼스 | 전력인프라 공사 계약 (2028 준공 예정) | 2 | 미공개 | 미공개 | 공시 2 |
| 가산 DCI SEL1 데이터센터 | 가산디씨제이브이 | 운영 중 (2025 준공·코로케이션 개시) | 13 | 미공개 | 미공개 | 공시 13 |
| 가산-eDC (독산동 엣지 데이터센터, 마스턴) | 미확인 | 브릿지 (9MW) | 2 | 미공개 | 미공개 | 언론 2 |
| 가산 STT Seoul 1 데이터센터 | 가산랜드마크데이터센터피에프브이 | 운영 중 (2025 준공, 100% 책임임차 20+20년) | 35 | 2,300억 (7건) | 2,000억 | 공시 35 |
| 고양 삼송 데이터센터 (이지스) | 미확인 | 준공 (2026-07 사용승인, 80MW) | 4 | 미공개 | 미공개 | 언론 4 |
| 군산 비응도 데이터센터 (SGC, 60MW) | 에스지씨에이아이인프라 | 부지조성 (토지 PEF 매각·리스백 구조 추정) | 3 | 미공개 | 미공개 | 공시 2, 언론 1 |
| 구로 개봉동 데이터센터 (블루리본디벨롭먼트) | 블루리본디벨롭먼트 | 현재 상태 미확인 (2024 본PF 전환 임박 보도 → 2025 감사보고서상 차입금 상환) | 6 | 미공개 | 미공개 | 언론 5, 공시 1 |
| 장성 파인데이터센터 | 파인디씨피에프브이 | 공사 중 (2027-12 준공 예정, 수전 26MW / IT 16.7MW) | 8 | 미공개 | 미공개 | 언론 6, 공시 2 |
| 하남 풍산 엣지 데이터센터 (물류센터 용도변경) | 하남엣지센터피에프브이 | 공사 중 (2027-08 준공 목표, 10MW 이하) | 2 | 미공개 | 미공개 | 언론 2 |
| 하남 풍산 데이터센터 (MKIF·LG CNS 임차) | 그린디지털인프라 | 운영 중 (2023-11 준공, 수전 40MW / IT 25.44MW) | 14 | 5,150억 (10건) | 4,950억 | 공시 12, 공식발표 2 |
| 인천 원창동 데이터센터 (북항아이디씨PFV) | 북항아이디씨피에프브이 | 브릿지 (토지 확보, 도시계획변경·전력 확보 조건부) | 23 | 미공개 | 미공개 | 공시 21, 언론 2 |
| 인천 도화동 데이터센터 (산은인프라) | 키암코인천도화동데이터센터일반부동산사모투자회사 | 브릿지(2차 연장) · 본PF 주선 중 (80MW, 지상 7층) | 2 | 미공개 | 미공개 | 언론 2 |
| 인천 구월 AI 허브센터 | 디씨아이티와이인천피에프브이 | 토지 매입·인허가 (PF 미확인) | 2 | 미공개 | 미공개 | 공시 2 |
| 인천 원창동 데이터센터 (청라 IDC) | 청라아이디씨피에프브이 | 브릿지 단계 (본PF 전) | 20 | 미공개 | 미공개 | 공시 17, 언론 3 |
| 케펠 안산 원시동 데이터센터 | 케펠데이터센터안산피에프브이 | 브릿지 단계 (본PF 전) | 16 | 310억 (3건) | 310억 | 공시 15, 언론 1 |
| 안산 성곡동 712 데이터센터 (브룩필드·코람코시화PFV) | 코람코시화데이터센터피에프브이 | 개발 (차입금 전액 상환·지분 투자 단계) | 10 | 미공개 | 미공개 | 공시 10 |
| 마그나 고양 덕이 데이터센터 | 마그나피에프브이 | 공사 중 | 31 | 2,730억 (8건) | 908억 | 공시 29, 언론 2 |
| 포항 AI Factory 데이터센터 | 포항 AI Factory 시행법인(명칭 미공개) | PF 약정 체결 (2026-09-23), 2027말 준공 목표 · 수전 40MW / IT 32MW | 9 | 미공개 (1건) | 미공개 | 언론 9 |
| 영등포 Y-eDC 데이터센터 | 엣지코어피에프브이 | 공사 중 | 15 | 2,200억 (4건) | 820억 | 공시 14, 언론 1 |
| 용인 덕성리 AI 데이터센터 | 용인덕성데이터센터피에프브이 | 본PF 기표 예정→착공 (2026-05), 수전 80MW | 5 | 미공개 | 미공개 | 언론 5 |
| 용인 죽전 퍼시픽써니 데이터센터 | 퍼시픽써니 시행 SPC(법인명 미확인) | 운영 중 (IT 64MW / 수전 100MW, LG CNS 운영) | 5 | 미공개 | 미공개 | 언론 5 |

현재 대출 약정은 상환되지 않은 대출성 관계(PF·인수금융·신용공여)의 기관별 약정만 더한 값입니다. 보증한도·우선수익권 한도·도급액·주선 규모는 더하지 않습니다.

## 3. 기업별 조사 상태

| 조사 상태 | 기업 수 | 지도 |
|---|---:|---|
| 조사 완료 · 공시 확인 | 201 | 표시 |
| 자료 미발견 | 70 | 숨김 (데이터에 유지) |
| 일부 확인 · 언론/공식발표 | 42 | 표시 |
| 기존 데이터 유지 · 추가 근거 미발견 | 8 | 표시 |

기업별 전체 목록: `frontend/public/data/pf/kr_dc_entity_status.csv` (앱의 Data & Sources 화면에도 표시).
'접근 제한'으로 분류한 기업은 없습니다. 유료 기사로만 언급된 사항은 아래 6절 미확인 목록에 사업별로 적었습니다.

## 4. 관계·출처 목록

- 새로 반영한 관계 382건 (공시 333 · 언론 47 · 공식발표 2). 모든 관계에 출처 URL·일자가 있고, 공시는 접수번호(rcept_no)와 원문 인용을 함께 기록했습니다.
- 파일: `frontend/public/data/pf/kr_dc_relationships.csv` / `.json` (관계별 금액·금액유형·실행액·순위·금리·만기·상태·조건부 의무·발동 조건·충격 방향·출처).
- 관계 유형: PROJECT_LOAN 160, EQUITY_INVESTMENT 76, PRIORITY_BENEFICIARY 21, TRUST_SERVICES 19, ASSET_MANAGER 18, EPC_CONTRACT 17, ARRANGER 15, ACQUISITION_LOAN 9, CORPORATE_LOAN 6, ABS_SPONSOR 5, SHARE_PLEDGE 5, TENANT_LEASE 5, ASSET_SALE 5, SHAREHOLDER_LOAN 4, COMPLETION_GUARANTEE 3, PARENT_AFFILIATE 2, LOAN_GUARANTEE 2, LEASE_GUARANTEE 2, DEBT_ASSUMPTION 2, FINANCIAL_ADVISOR 2, INSURANCE_PLEDGE 1, COLLATERAL_PROVIDED 1, REVOLVER 1, FACILITY_OPERATION 1

## 5. 변경 내역

- 추가 기업 140 · 추가 관계 382 · 추가 사업 20 · 갱신 사업 10
- 숨김 처리 70 (근거 미발견 · 데이터에는 유지)

### 병합 (ID 하나로 통합, 이전 ID는 별칭으로 보존)
- `kreit` → `korealand_trust` (한국토지신탁)
- `korea_land_trust` → `korealand_trust` (한국토지신탁)
- `woori_trust` → `woori_asset_trust` (우리자산신탁)
- `ibk` → `ibk_bank` (IBK기업은행)
- `woori_ib` → `woori_inv_sec` (우리투자증권)
- `hanwha_eng` → `hanwha_corp` (한화)
- `kfcc` → `nh_fg` (농협금융지주)

### 삭제
- `mg_seoul` — ‘서울특별시새마을금고’ 등 시·도 명칭 노드는 실재 단일 법인이 아님(중앙회 지역본부/가칭) — 삭제
- `mg_busan` — 시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님
- `mg_incheon` — 시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님
- `mg_daegu` — 시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님
- `mg_gwangju` — 시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님
- `mg_daejeon` — 시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님
- `mg_ulsan` — 시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님
- `mg_gyeonggi` — 시·도 명칭 새마을금고 노드 — 실재 단일 법인 아님

### 공시 근거로 대체한 기존 관계 (v5 → v6)
- `pf_lf_casequare` — LF 출자액 97억(오기) → 감사보고서 970억(66.9%)으로 정정 대체
- `pf_hyundai_casequare_epc_co` — 감사보고서 시공·우선수익권 소멸(준공) 관계로 대체
- `pf_koramco_am_casequare` — 감사보고서 주주·자산관리 관계로 대체
- `pf_koramco_trust_eq` — 감사보고서 주주명부로 대체
- `pf_db_ins_eq` — 감사보고서 주주명부로 대체
- `pf_nh_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_tongyang_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_hyundai_cap_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_woori_cap_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_shinhan_cap_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_kb_cap_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_hyundai_com_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_woori_ib_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_thek_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_kis_junior_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_mountain_casequare` — 케이스퀘어 2025 감사보고서로 대체 (종전 대주는 '상환'으로, 신규 대주는 약정·실행액으로 재등록)
- `pf_eugene_camsquare` — 감사보고서 2종종류주 출자로 대체
- `pf_korea_alt_camsquare` — 감사보고서 AMC·출자 관계로 대체
- `pf_hanwha_camsq_yongin_bridge` — 딜북(2026-02) 기준 한화투자증권 SPC 380억 경유 관계로 정정 — 선순위 530억 전액 배분 오류
- `pf_sksec_camsq_yongin_mezz` — SK증권 SPC 경유 관계로 정정
- `pf_hanwha_edgecore_support` — 한화 주식근질권(2,860억 한도)·도급 공시로 대체
- `pf_dongyang_bucheon` — 공시(유상증자·주식근질권)로 대체
- `pf_hana_bucheon` — 공시 채권자 목록으로 대체
- `pf_bnk_bucheon` — 공시 채권자 목록으로 대체
- `pf_ibk_bucheon` — 공시 채권자 목록으로 대체
- `pf_hana_cap_bucheon` — 공시 채권자 목록으로 대체
- `pf_daewoo_fine_epc` — 대우건설 단일판매공급계약(2,525억) 공시로 대체
- `pf_daewoo_fine_guar` — 대우건설 채무보증결정(2,959억) 공시로 대체
- `pf_camsquare_first_to_pfv` — 감사보고서 Tr.A 약정 1,240억·실행 200.8억으로 대체
- `pf_magna_lender_ibk` — 마그나 2025 감사보고서 대주별 약정·실행액으로 대체
- `pf_magna_lender_hana_bank` — 마그나 2025 감사보고서 대주별 약정·실행액으로 대체
- `pf_magna_lender_nh_bank` — 마그나 2025 감사보고서 대주별 약정·실행액으로 대체
- `pf_magna_lender_kb_bank` — 마그나 2025 감사보고서 대주별 약정·실행액으로 대체
- `pf_magna_lender_shinhan_bank` — 마그나 2025 감사보고서 대주별 약정·실행액으로 대체
- `pf_magna_lender_hyundai_capital` — 마그나 2025 감사보고서 대주별 약정·실행액으로 대체
- `pf_magna_lender_shinhan_capital` — 마그나 2025 감사보고서 대주별 약정·실행액으로 대체
- `pf_magna_lender_hanwha_life` — 마그나 2025 감사보고서 대주별 약정·실행액으로 대체
- `pf_hana_sec_magna_arranger` — 원장 주선 관계로 대체
- `pf_gs_magna_parent` — 감사보고서 주주명부(51.39%)로 대체
- `pf_gs_magna_epc` — 감사보고서 도급액 1,783억(GMP)·책임준공으로 대체
- `pf_k1_magna_equity` — 감사보고서 주주명부로 대체
- `pf_hana_sec_magna_equity` — 감사보고서 주주명부로 대체

### 상태를 정정한 기존 관계
- `pf_yuanta_mountain` → repaid · 마운틴리치제일차의 케이스퀘어 대출(2024말 108억)은 2025 리파이낸싱으로 상환 — 매입확약도 종료된 것으로 봄
- `pf_kiwoom_refin` → unknown · 2025 리파이낸싱 실행(약정 3,800억) — 키움 잔여 보유분 미확인. Tr.B 케이더블유투금제사차(300억) 경유 가능성
- `pf_hyundai_camsquare_eq` → historical · 2025말 캄스퀘어안산PFV 주주명부에 현대건설 없음 — 과거 관계
- `pf_admin_camsquare_co` → unknown · 감사보고서 주주명부에 행정공제회 직접 지분 없음 — 보도된 1,300억은 펀드 경유로 추정
- `pf_cw_kr_funding` → assumption · 코어위브와 새마을금고중앙회 사이에 계약 관계 없음. 시나리오의 '자금시장 심리' 경로를 나타내는 가정 연결이며 직접 익스포저가 아님
- `pf_hana_sec_edgecore` →  · 2025 감사보고서에서 하나증권 주선 확인되지 않음 — 언론 보도로만 유지
- `pf_dl_bucheon_epc` →  · 서울파이낸스(2026-10)는 'DL건설' 수주로 표기 — 법인 표기 확인 필요
- `pf_samsung_sec_camsquare_equity` → unknown · 2025말 주주명부에 삼성증권 없음(특수관계자로만 기재) — 지분 보유 미확인

### 사업 메타데이터 정정
- `casequare_gasan` · construction_stage (under_construction → stabilized_operating) — 조사 단계 '운영 중 (2025 준공·운영 개시)'와 불일치
- `yeongdeungpo_yedc` · construction_stage (pre_construction → under_construction) — 조사 단계 '공사 중'와 불일치
- `yongin_jukjeon_pacific` · construction_stage (completed_permit → stabilized_operating) — 조사 단계 '운영 중 (IT 64MW / 수전 100MW, LG CNS 운영)'와 불일치
- `bucheon_samjeong_ai` · construction_stage (under_construction → pre_construction) — 조사 단계 '착공 전·PF 약정'와 불일치
- `keppel_ansan` · construction_stage (planned → pre_construction) — 조사 단계 '브릿지 단계 (본PF 전)'와 불일치
- `gasan_stt_seoul1` · construction_stage (planned → stabilized_operating) — 조사 단계 '운영 중 (2025 준공, 100% 책임임차 20+20년)'와 불일치
- `busan_ecodelta_dc` · construction_stage (planned → pre_construction) — 조사 단계 '토지 매입 단계 (본PF 전)'와 불일치
- `incheon_wonchang_dc` · construction_stage (planned → pre_construction) — 조사 단계 '브릿지 단계 (본PF 전)'와 불일치
- `bucheon_peach_dc` · construction_stage (planned → under_construction) — 조사 단계 '공사 중 (연면적 76,429㎡ · 지하4~지상6층)'와 불일치
- `gasan_dci_sel1` · construction_stage (planned → stabilized_operating) — 조사 단계 '운영 중 (2025 준공·코로케이션 개시)'와 불일치
- `gunsan_sgc_dc` · construction_stage (planned → pre_construction) — 조사 단계 '부지조성 (토지 PEF 매각·리스백 구조 추정)'와 불일치
- `donghae_gs_aidc` · construction_stage (planned → pre_construction) — 조사 단계 '전력인프라 공사 계약 (2028 준공 예정)'와 불일치
- `hanam_mkif_dc` · construction_stage (planned → stabilized_operating) — 조사 단계 '운영 중 (2023-11 준공, 수전 40MW / IT 25.44MW)'와 불일치
- `bupyeong_digital_edge` · construction_stage (planned → expanding) — 조사 단계 '1단계 운영·2단계(Phase II-1) 공사'와 불일치
- `goyang_samsong_dc` · construction_stage (planned → completed_permit) — 조사 단계 '준공 (2026-07 사용승인, 80MW)'와 불일치
- `pohang_ai_factory` · construction_stage (planned → pre_construction) — 조사 단계 'PF 약정 체결 (2026-09-23), 2027말 준공 목표 · 수전 40MW / IT 32MW'와 불일치
- `yongin_deokseong_dc` · construction_stage (planned → under_construction) — 조사 단계 '본PF 기표 예정→착공 (2026-05), 수전 80MW'와 불일치
- `incheon_dohwa_dc` · construction_stage (planned → pre_construction) — 조사 단계 '브릿지(2차 연장) · 본PF 주선 중 (80MW, 지상 7층)'와 불일치
- `hanam_edge_dc` · construction_stage (planned → under_construction) — 조사 단계 '공사 중 (2027-08 준공 목표, 10MW 이하)'와 불일치
- `incheon_bukhang_idc` · construction_stage (planned → pre_construction) — 조사 단계 '브릿지 (토지 확보, 도시계획변경·전력 확보 조건부)'와 불일치
- `gasan_edc_mastern` · construction_stage (planned → pre_construction) — 조사 단계 '브릿지 (9MW)'와 불일치
- `camsquare_ansan` · power_mw/power_note — 아워디씨(반월국가산단 엣지DC) 기사 내용이 잘못 매칭됨 — 별개 사업
- `casequare_gasan` · senior_debt_krw_b — 단위 표기 오류(값 3450는 억원인데 필드명은 십억원) · 화면 미사용 — 삭제, 금액은 공시 원장 관계(amount_krw_eok)로 대체
- `camsquare_ansan` · senior_debt_krw_b — 단위 표기 오류(값 8340는 억원인데 필드명은 십억원) · 화면 미사용 — 삭제, 금액은 공시 원장 관계(amount_krw_eok)로 대체
- `camsquare_ansan` · epc_krw_b — 단위 표기 오류(값 573.5는 억원인데 필드명은 십억원) · 화면 미사용 — 삭제, 금액은 공시 원장 관계(amount_krw_eok)로 대체

## 6. 미확인 · 자료 상충 · 추가 확인 필요

| 사업 | 구분 | 내용 |
|---|---|---|
| camsquare_ansan | 자료 상충 | 언론(아시아경제 2024-11)은 대한지방행정공제회 1,300억 '에쿼티'로 보도. 2025 감사보고서 주주명부에 행정공제회 직접 지분 없음 — KAAM2호 펀드(보통주 1,050억 + 일반자금 1,360억) 수익자로 참여했을 가능성. 펀드 수익자 명단 비공개 → 투자 경로 미공개로 표시. |
| camsquare_ansan | 자료 상충 | 언론(딜사이트TV 2024-12)은 본PF 8,340억·삼성증권 신용보강 6,800억 보도. 감사보고서 약정한도 합계 9,700억(일반자금 1,360 포함)과 본PF(Tr.A~C) 8,340억은 일치. 삼성증권 신용보강 6,800억은 유동화 SPC 대상 한도로 보이나 캄스퀘어제일차의 Tr.A 약정은 1,240억뿐 — 대상 범위 미확인. |
| camsquare_ansan | 과거 관계 | 기존 데이터의 '현대건설 지분 50억'은 2025말 주주명부에 없음 → 과거 관계(현재 미보유)로 상태 변경. |
| casequare_gasan | 자료 상충 | 딜사이트(2024-07) 대주별 금액(동양생명 70억 등)과 2024말 감사보고서 잔액(동양생명 300억 등)이 다름 — 보도는 일부 트랜치 또는 특정 시점 기준으로 보임. 감사보고서 수치를 우선 표시, 기사 수치는 과거 보도치로 보존. |
| casequare_gasan | 날짜 확인 | 감사보고서의 준공·사용승인일 '2026-06-25' 표기 확인 필요(2025년 감가상각 개시와 불일치). |
| casequare_gasan | 미확인 | 케이더블유투금제사차의 신용보강(매입확약) 제공자 · 투자자 공시 미확인. |
| keppel_ansan | 현재 상태 미확인 | 브릿지 만기(2026-09-29) 이후 본PF 약정·대주단 공시 미확인. 2026-06 케펠 펀드 증자로 최대주주 변경 추정. |
| keppel_ansan | 프로젝트 식별 | dc.namepf 인허가 'Arclight'(원시동 726-4)와 주소 일치 → 동일 사업장으로 연결. |
| koramco_siheung_dc | 자료 상충 | 감사보고서 차입금 표는 NH농협은행 50억·SH수협은행 100억, 약정 주석은 '고양축산업협동조합 등과 150억 대출약정'으로 기재 — 대주 명칭 불일치. 상환 완료된 과거 관계로만 표시. |
| koramco_siheung_dc | 프로젝트 식별 | 기존 연구 대기열의 '안산 코람코·DCI' 클러스터. 캄스퀘어 안산(성곡동 670-4)과 다른 필지 — 병합 금지. |
| gasan_stt_seoul1 | 미확인 | 100% 책임임차(Master Lease, 20+20년, Triple Net) 임차인 명칭이 감사보고서에 없음. STT GDC(효성 합작) 추정은 공시로 미확인 — 임차 관계 미등록. |
| incheon_wonchang_dc | 미확인 | 연구 대기열의 '신한은행·현대엔지니어링' 참여는 감사보고서에서 확인되지 않음 — 미등록. |
| None | 제외 | 천안제이디씨피에프브이: 감사보고서상 천안테크노파크 '물류센터' 개발사업, 2024-03 용지계약 해제·조기청산 예정 → 데이터센터 아님, 미등록. |
| bucheon_peach_dc | 만기 도래 | 본PF 만기 2026-10-20 (2025말 전액 유동성대체). 연장·리파이낸싱 여부 공시 미확인 — 현재 상태 미확인. |
| bucheon_peach_dc | 미확인 | 시공사·임차인이 감사보고서에 기재되지 않음. 정관 목적은 '물류센터 및 기타' 이나 사업개요는 '데이터센터 개발사업'. |
| bucheon_peach_dc | 프로젝트 식별 | 부천 삼정동 48-59(유진 디씨아이티와이부천PFV)와 13-15(퍼시픽피치PFV)는 별개 사업 — 병합 금지. |
| yeongdeungpo_yedc | 자료 상충 | 기존 데이터의 '하나증권 주선'(아시아경제 2024-11)은 2025 감사보고서에서 확인되지 않음 — 언론 보도로만 유지. |
| anseong_rec_dc | 분류 | 한화그룹 자체 데이터센터 — 그룹 계열 시행법인의 PF(주식 근질권)로 조달. 외부 임차형 AIDC 여부 미확인. |
| anseong_rec_dc | 미확인 | 대주단 전체 명단·주관사·시공사(건축) 공시 미확인. |
| gasan_dci_sel1 | 미확인 | 코로케이션 임차인(운용리스 3,919억) 명칭 공시 미기재. |
| gunsan_sgc_dc | 미확인 | PEF(에스지씨한국투자제1호) 출자자·GP, 본공사 금융조달 공시 미확인. |
| donghae_gs_aidc | 분류 | 자기자본 조달 — PF 사업 아님. 임차인·외부 금융 미확인. |
| gwangju_fine_dc | 미확인 | 파인디씨PFV 감사보고서 DART 미검색(외감 대상 전). 하나은행·KB국민은행 외 대주('등')와 기관별 금액 미공개. |
| camsquare_yongin | 자료 상충 | 기존 데이터(딜사이트)는 한화투자증권 530억·SK증권 70억 직접 대출로 표시. 딜북(2026-02-06)은 '한화투자증권 SPC 380억(선순위)·SK증권 SPC 70억(후순위)', 선순위 총 530억 중 150억 대주 미공개 → 기존 직접대출 엣지는 SPC 경유 관계로 대체하고 '선순위 잔여 150억 대주 미공개'로 기록. |
| hanam_mkif_dc | 프로젝트 식별 | 하남 풍산동에는 607-2(MKIF), 610(IBK 하남), 595(용도변경 AI DC), 하남엣지센터PFV(물류센터 전환) 등 복수 사업 — 주소별로 분리 유지. |
| yongin_jukjeon_pacific | 미확인 | 시행 SPC 법인명 DART 미확인('퍼시픽써니관련시행SPC'는 기존 데이터의 가칭) — 8,280억의 지분/대출 구분·대주단 미공개. |
| bupyeong_digital_edge | 자료 상충 | 언론의 'SK에코플랜트 49 : 디지털엣지 51' 지분과 디씨케이원 주주명부(Digital Edge Developments 100%)가 다름 — 상위 단계 지분으로 추정. |
| bupyeong_digital_edge | 미확인 | SK에코플랜트 시공·책임준공 여부 감사보고서 미기재. 부평 'ESR/STACK' 별도 사업과 병합하지 않음. |
| goyang_samsong_dc | 미확인 | 펀드명·대주단·출자자 공시 미확인 (연구 대기열의 '네이버클라우드' 참여 근거 미발견). |
| pohang_ai_factory | 미확인 | 시행 SPC 명칭·출자자(자기자본 1,500억)·대주단 전체 명단·기관별 금액 미공개. 우리은행·KB국민은행의 대출 참여액 미공개(주선만 확인). |
| yongin_deokseong_dc | 미확인 | 국민연금·교직원공제회 투자, KT클라우드 선임차 보도는 신뢰도 확인이 어려운 매체 — 미등록(추가 확인 대상). |
| yongin_deokseong_dc | 미확인 | 케이클라비스용인덕성피에프브이제25호(DART 법인)와의 관계 미확인 — 별도 사업 가능성. |
| incheon_dohwa_dc | 미확인 | IB토마토는 IBK투자증권의 도화동 관련 우발채무(브릿지 매입확약 등)를 다뤘으나 금액·구조는 기사 원문 확인 필요. 하나증권·현대차증권 공동주관설은 검색 발췌로만 확인 → 미등록. |
| hanam_edge_dc | 미확인 | 삼성생명·삼성SRA자산운용 사업주체설은 유료 기사 발췌로만 확인 → 미등록. 대주단·책임준공 조건 미공개. |
| incheon_bukhang_idc | 프로젝트 식별 | 원창동 청라아이디씨PFV(381-73, 이도)와 북항아이디씨PFV(HJ중공업)는 별개 사업 — 병합 금지. |
| incheon_bukhang_idc | 부분 확인 | 단기차입금 합계 1,288억 중 감사보고서에서 행 단위로 확인한 대주는 776억 — 나머지 대주 행 재확인 필요. |
| guro_gaebong_dc | 현재 상태 미확인 | 2025 감사보고서상 이익잉여금 흑자 전환·차입 상환 — 사업지 매각 가능성. 매수자·현재 시행 주체 확인 필요. |
| bucheon_samjeong_ai | 자료 상충 | 시공사 표기: 이데일리(기존)=DL이앤씨, 서울파이낸스(2026-10)='DL건설 1,268억 수주' — 동일 계약의 법인 표기 차이 확인 필요. |
| bundang_hostway_idc | 프로젝트 식별 | 기사상 자산 소재지는 '경기도 용인시 수지구' — 명칭(분당 IDC)과 행정구역이 다름. 매매가·인수금융 대주 미공개. |

## 7. 데이터 검증 결과

`python scripts/validate_kr_dc_v6.py` → **PASSED** (29/29 검사 통과)

- 통과 · edge endpoints exist
- 통과 · unique edge ids
- 통과 · unique node ids
- 통과 · every v6 relation has a source
- 통과 · every v6 relation has a URL
- 통과 · no zero placeholder amounts
- 통과 · commitment sum ('camsquare_ansan', 'main_pf')
- 통과 · commitment sum ('casequare_gasan', 'refinancing')
- 통과 · commitment sum ('magna_deogi', 'refinancing')
- 통과 · commitment sum ('bucheon_peach_dc', 'main_pf')
- 통과 · commitment sum ('bupyeong_digital_edge', 'refinancing')
- 통과 · commitment sum ('gasan_stt_seoul1', 'refinancing')
- 통과 · commitment sum ('yeongdeungpo_yedc', 'main_pf')
- 통과 · commitment sum ('hanam_mkif_dc', 'refinancing')
- 통과 · drawn sum ('camsquare_ansan', 'main_pf')
- 통과 · drawn sum ('casequare_gasan', 'refinancing')
- 통과 · drawn sum ('magna_deogi', 'refinancing')
- 통과 · drawn sum ('bucheon_peach_dc', 'main_pf')
- 통과 · drawn sum ('bupyeong_digital_edge', 'refinancing')
- 통과 · drawn sum ('yeongdeungpo_yedc', 'main_pf')
- 통과 · arranger amounts typed as context/fee
- 통과 · no syndicate total copied to each lender
- 통과 · repaid relations use historical amount types
- 통과 · no receivable typed as contract value
- 통과 · contingent obligations have trigger
- 통과 · no factual CoreWeave–Korea PF edge
- 통과 · v6 relations attach to vehicle/borrower (no peer-to-peer)
- 통과 · distinct projects kept separate
- 통과 · hidden nodes not on map

## 8. 실행 방법

```bat
rem Windows — 기존과 동일
start.bat            & rem 백엔드(:8000) + 프런트(:5173)
preview.bat          & rem 서버 없이 정적 미리보기(:4173)
```

데이터를 다시 만들 때 (원장 수정 후):

```bash
python scripts/build_kr_dc_v6.py      # v5 기준본(scripts/data/pf_v5_baseline) + 조사 원장 → frontend/public/data/pf/*
python scripts/validate_kr_dc_v6.py   # 금액 합계·중복 배분·참조 무결성·표시 규칙 검사
python scripts/validate_pf_finance_v5.py
python scripts/report_kr_dc_v6.py     # 이 문서 재생성
```

앱에서 보는 법: 상단 `AI DATA CENTER PF` → 좌측 '확인된 사업'에서 사업 클릭(참여자·금융 이력·미확인 사항), 회사 클릭(참여 사업·역할·조건부 의무·같은 사업의 간접 상대방), 관계선·관계 행 클릭(쉬운 설명·근거·공시 접수번호·원문 인용). 좌측 필터(기관 유형·금융 단계·투자·신용 경로·근거·상태)는 목록과 3D 지도에 함께 적용됩니다. `Data & Sources` 화면에 기업별 조사 상태와 미확인 목록이 있습니다.

OpenDART API 키는 조사 중 조회에만 사용했고 코드·데이터·이 저장소 어디에도 저장하지 않았습니다.

