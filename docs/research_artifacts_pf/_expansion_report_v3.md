# Company-only PF map expansion (v3)

**Graph:** 197 company nodes · 71 edges · 0 facility/permit/aggregate nodes

## Companies added (by role)

### Securities / arranger / lender
| Company | ID | Listing | Status |
|---------|-----|---------|--------|
| 한화투자증권 | `hanwha_inv_sec` | 003530 KRX | 관계 확인 |

### CSP / cloud / telecom-operator
| Company | ID | Listing | Status |
|---------|-----|---------|--------|
| LG유플러스 | `lg_uplus` | 032640 KRX | 관계 확인 (위탁운영) |
| 네이버클라우드 | `naver_cloud` | 비상장 | 연결관계 확인 필요 |
| NHN클라우드 | `nhn_cloud` | 비상장 | 연결관계 확인 필요 |
| KINX | `kinx` | 053110 KRX | 연결관계 확인 필요 |
| 가비아 | `gabia` | 079940 KRX | 연결관계 확인 필요 |
| SK브로드밴드 | `sk_broadband` | 비상장 | 연결관계 확인 필요 |

### Operator / developer / owner
| Company | ID | Listing | Status |
|---------|-----|---------|--------|
| 디지털엣지코리아 | `digital_edge_kr` | 비상장 | 연결관계 확인 필요 |

### PM / CM / design
| Company | ID | Listing | Status |
|---------|-----|---------|--------|
| 삼우종합건축사사무소 | `samoo_cm` | 비상장 | 연결관계 확인 필요 (설계·CM 구분; DC PF 엣지 미검증) |
| 한미글로벌 | `hanmi_global` | 053690 KRX | 연결관계 확인 필요 (CM; DC PF 엣지 미검증) |

### Sponsor / credit support / contractor-adjacent
| Company | ID | Listing | Status |
|---------|-----|---------|--------|
| 한화 | `hanwha_corp` | 000880 KRX | 관계 확인 (엣지코어 신용지원) |
| 한화솔루션 | `hanwha_solutions` | 009830 KRX | 관계 확인 (REC 지분·담보) |

### Project SPCs (legal company names)
| Company | ID | Listing | Status |
|---------|-----|---------|--------|
| 캄스퀘어용인데이터센터PFV | `camsquare_yongin_pfv` | 비상장 | 관계 확인 |
| 엣지코어와이에이디씨 | `edgecore_pfv` | 비상장 | 관계 확인 |
| 알이씨데이터센터 | `rec_datacenter` | 비상장 | 관계 확인 |

## Relationships verified (company ↔ company)

| Edge | Counterparties | Type | Project (metadata) | Evidence | Gap |
|------|----------------|------|--------------------|----------|-----|
| `pf_hanwha_camsq_yongin_bridge` | 한화투자증권 → 캄스퀘어용인PFV | 선순위 브릿지론·금융주관 | 용인 지곡 HS DC | [딜사이트](https://dealsite.co.kr/articles/157007) | DART 잔액 미조회; 보도 ~530억은 참고 |
| `pf_sksec_camsq_yongin_mezz` | SK증권 → 캄스퀘어용인PFV | 후순위 브릿지 | 동일 | 동일 | DART 미대조 |
| `pf_korea_alt_camsq_yongin` | 한국대체투자자산운용 → 캄스퀘어용인PFV | 운용·스폰서 | 동일 | 동일 | 출자액 미공시 |
| `pf_lguplus_casequare_ops` | LG유플러스 → 케이스퀘어PFV | 위탁운영 | 가산 IDC | [ZDNet](https://zdnet.co.kr/view/?no=20250926172539) | 수수료 미공시 |
| `pf_kt_casequare_hist` | KT → 케이스퀘어PFV | 설계·구축·운영 (historical) | 가산 IDC | ZDNet 2021 | 현재 계약 잔존 미확인 |
| `pf_hanwha_edgecore_support` | 한화 → 엣지코어PFV | 자금보충·채무인수 | 영등포 Y-eDC | [아시아경제](https://core.asiae.co.kr/article/2024110607330592990) | DART 한도 미완전 |
| `pf_hana_sec_edgecore` | 하나증권 → 엣지코어PFV | 주관·유동화 | 동일 | 동일 | 인수 익스포저 미확정 |
| `pf_hanwha_sol_rec` | 한화솔루션 → 알이씨데이터센터 | 지분·근질권 | 안성 REC DC | [이포커스](https://www.e-focus.co.kr/news/articleView.html?idxno=3002445) | DART 미대조 |

**한화투자증권:** 용인 캄스퀘어 브릿지론에만 연결. 증권사라는 이유만으로 다른 DC PF에 엣지를 만들지 않음.

## Removed from map nodes
44 non-company nodes (permits, facilities, `kr_pf_market`, Hostway facility, Helios campus, etc.). Project/location retained as edge/project metadata only.

## Unresolved coverage gaps
1. **분당 Hostway:** 임차인(호스트웨이)은 확인되나 소유 SPC 법인명이 없어 회사↔회사 임차 엣지 미생성.
2. **igis_am / fine_partners_am / hana_alt_am:** 시설 노드 기준이었던 운용·지분 — 소유 SPC 확인 전 엣지 보류 (회사는 유지, 연결관계 확인 필요 가능).
3. **네이버클라우드·NHN클라우드·KINX·가비아·SK브로드밴드·디지털엣지·삼우·한미글로벌:** 회사 노드는 유지하되 DC PF 회사↔회사 엣지 미검증 → Shock 자동 손실 미부여.
4. **DART:** 신규 금융 엣지는 보도·2차 출처 기반; 분기·감사보고서 원문 조회는 미완 — UI에 `verification_gap` / `미확인 사항`으로 명시.
5. **KINX 시세:** 티커 053110 연결됐으나 피드 `bad_response` (심볼 이슈); 나머지 신규 상장사는 KRW 종가 수집됨.

## UI / Shock
- DetailPanel: 관련 사업, 위험 전이 경로, 확인된 익스포저, 의무 발생 조건, 근거 공시, 미확인 사항
- Role filters: CSP, 운영사, PM/CM, 시공, 전력·인프라, 대주, 증권, 운용사·투자, 연결관계 확인 필요
- Aggregate `kr_pf_market` hub removed from Shock path
- Shock still compared against +0 bp baseline in ScenarioBuilder
