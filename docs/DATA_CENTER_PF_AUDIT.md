# DATA CENTER PF AUDIT

**Verification date:** 2026-10-21
**Audit complete:** NO (partial — see limitations)
**OpenDART API configured:** yes
**Filings inspected (live):** 0
**Network:** 311 nodes / 497 edges · projects file: 173

## Securities firms reviewed (mandatory list)

| Firm | In map | Node | Edges | Active economic | Arranger-only | Historical/repaid |
|---|---|---|---:|---:|---:|---:|
| 한국투자증권 | Y | korea_inv_sec | 6 | 3 | 3 | 0 |
| KB증권 | Y | kb_sec | 4 | 1 | 3 | 0 |
| 메리츠증권 | Y | meritz_sec | 1 | 0 | 1 | 0 |
| NH투자증권 | Y | nh_inv_sec | 6 | 3 | 3 | 0 |
| 미래에셋증권 | Y | mirae_asset_sec | 0 | 0 | 0 | 0 |
| 삼성증권 | Y | samsung_sec | 6 | 2 | 4 | 0 |
| 신한투자증권 | Y | shinhan_sec | 8 | 7 | 1 | 0 |
| 하나증권 | Y | hana_sec | 4 | 1 | 3 | 0 |
| 대신증권 | Y | daishin_sec | 0 | 0 | 0 | 0 |
| 키움증권 | Y | kiwoom_sec | 3 | 1 | 2 | 0 |
| IBK투자증권 | Y | ibk_sec | 3 | 2 | 1 | 0 |
| 현대차증권 | Y | hyundai_motor_sec | 5 | 2 | 3 | 0 |
| SK증권 | Y | sk_sec | 1 | 0 | 1 | 0 |
| 교보증권 | Y | kyobo_sec | 1 | 0 | 1 | 0 |
| 유안타증권 | Y | yuanta_sec | 2 | 0 | 2 | 0 |
| 한화투자증권 | Y | hanwha_inv_sec | 3 | 2 | 1 | 0 |
| 다올투자증권 | Y | daol_sec | 1 | 0 | 1 | 0 |
| LS증권 | Y | ls_sec | 1 | 1 | 0 | 0 |
| 신영증권 | Y | shinyoung_sec | 0 | 0 | 0 | 0 |
| DB증권 | Y | db_sec | 0 | 0 | 0 | 0 |
| 유진투자증권 | Y | eugene_inv_sec | 3 | 2 | 1 | 0 |
| iM증권 | Y | im_sec | 0 | 0 | 0 | 0 |
| BNK투자증권 | Y | bnk_sec | 0 | 0 | 0 | 0 |
| 부국증권 | Y | bookook_sec | 0 | 0 | 0 | 0 |
| 케이프투자증권 | Y | cape_sec | 0 | 0 | 0 | 0 |

## Classification rules applied

- Arranger / underwriting / facility_total_context → **not** current credit exposure; `shock_eligible=false`.
- `repaid` / `terminated` / `historical` → FULLY_REPAID or HISTORICAL_ONLY; excluded from loss propagation.
- Missing outstanding balance → ACTIVE_AMOUNT_UNKNOWN or UNVERIFIED; never invent 0 or market-share fill.

## Confirmed active economic relationships (map metadata): 27

- **한국투자증권** · EQUITY_INVESTMENT · 미확인 · status=ACTIVE_AMOUNT_UNKNOWN · project=guro_gaebong_dc · edge=`v6_gr_eq_korea_inv_sec`
- **한국투자증권** · EQUITY_INVESTMENT · 9.5억 · status=ACTIVE_CONFIRMED · project=capstone_meta_idc · edge=`dart_eq_korea_inv_sec_capstone_meta`
- **한국투자증권** · EQUITY_INVESTMENT · 28.22억 · status=ACTIVE_CONFIRMED · project=None · edge=`dart_eq_kis_value_dc_fund`
- **KB증권** · CORPORATE_LOAN · 미확인 · status=ACTIVE_AMOUNT_UNKNOWN · project=gasan_stt_seoul1 · edge=`v6_hs_loan_kb_sec`
- **NH투자증권** · EQUITY_INVESTMENT · 100.0억 · status=ACTIVE_AMOUNT_UNKNOWN · project=keppel_ansan · edge=`v6_kp_capinc_nh_inv_sec`
- **NH투자증권** · EQUITY_INVESTMENT · 미확인 · status=ACTIVE_AMOUNT_UNKNOWN · project=gasan_stt_seoul1 · edge=`v6_glm_eq_nh_inv_sec`
- **NH투자증권** · PROJECT_LOAN · 1350억 · status=ACTIVE_CONFIRMED · project=gasan_dci_sel1 · edge=`v6_gj_loan_nh_inv_sec`
- **삼성증권** · CREDIT_ENHANCEMENT · 6800.0억 · status=ACTIVE_AMOUNT_UNKNOWN · project=camsquare_ansan · edge=`pf_samsung_camsquare_abstb_support`
- **삼성증권** · EQUITY_INVESTMENT · 미확인 · status=ACTIVE_AMOUNT_UNKNOWN · project=camsquare_ansan · edge=`pf_samsung_sec_camsquare_equity`
- **신한투자증권** · EQUITY_SPONSOR · 미확인 · status=ACTIVE_AMOUNT_UNKNOWN · project=yongin_jukjeon_pacific · edge=`pf_shinhan_jukjeon_eq`
- **신한투자증권** · EQUITY_INVESTMENT · 미확인 · status=ACTIVE_AMOUNT_UNKNOWN · project=keppel_ansan · edge=`v6_kp_eq_shinhan_sec`
- **신한투자증권** · PROJECT_LOAN · 60억 · status=ACTIVE_CONFIRMED · project=keppel_ansan · edge=`v6_kp_bridge_shinhan_sec`
- **신한투자증권** · PROJECT_LOAN · 200억 · status=ACTIVE_CONFIRMED · project=incheon_wonchang_dc · edge=`v6_cn_bridge_shinhan_sec`
- **신한투자증권** · PROJECT_LOAN · 100억 · status=ACTIVE_CONFIRMED · project=bucheon_peach_dc · edge=`v6_pc_B_shinhan_sec`
- **신한투자증권** · EQUITY_INVESTMENT · 110.5억 · status=ACTIVE_AMOUNT_UNKNOWN · project=bucheon_peach_dc · edge=`v6_pc_eq_shinhan_sec`
- **신한투자증권** · LIQUIDITY_COMMITMENT · 71.0억 · status=ACTIVE_AMOUNT_UNKNOWN · project=None · edge=`dart_commit_shinhan_dc_fund`
- **하나증권** · EQUITY_INVESTMENT · 미확인 · status=ACTIVE_AMOUNT_UNKNOWN · project=magna_deogi · edge=`v6_mg_eq_hana_sec`
- **키움증권** · EQUITY_INVESTMENT · 미확인 · status=ACTIVE_AMOUNT_UNKNOWN · project=casequare_busan_jangnim · edge=`dart_eq_kiwoom_casequare_jangnim`
- **IBK투자증권** · EQUITY_INVESTMENT · 17.85억 · status=ACTIVE_CONFIRMED · project=busan_ecodelta_dc · edge=`v6_bed_eq_ibk_sec`
- **IBK투자증권** · EQUITY_INVESTMENT · 9.5억 · status=ACTIVE_CONFIRMED · project=capstone_meta_idc · edge=`dart_eq_ibk_sec_capstone_meta`
- **현대차증권** · LIQUIDITY_COMMITMENT · 30.0억 · status=ACTIVE_AMOUNT_UNKNOWN · project=None · edge=`dart_commit_hyundai_fine_dc_fund`
- **현대차증권** · EQUITY_INVESTMENT · 미확인 · status=ACTIVE_AMOUNT_UNKNOWN · project=casequare_yongsan · edge=`dart_rel_hyundai_casequare_yongsan`
- **한화투자증권** · EQUITY_INVESTMENT · 29.95억 · status=ACTIVE_CONFIRMED · project=camsquare_seori · edge=`dart_eq_hanwha_camsquare_seori`
- **한화투자증권** · LIQUIDITY_COMMITMENT · 280.0억 · status=ACTIVE_AMOUNT_UNKNOWN · project=yongin_jigok_dc · edge=`dart_commit_hanwha_yongin_jigok`
- **LS증권** · ABS_HOLDING · 미확인 · status=ACTIVE_AMOUNT_UNKNOWN · project=camsquare_ansan · edge=`dart_bond_ls_camsquare_ansan`
- **유진투자증권** · EQUITY_INVESTMENT · 15억 · status=ACTIVE_CONFIRMED · project=camsquare_ansan · edge=`v6_ka_eq_eugene`
- **유진투자증권** · EQUITY_INVESTMENT · 5.0억 · status=ACTIVE_CONFIRMED · project=casequare_manus_guro · edge=`dart_eq_eugene_casequare_manus_guro`

## Historical / arranger (informational): 31
## Unknown balances flagged: 10
## Missing from map (no node): 0

## Additional securities already in map
- 우리투자증권 (`woori_inv_sec`)
- 신한데이터센터개발일반사모혼합자산투자신탁 (`shinhan_dc_dev_fund`)
- 한국밸류K-리더스데이터센터일반사모투자신탁 (`korea_value_dc_fund`)
- 파인앤파트너스데이터센터개발블라인드펀드 (`fine_partners_dc_fund`)

## Limitations

- OPEN_DART_API_KEY unset or empty → live DART full-text / notes search not executed this run.
- Existing edges remain news/DART-metadata sourced; arrangement amounts are tagged HISTORICAL_ONLY / shock_eligible=false.
- Absence from latest disclosure is NOT treated as repayment (Case E → UNVERIFIED).
- No fabricated lender shares from facility totals.

## Remaining work

- Set OPEN_DART_API_KEY and run disclosure keyword crawl for all 25+ firms (2018–latest).
- Reconcile bridge→mortgage refinancing successor creditors with explicit evidence.
- Cross-check borrower/SPC filings for each ACTIVE_AMOUNT_UNKNOWN loan.
- Investigate missing firms: (none)

## Machine-readable evidence

- `docs/DATA_CENTER_PF_AUDIT.json`
- `docs/pf_exposure_evidence.json` (per-edge source links after normalize_exposure_status.py)



## OpenDART lead integration v1 (applied to graph)

- Date: 2026-10-21
- Added nodes: 11 · Added edges: 14 · Updated edges: 1 · Added projects: 8
- Detail: docs/opendart_integration_v1.json

### Newly verified / updated active relationships
- IBK투자증권 → 부산에코델타 PFV 출자 18.2% / 17.85억 (DART 2026.06) — updated
- IBK·한국투자증권 → 캡스톤메타IDC PFV 각 19% / 9.5억
- 한화투자증권 → 캄스퀘어서리 PFV 60% / 29.95억
- 유진투자증권 → 케이스퀘어마누스구로 PFV 10% / 5억
- 키움증권 → 케이스퀘어부산장림 PFV (관계회사, 금액 미확인)
- 한화 → 용인지곡동 DC 매입확약 280억 (조건부, 대출원금 아님)
- 신한 → DC개발펀드 매입약정 71억 · 현대차증권 → 파인앤파트너스 DC펀드 30억
- LS → 캄스퀘어안산 사모사채 약정 (금액 미확인)
- 한국투자 → K-리더스 DC펀드 15% / 28.22억

### Terminated / informational (no current loan-loss path)
- KB증권 케이스퀘어에코송파 출자 처분완료 (잔액 0)
- 유안타 안산캄스퀘어 유동화 주선 (facility context ≠ 보유)
- 하나데이터센터제일차 지분 0% 도관
- 현대차 케이스퀘어용산 UNVERIFIED

### Explicitly not added
- NH투자증권 AI 데이터센터 IB 서술 (관계 아님)
- 키움 구조화금융 일반 Track Record 서술
- 교보데이터센터→교보정보통신 합병 역사 (현재 DC PF 아님)
- 다올 케이스퀘어세종물류 (물류 PFV — DC 아님, 미반영)

---

## Borrower-28 follow-up (2026-10-22)

상세: [`docs/BORROWER28_AUDIT.md`](docs/BORROWER28_AUDIT.md) · 원본 JSON: `docs/opendart_borrower28_*.json`

- 28개 시드 차주 OpenDART 법인·공시 제목·감사보고서 본문 키워드 스캔 완료
- 네트워크: 시드 노드 5개 추가(`gaya_pfv` 등), 기존 15개에 `dart_corp_code`·감사보고서 출처 부착
- **금융 엣지 자동 추가 0건** — 본문 키워드 동시출현만으로 잔액/대주를 확정하지 않음
- 충격 적격 엣지 수 유지(248) — 쇼크 엔진 변경 없음
- UI: 좌측 “예정·과거·상환” 필터 및 범례의 과거사례 안내 문구 삭제
- 맵: 동일 토폴로지 재레이아웃 방지, 조작 중 DPR/라벨 완화, 시점 복구 버튼

