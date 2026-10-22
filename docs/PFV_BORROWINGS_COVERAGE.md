# PFV/SPC Borrowings Coverage

- Verification date: **2026-10-22**
- Inventory: **66** entities (visible + hidden + unresolved seeds)
- Status counts: `{"Report unavailable": 44, "Reviewed and mapped": 20, "Reviewed — no outstanding borrowings disclosed": 2}`

## Critical correction — 안산그린에너지피에프브이

Previously mis-labeled as “no outstanding borrowings.” Audit `20260406003916` 주석5 장기차입금 discloses **당기말 104,000,000천원 (1,040억)** across **17 named lenders**. Pipeline failure: note never written to `network.json` + false hard-coded coverage status. Now mapped as `dart_loan_*_ansan_green_*`. Row-by-row: `docs/ansan_green_borrowings_reconciliation.json`. Source sweep: `docs/pfv_source_vs_graph_audit.json`.

| PFV/SPC | Latest report | Reporting date | Note reviewed | Named lenders (current) | Mapped relationships | Status | Gaps |
|---|---|---|---|---|---|---|---|
| 에이원브리즈 (`a1_breeze`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 에이원리빙 (`a1_living`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 안산그린에너지피에프브이 (`ansan_green_energy_pfv`) | 안산그린에너지피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | kb_capital (57.7778억), nh_inv_sec (11.5556억), thek_savings (11.5556억), nh_federation (231.1111억), hana_alt_geongungoong_1 (11.5556억), nh_inv_sec (11.5556억), fund_kb_re_loan_pe2 (80.8889억), db_ins (231.1111억) …(+9) | 17 | Reviewed and mapped | — |
| APLD ELN-01 LLC (`apld_eln_01`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| APLD HPC Holdings LLC (`apld_hpc_holdings`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 블루드래곤제칠차 (`blue_dragon7_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 블루리본디벨롭먼트 (`blueribbon_dev`) | 감사보고서 (2025.12) | — | Y | — | 0 | Reviewed — no outstanding borrowings disclosed | — |
| 부천공간제일차 (`bucheon_space1_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 북항아이디씨피에프브이 (`bukhang_idc_pfv`) | 북항아이디씨피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | hj_heavy (248.0억), a1_breeze (129.0억), icecream_media (50.0억), a1_living (80.0억), the_ym_korea (5.0억), meritz_fire (258.0억), meritz_capital (258.0억), jt_savings (30.0억) …(+4) | 12 | Reviewed and mapped | — |
| 부산에코델타그린데이터센터피에프브이 (`busan_ecodelta_pfv`) | 부산에코델타그린데이터센터피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | ibk_capital (202.1373억) | 1 | Reviewed and mapped | — |
| 캄스퀘어제일차 (`camsquare_first_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 캄스퀘어안산데이터센터PFV (`camsquare_pfv`) | 캄스퀘어안산데이터센터피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | camsquare_first_spc (200.8억), hyundai_capital (162.0억), kb_ins (113.4억), military_mutual (113.4억), db_life (81.0억), yk_ansan_d1 (37.3억), kb_capital (48.6억), woori_finance_capital (48.6억) …(+4) | 12 | Reviewed and mapped | — |
| 캄스퀘어제이차 (`camsquare_second_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 캄스퀘어서리데이터센터PFV (`camsquare_seori_pfv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 캄스퀘어제삼차 (`camsquare_third_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 캄스퀘어용인데이터센터PFV (`camsquare_yongin_pfv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 캡스톤메타IDC피에프브이 (`capstone_meta_idc_pfv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 케이스퀘어부산장림데이터센터피에프브이 (`casequare_busan_jangnim_pfv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 케이스퀘어에코송파피에프브이 (`casequare_eco_songpa_pfv`) | 케이스퀘어에코송파피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | astom_1st_spc (420.0억), suhyup_bank (500.0억), korea_inv_sec (100.0억), nh_life (300.0억), shinhan_capital (50.0억), frenchshine_1st_spc (100.0억), korea_inv_capital (200.0억), kb_sec (150.0억) …(+3) | 11 | Reviewed and mapped | — |
| 케이스퀘어마누스데이터센터구로피에프브이 (`casequare_manus_guro_pfv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 케이스퀘어데이터센터PFV (`casequare_pfv`) | 케이스퀘어데이터센터피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | kyobo_life (492.0억), kyobo_life (492.0억), hana_bank (296.0억), samsung_fire (836.0억), hanwha_life (983.0억), thek_savings (99.0억), shinhan_capital (198.0억), bluecorner_capital (50.0억) …(+1) | 9 | Reviewed and mapped | — |
| 케이스퀘어용산피에프브이 (`casequare_yongsan_pfv`) | 케이스퀘어용산피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | bnk_sum_23rd_spc (1900.0억), welcome_savings (120.0억), incheon_savings (50.0억), samjung_savings (70.0억), osb_savings (100.0억), minguk_savings (20.0억), geumhwa_savings (40.0억), namyang_savings (50.0억) …(+24) | 32 | Reviewed and mapped | — |
| 청라아이디씨피에프브이 (`cheongna_idc_pfv`) | 청라아이디씨피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | shinhan_capital (290.0억), shinhan_sec (200.0억), wonchang_idc (100.0억), gps23_spc (310.0억), ido (50.0억), ido (232.396억) | 6 | Reviewed and mapped | — |
| 코어사이언티픽 Finance I (`corz_finance_i`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 디씨아이티와이부천피에프브이 (`dcity_bucheon_pfv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 디씨아이티와이인천피에프브이 (`dcity_incheon_pfv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 디씨케이원 (`dck1`) | 디씨케이원 감사보고서 (2025.12) | 2025-12-31 | Y | ibk_bank (1100.0억), kdb (1100.0억), db_ins (715.0억), hyundai_marine (275.0억), kb_ins (247.5억), kb_bank (192.5억), ibk_capital (137.5억), ing_bank (357.5억) …(+10) | 18 | Reviewed and mapped | — |
| 디토피에프브이 (`dito_pfv`) | 디토피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | ibk_bank (1500.0억), kdb (1000.0억), ibk_bank (250.0억) | 3 | Reviewed and mapped | — |
| 동해에이아이제3캠퍼스 (`donghae_ai_campus3`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 엣지코어피에프브이 (`edgecore_pfv`) | 엣지코어피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | kb_ins (207.0억), hyundai_marine (76.0억), msedc1_spc (37.0억), msedc2_spc (500.0억) | 4 | Reviewed and mapped | — |
| 에포크피에프브이 (`epoch_pfv`) | 에포크피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | ibk_bank (1200.0억), kdb (425.0억), kb_bank (300.0억), woori_bank (425.0억), hana_bank (425.0억), nh_bank (425.0억), ibk_bank (265.0억) | 7 | Reviewed and mapped | — |
| 파인디씨피에프브이 (`fine_dc_pfv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 갤럭시 Helios II (`galaxy_helios_ii`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 가온해제오차 (`gaon_haeje5_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 가산디씨제이브이 (`gasan_dc_jv`) | 가산디씨제이브이 감사보고서 (2025.12) | 2025-12-31 | Y | bnp_paribas (500.0억), mufg (500.0억), ca_cib (650.0억), nh_inv_sec (1350.0억) | 4 | Reviewed and mapped | — |
| 가산디씨에스엘원 (`gasan_dc_sl1`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 가산-eDC 시행법인(명칭 미공개) (`gasan_edc_spv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 가산랜드마크데이터센터피에프브이 (`gasan_landmark_pfv`) | 가산랜드마크데이터센터피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | kdb (1000.0억), im_bank (300.0억), kb_bank (200.0억), bnk_kyongnam (200.0억), hana_bank (200.0억), suhyup_bank (100.0억) | 6 | Reviewed and mapped | — |
| 가야피에프브이 (`gaya_pfv`) | 가야피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | kb_bank (1190.0억), ubob_seoul (795.0억), hyundai_marine (100.0억), hyundai_marine (300.0억) | 4 | Reviewed and mapped | — |
| 쥐피에스23제일차 (`gps23_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 그린디지털인프라 (`green_digital_infra`) | 그린디지털인프라 감사보고서 (2025.12) | 2025-12-31 | Y | kb_bank (800.0억), kyobo_life (1500.0억), shinhan_bank (1000.0억), hyundai_marine (300.0억), kb_ins (400.0억), kb_bank (200.0억), kyobo_life (500.0억), hyundai_marine (150.0억) …(+2) | 10 | Reviewed and mapped | — |
| 하나데이터센터제일차 (`hana_dc_1st_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 하남엣지센터피에프브이 (`hanam_edge_pfv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 한화투자증권 SPC(명칭 미공개) (`hanwha_sec_spc_yongin`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 케펠데이터센터안산피에프브이 (`keppel_ansan_pfv`) | 케펠데이터센터안산피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | shinhan_capital (50.0억), shinhan_sec (60.0억), shinyoung (210.0억) | 3 | Reviewed and mapped | — |
| 코람코시화데이터센터피에프브이 (`koramco_siheung_pfv`) | 감사보고서 (2025.12) | — | Y | — | 0 | Reviewed — no outstanding borrowings disclosed | — |
| 케이더블유투금제사차 (`kw_tg4_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 마그나피에프브이 (`magna_pfv`) | 마그나피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | kb_bank (99.0억), shinhan_bank (134.0억), hana_bank (83.0억), ibk_bank (99.0억), hanwha_life (232.0억) | 5 | Reviewed and mapped | — |
| 마운틴리치제일차 (`mountain_rich`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 엠에스이디씨제일차 (`msedc1_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 엠에스이디씨제이차 (`msedc2_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 퍼시픽써니 시행 SPC(법인명 미확인) (`pacific_sunny_spv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 퍼시픽피치피에프브이 (`peach_pfv`) | 퍼시픽피치피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | ibk_bank (258.3억), hyundai_capital (155.0억), hana_capital (25.8억), db_ins (206.6억), heungkuk_fire (129.1억), kdb (258.3억), kb_capital (51.7억), bccard (51.7억) …(+10) | 18 | Reviewed and mapped | — |
| 포항 AI Factory 시행법인(명칭 미공개) (`pohang_aif_spc`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 알이씨데이터센터 (`rec_datacenter`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 더엣지영등포피에프브이(주) (`seed:b04`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 신영식사피에프브이(주) (`seed:b11`) | 감사보고서 (2020.12) | — | N | — | 0 | Report unavailable | — |
| 아이비케이부산에이아이데이터센터(주) (`seed:b12`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 에이아이팩토리포항피에프브이(주) (`seed:b14`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 케이인더스트리피에프브이(주) (`seed:b19`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 하양에너지발전(주) (`seed:b28`) | 하양에너지발전 감사보고서 (2025.12) | 2025-12-31 | Y | — | 0 | Report unavailable | 주석6 당기말 단기차입금 44.5억(관련당사자) 확인했으나 DC PFV 미확정·맵 노드 없음(visibility=no_map_node) |
| 신영문봉피에프브이 (`shinyoung_munbong_pfv`) | 신영문봉피에프브이 감사보고서 (2025.12) | 2025-12-31 | Y | bdh_1st_spc (200.0억), kis_savings (120.0억), louis_alpha_1st_spc (60.0억), goryo_savings (90.0억), seram_savings (20.0억), db_capital (50.0억), welcome_savings (30.0억), kiwoom_fni (40.0억) …(+4) | 12 | Reviewed and mapped | — |
| SK증권 SPC(명칭 미공개) (`sk_sec_spc_yongin`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 와이케이안산디원 (`yk_ansan_d1`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 용인덕성데이터센터피에프브이 (`yongin_deokseong_pfv`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
| 용인지곡동데이터센터(브릿지 참조) (`yongin_jigok_dc_bridge_ref`) | — | — | N | — | 0 | Report unavailable | DART 감사/정기보고서 rcept 미확보 또는 비대상(해외·미공개법인) |
