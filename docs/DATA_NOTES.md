# 데이터 노트 — 확인된 값과 가정의 구분 (v0.5)

재무 기준일: 2026-06-30 (CoreWeave 10-Q 2026년 2분기) · 데이터 정리일: 2026-10-19 · 금액 단위: USD million

이 문서는 `backend/data/*.json`에서 생성했습니다. 화면·계산과 같은 데이터입니다.

## 1. 분류 기준

| 분류 | 의미 | 처리 |
|---|---|---|
| **VERIFIED** | 공식 공시 또는 회사 발표로 확인 | 그대로 사용 |
| **INFERRED** | 공개자료 기반 추론 또는 2차 출처 | 사용하되 점선·태그로 표시, 경고 문구 |
| **ASSUMED** | 사용자가 시나리오에서 정한 값 | 사용자 입력값만 해당 |
| **UNKNOWN** | 공개자료로 확인되지 않음 | 숫자를 만들지 않음 (빈칸·'미공시') |

## 2. 데이터 파일 구조

| 파일 | 내용 | 건수 |
|---|---|---|
| `entities.json` | 기업·기관 기본정보, 상장 여부, 티커, 거래소, 업종 | 39 |
| `relationships.json` | 기업 간 관계, 금융기관 역할, 금액, 연결 계약(금융·상업), 출처 | 44 |
| `financials.json` | CoreWeave 차입금·만기·이자·현금흐름(10-Q), 수주잔고·임차·고객 집중도 | 차입 계약 19 |
| `contracts.json` | 고객·용량 약정·임차 계약 장부 | 12 |
| `sources.json` | 출처 (URL·일자·사용 내용) | 39 |
| `market.db` (로컬 생성, 배포 제외) | 주가·환율·HY OAS·GPU 임대료 관측값 | — |

3D 지도, 관계 경로, 차환 엔진은 모두 `service.load_network()`에서 같은 데이터를 읽습니다. 로딩할 때 다음을 검사해 오류로 막습니다.

- ID 중복
- 존재하지 않는 기업·계약·출처 참조
- 출처 없는 VERIFIED/INFERRED 관계·계약

## 3. CoreWeave 차입 계약 (10-Q 2026.6.30 기준)

2026-10-20에 10-Q 차입금 표(`R63.htm`)와 원금·유효이자율을 대조해 모두 일치함을 확인했습니다. 총 원금 $35,551M은 만기 일정 합계(`R65.htm`)와 같습니다.

| 계약 | 잔액 | 금리 | 금리 근거 | 유효이자율 | 체결 | 만기 | 차입자 | 참여기관 (역할) |
|---|---|---|---|---|---|---|---|---|
| DDTL 1.0 | 1300.0 | SOFR+9.62% | INFERRED | 15.0% | 2023-08 | 2028-03-28 | 미확인 (UNKNOWN) | Magnetar (Lead Lender); Blackstone (Lead Lender (Tactical Opportunities)); Coatue (Lender); DigitalBridge Credit (Lender); BlackRock (Lender); PIMCO (Lender); Carlyle (Lender) |
| DDTL 2.0 | 3190.0 | 미공시 | UNKNOWN | 11.0% | 2024-05 | 2030-08 | 미확인 (UNKNOWN) | Blackstone (Lead Lender); Magnetar (Co-Lead Lender); Coatue (Lender); Carlyle (Lender); CDPQ (Lender); DigitalBridge Credit (Lender); BlackRock (Lender); Eldridge Industries (Lender); Great Elm Capital (Lender) |
| DDTL 2.1 | 3000.0 | SOFR+4.25% | INFERRED | 9.0% | 2025-09 | 2031-03 | 미확인 (UNKNOWN) | 미공시 |
| DDTL 3.0 | 2215.0 | SOFR+4.0% | VERIFIED | 9.0% | 2025-07 | 2030-08-21 | CoreWeave Compute Acquisition Co. VII, LLC (INFERRED) | Morgan Stanley (Joint Bookrunner, Joint Lead Arranger); MUFG (Joint Bookrunner, Joint Lead Arranger); Goldman Sachs (Joint Lead Arranger); JPMorgan (Lender (Syndicate)); Wells Fargo (Lender (Syndicate)); BBVA (Lender (Syndicate)); Crédit Agricole (Lender (Syndicate)); SMBC (Lender (Syndicate)); PNC (Lender (Syndicate)); Société Générale (Lender (Syndicate)) |
| DDTL 4.0 | 2837.0 | SOFR+2.25% | VERIFIED | 7.0% | 2026-03 | 2032-03 | CoreWeave Compute Acquisition Co. VIII, LLC (INFERRED) | MUFG (Co-Structuring Agent, Joint Bookrunner); Morgan Stanley (Co-Structuring Agent, Joint Bookrunner); Goldman Sachs (Coordinating Lead Arranger); JPMorgan (Coordinating Lead Arranger); Blackstone (Anchor Investor) |
| DDTL 5.0 | 1101.0 | SOFR+4.5% | VERIFIED | 9.0% | 2026-05 | 2031-11-15 | CoreWeave Financing DDTL V, LLC (VERIFIED) | Morgan Stanley (Administrative Agent, Coordinating Lead Arranger, Joint Bookrunner); MUFG (Coordinating Lead Arranger, Joint Bookrunner); U.S. Bank (Collateral Agent, Depositary Bank) |
| DDTL 5.5 | 미공시 | SOFR+5.5% | VERIFIED | — | 2026-08 | 2031-09-01 | CoreWeave Financing DDTL V-V, LLC (VERIFIED) | JPMorgan (Administrative Agent, Joint Lead Arranger, Joint Bookrunner, Syndication Agent); MUFG (Joint Lead Arranger, Joint Bookrunner, Syndication Agent); U.S. Bank (Collateral Agent, Depositary Bank) |
| Revolving Credit Facility | 0.0 | 미공시 | UNKNOWN | 7.0% | 2024-10 | 2029-11 | 미확인 (UNKNOWN) | JPMorgan (Lead Bank); Goldman Sachs (Lead Bank); Morgan Stanley (Lead Bank); MUFG (Lead Bank); Citi (Participant); Crédit Agricole (Participant); Deutsche Bank (Participant); SMBC (Participant); Wells Fargo (Participant); Barclays (Participant (2024 최초 $650M, 현재 참여 미확인)); Jefferies (Participant (2024 최초 $650M, 현재 참여 미확인)); Mizuho (Participant (2024 최초 $650M, 현재 참여 미확인)) |
| 2030 Senior Notes 9.250% | 2000.0 | 고정 9.25% | VERIFIED | 10.0% | 2025-05 | 2030-06-01 | 미확인 (UNKNOWN) | 미공시 |
| 2031 Senior Notes 9.000% | 1750.0 | 고정 9.0% | VERIFIED | 10.0% | 2025-07 | 2031-02-01 | 미확인 (UNKNOWN) | 미공시 |
| 2031 Senior Notes 9.750% | 2750.0 | 고정 9.75% | VERIFIED | 10.0% | 2026-04 | 2031-10-01 | 미확인 (UNKNOWN) | 미공시 |
| 2032 Senior Notes 9.625% | 1250.0 | 고정 9.625% | VERIFIED | 10.0% | 2026-06 | 2032-07-15 | 미확인 (UNKNOWN) | 미공시 |
| 2032 EUR Senior Notes 8.50% (€2.0B) | 2279.0 | 고정 8.5% | VERIFIED | 9.0% | 2026-06 | 2032-07-15 | 미확인 (UNKNOWN) | 미공시 |
| 2031 Convertible Senior Notes | 2588.0 | 고정 1.75% | INFERRED | 2.0% | 2025-12 | 2031-12 | 미확인 (UNKNOWN) | 미공시 |
| 2032 Convertible Senior Notes 1.75% | 4000.0 | 고정 1.75% | VERIFIED | 2.0% | 2026-04 | 2032-10-01 | 미확인 (UNKNOWN) | 미공시 |
| 2033 Convertible Senior Notes 2.875% | 미공시 | 고정 2.875% | VERIFIED | — | 2026-09 | 2033 | 미확인 (UNKNOWN) | 미공시 |
| OEM·소프트웨어 라이선스 금융 (소구) | 4220.0 | 미공시 | UNKNOWN | 11.0% | — | 미공시 | 미확인 (UNKNOWN) | 미공시 |
| OEM·소프트웨어 라이선스 금융 (비소구) | 882.0 | 미공시 | UNKNOWN | 9.0% | — | 미공시 | 미확인 (UNKNOWN) | 미공시 |
| Magnetar Loan (MagAI Ventures) | 189.0 | 미공시 | UNKNOWN | 12.0% | — | 2029-01 | 미확인 (UNKNOWN) | Magnetar (Lender) |

주의:

- Arranger · Bookrunner는 대출을 구조화·판매하는 역할입니다. 대출 전체를 보유한다는 뜻이 아닙니다.
- 공시는 계약 단위 금액과 참여기관 명단만 제공합니다. 은행별 보유액은 공시되지 않아 화면에 표시하지 않습니다(사용자 선택).
- 분할상환 차입금은 만기 시점 잔액이 6.30 잔액보다 작습니다.
- DDTL 5.5(2026.8)와 2033 전환사채(2026.9)는 6.30 이후에 체결돼 이 기준일 잔액이 없습니다.
- 2024년 리볼버 최초 참여기관(Barclays, Jefferies, Mizuho)은 2025.11 증액 공시에 이름이 없어 INFERRED로 표시합니다.

## 4. 금융기관별 참여 현황 (계약 단위)

| 기관 | 참여 계약 | 계약 잔액 합계 (기관 보유액 아님) | 만기 범위 |
|---|---|---|---|
| Blackstone | DDTL 1.0, DDTL 2.0, DDTL 4.0 | 7,327 | 2028-03-28 ~ 2032-03 |
| Morgan Stanley | DDTL 3.0, DDTL 4.0, DDTL 5.0, Revolving Credit Facility | 6,153 | 2029-11 ~ 2032-03 |
| MUFG | DDTL 3.0, DDTL 4.0, DDTL 5.0, DDTL 5.5, Revolving Credit Facility | 6,153 | 2029-11 ~ 2032-03 |
| Goldman Sachs | DDTL 3.0, DDTL 4.0, Revolving Credit Facility | 5,052 | 2029-11 ~ 2032-03 |
| JPMorgan | DDTL 3.0, DDTL 4.0, DDTL 5.5, Revolving Credit Facility | 5,052 | 2029-11 ~ 2032-03 |
| Magnetar | DDTL 1.0, DDTL 2.0, Magnetar Loan (MagAI Ventures) | 4,679 | 2028-03-28 ~ 2030-08 |
| Coatue | DDTL 1.0, DDTL 2.0 | 4,490 | 2028-03-28 ~ 2030-08 |
| DigitalBridge Credit | DDTL 1.0, DDTL 2.0 | 4,490 | 2028-03-28 ~ 2030-08 |
| BlackRock | DDTL 1.0, DDTL 2.0 | 4,490 | 2028-03-28 ~ 2030-08 |
| Carlyle | DDTL 1.0, DDTL 2.0 | 4,490 | 2028-03-28 ~ 2030-08 |
| CDPQ | DDTL 2.0 | 3,190 | 2030-08 ~ 2030-08 |
| Eldridge Industries | DDTL 2.0 | 3,190 | 2030-08 ~ 2030-08 |
| Great Elm Capital | DDTL 2.0 | 3,190 | 2030-08 ~ 2030-08 |
| Wells Fargo | DDTL 3.0, Revolving Credit Facility | 2,215 | 2029-11 ~ 2030-08-21 |
| BBVA | DDTL 3.0 | 2,215 | 2030-08-21 ~ 2030-08-21 |
| Crédit Agricole | DDTL 3.0, Revolving Credit Facility | 2,215 | 2029-11 ~ 2030-08-21 |
| SMBC | DDTL 3.0, Revolving Credit Facility | 2,215 | 2029-11 ~ 2030-08-21 |
| PNC | DDTL 3.0 | 2,215 | 2030-08-21 ~ 2030-08-21 |
| Société Générale | DDTL 3.0 | 2,215 | 2030-08-21 ~ 2030-08-21 |
| PIMCO | DDTL 1.0 | 1,300 | 2028-03-28 ~ 2028-03-28 |
| U.S. Bank | DDTL 5.0, DDTL 5.5 | 1,101 | 2031-09-01 ~ 2031-11-15 |
| Citi | Revolving Credit Facility | 0 | 2029-11 ~ 2029-11 |
| Deutsche Bank | Revolving Credit Facility | 0 | 2029-11 ~ 2029-11 |
| Barclays | Revolving Credit Facility | 0 | 2029-11 ~ 2029-11 |
| Jefferies | Revolving Credit Facility | 0 | 2029-11 ~ 2029-11 |
| Mizuho | Revolving Credit Facility | 0 | 2029-11 ~ 2029-11 |

## 5. 상업 계약 장부 (고객 · 용량 약정 · 임차)

| 계약 | 상대 | 체결 | 금액 | 금액 기준 | 종료 | 남은 금액 | 출처 |
|---|---|---|---|---|---|---|---|
| OpenAI 연산 계약 (최초) | OpenAI | 2025-03 | 11900.0 | 최대(up to) | 미공시 (기간 미공시) | 계약별 잔여 미공시 | S_OPENAI65, S_REUTERS_MS |
| OpenAI 연산 계약 (1차 확대) | OpenAI | 2025-05 | 4000.0 | 최대(up to) | 2029 (2029년까지 지급 (Reuters)) | 계약별 잔여 미공시 | S_OPENAI65, S_REUTERS_MS |
| OpenAI 연산 계약 (2차 확대) | OpenAI | 2025-09-25 | 6500.0 | 최대(up to) | 미공시 (기간 미공시) | 계약별 잔여 미공시 | S_OPENAI65 |
| Meta Order Form (MSA 2023.12.10) | Meta Platforms | 2025-09-25 | 14200.0 | 초기 약정 최대(up to approx.) | 2031-12-14 (2032년까지 대폭 확대 옵션) | 계약별 잔여 미공시 | S_META142 |
| Meta 확대 계약 | Meta Platforms | 2026-04-09 | 21000.0 | 약(approximately) | 2032-12 (2032년 12월까지 용량 제공) | 계약별 잔여 미공시 | S_META21 |
| NVIDIA 용량 매입 약정 (Order Form) | NVIDIA | 2025-09-09 | 6300.0 | 초기 계약가치 | 2032-04-13 (—) | 실제 매입액은 미판매 용량에 따라 달라짐 · 미공시 | S_NV_ORDER |
| Jane Street AI 클라우드 계약 | Jane Street | 2026-04-15 | 6000.0 | 약(approximately) | 미공시 (기간 미공시) | 계약별 잔여 미공시 | S_JANE |
| Anthropic 다년 계약 | Anthropic | 2026-04-10 | 미공시 | 미공시 | 미공시 (다년 (기간 미공시), 2026년 하반기부터 단계적 가동) | 미공시 | S_ANTHROPIC |
| Microsoft 클라우드 계약 | Microsoft | 미공시 | 미공시 | 미공시 | 미공시 (—) | 미공시 | S_10K, S_10Q2_CONC |
| Hudson River Trading 계약 확대 | Hudson River Trading | 2026-08 | 미공시 | 미공시 ('수십억 달러' 보도) | 미공시 (—) | 미공시 | S_Q2, S_HRT |
| Core Scientific 데이터센터 임차 (6개 사이트) | Core Scientific | 2025-02-26 | 10200.0 | 임대인 기준 총 계약매출 | 미공시 (12년 계약 (5년 연장 옵션 2회), 개시일별로 상이) | 계약별 잔여 미공시 | S_CORZ |
| Applied Digital 엘런데일(ND) 임차 2건 | Applied Digital | 2025-06-02 | 7000.0 | 임대인 기준 예상 총매출 (확정 아님) | 미공시 (약 15년, 첫 100MW 2025년 4분기 가동 예정) | 계약별 잔여 미공시 | S_APLD |
| Galaxy Helios 캠퍼스 임차 (Phases I–III) | Galaxy Digital | 2025-04 | — | 총액 미공시 · 평균 연간 >$1B 예상 | 15년 + 연장 옵션 | 526MW critical IT | S_GLXY_10K25, S_GLXY_HELIOS |

- 수주잔고(RPO) $103,700M (2026-06-30)의 인식 시기는 ~2028.6 (24개월) 41% · 2028.7~2030.6 (25~48개월) 39% · 2030.7~ (49~78개월) 20%입니다(10-Q).
- 2026년 3분기 초 순신규 약정 250억 달러 이상 — 6.30 RPO 미포함, 3~6개월 단기 계약 위주 (S_CAPACITY)
- 10-Q는 매출 10% 이상 고객을 익명(A·B·C)으로 표기합니다. 그래서 2026년 고객별 비중은 특정 기업에 연결하지 않습니다.
- 미개시 임차 약정은 $35,500M이고 미개시 임차 355억 달러는 2026~2029 개시, 7~16년입니다. 운영리스 미할인 지급액은 $29,135M입니다.

## 6. 주가 · 환율 데이터

| 대상 | 제공처 | 기준 | 재배포 |
|---|---|---|---|
| 미국 상장 (CRWV·NVDA·MSFT·META·TSM·DELL·BX·MS·JPM·GS·C·WFC·PNC·USB·BLK·CG·JEF·GECC·CORZ·APLD) | Finnhub `/quote` · `/stock/profile2` | 제공처 표기 '실시간', 앱은 15분마다 조회 | 공개 데모 미포함 |
| SK hynix 000660 (KOSPI) | 금융위원회_주식시세정보 | 일간 종가 · 다음 영업일 13시 이후 공개 | 공공누리 4유형 — 공개 데모 미포함 |
| TSE · XETRA · LSE · Euronext · BME 상장 (MUFG, SMBC, Mizuho, Allianz(PIMCO 모회사), Deutsche Bank, Barclays, Crédit Agricole, Société Générale, BBVA) | 미지원 | Finnhub 무료 플랜은 미국 상장 종목만 지원 | — |
| 환율 (USD·JPY(100)·EUR 등) | 한국수출입은행 매매기준율 | 영업일 1회 고시, 주말·휴일은 직전 영업일 | 공개 데모 미포함 |

원화 환산은 현지 주가에 같은 통화의 KRW 환율을 곱한 단순 환산이며, 한국에서 거래되는 가격이 아닙니다. 과거 차트는 날짜별 환율을 쓰고, 환율이 없는 날은 원화 값을 비워 둡니다.

## 7. 출처

| ID | 자료 | 일자 |
|---|---|---|
| S_10K | [CoreWeave, Inc. Form 10-K (FY2025)](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000104/crwv-20251231.htm) | 2026-03 |
| S_10Q1 | [CoreWeave, Inc. Form 10-Q (Q1 2026)](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000222/crwv-20260331.htm) | 2026-05 |
| S_10Q2 | [CoreWeave, Inc. Form 10-Q (Q2 2026) — Note 10 Debt](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000366/crwv-20260630.htm) | 2026-08-12 |
| S_10Q1_2025 | [CoreWeave, Inc. Form 10-Q (Q1 2025)](https://www.sec.gov/Archives/edgar/data/1769628/000176962825000014/crwv-20250331.htm) | 2025-05 |
| S_Q2 | [CoreWeave Reports Second Quarter 2026 Results (8-K)](https://www.sec.gov/Archives/edgar/data/0001769628/000176962826000362/coreweave2q26earningspress.htm) | 2026-08-11 |
| S_DDTL3 | [CoreWeave Closes $2.6 Billion Secured Debt Financing Facility (DDTL 3.0)](https://investors.coreweave.com/news/news-details/2025/CoreWeave-Closes-2-6-Billion-Secured-Debt-Financing-Facility-Strengthening-Market-Position-as-AI-Cloud-Leader/default.aspx) | 2025-07-31 |
| S_DDTL4 | [CoreWeave Closes $8.5 Billion Financing Facility (DDTL 4.0)](https://investors.coreweave.com/news/news-details/2026/CoreWeave-Closes-Landmark-8-5-Billion-Financing-Facility-Achieving-First-Investment-Grade-Rated-GPU-backed-Financing/default.aspx) | 2026-03-31 |
| S_DDTL5 | [Form 8-K — DDTL 5.0 Credit Agreement](https://www.sec.gov/Archives/edgar/data/0001769628/000176962826000236/crwv-20260515.htm) | 2026-05-18 |
| S_DDTL55 | [Form 8-K — DDTL 5.5 Credit Agreement](https://www.sec.gov/Archives/edgar/data/0001769628/000176962826000357/crwv-20260807.htm) | 2026-08-07 |
| S_RCF25 | [CoreWeave Expands Revolving Credit Facility to $2.5 Billion](https://www.nasdaq.com/press-release/coreweave-expands-revolving-credit-facility-25-billion-support-growth-2025-11-12) | 2025-11-12 |
| S_650 | [CoreWeave Announces $650 Million Credit Facility](https://investors.coreweave.com/news/news-details/2024/CoreWeave-Announces-650-Million-Credit-Facility-to-Support-Ongoing-Growth/default.aspx) | 2024-10-11 |
| S_NOTES2030 | [CoreWeave Announces Upsize and Pricing of $2,000 million of Senior Notes](https://investors.coreweave.com/news/news-details/2025/CoreWeave-Announces-Upsize-and-Pricing-of-2000-million-of-Senior-Notes/default.aspx) | 2025-05-21 |
| S_NOTES2031 | [CoreWeave Announces Upsize and Pricing of $1,750 million of Senior Notes (8-K Ex.99.1)](https://www.sec.gov/Archives/edgar/data/0001769628/000176962825000030/coreweave-pressreleasepric.htm) | 2025-07-22 |
| S_CONV2033 | [Latham advises on CoreWeave upsized convertible senior notes offering](https://www.lw.com/en/news/2026/09/latham-advises-on-coreweave-upsized-convertible-senior-notes-offering) | 2026-09 |
| S_AMCOMPUTE | [CoreWeave Debt, Lenders and Contracts (집계 사이트)](https://www.amcompute.com/companies/coreweave) | 2026-10 |
| S_REUTERS | [Factbox: CoreWeave's AI contracts and the lenders financing its build-out](https://www.reuters.com/legal/transactional/coreweaves-ai-contracts-lenders-financing-its-build-out-2026-10-15/) | 2026-10-15 |
| S_REUTERS_SYN | [Factbox (Reuters 기사 전재본)](https://money.usnews.com/investing/news/articles/2026-10-15/factbox-coreweaves-ai-contracts-and-the-lenders-financing-its-build-out) | 2026-10-15 |
| S_NV_EQ | [NVIDIA Tops CoreWeave Stake with $2 Billion](https://www.futuriom.com/articles/news/nvidia-tops-coreweave-stake-with-2-billion/2026/01) | 2026-01 |
| S_NV_BACKSTOP | [Nvidia commits $6.3B for CoreWeave's unused cloud capacity](https://www.rcrwireless.com/?p=424411) | 2025-09 |
| S_MAGNETAR | [Nvidia reinforces its commitment to CoreWeave with $2 billion](https://en.eloutput.com/news/tech/Nvidia-reinforces-its-commitment-to-CoreWeave-with-%242-billion/) | 2026-01 |
| S_DELL | [Dell Delivers Market's First NVIDIA GB300 NVL72 to CoreWeave](https://www.dell.com/en-us/blog/dell-delivers-market-s-first-nvidia-gb300-nvl72-to-coreweave/) | 2025-07 |
| S_SKH | [SK hynix and NVIDIA Announce Multi-year Technology Partnership](https://news.skhynix.com/en/multi-year-tech-partnership-with-nvidia/) | 2026-06-08 |
| S_HBM | [Foundry & HBM Allocation Dashboard (2026)](https://siliconanalysts.com/tools/allocation) | 2026 |
| S_META21 | [CoreWeave and Meta $21 billion expanded agreement (8-K Ex.99.1)](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000154/ex991.htm) | 2026-04-09 |
| S_JANE | [Jane Street $6B AI cloud agreement and $1B equity investment (8-K Ex.99.1)](https://www.sec.gov/Archives/edgar/data/0001769628/000176962826000167/ex991.htm) | 2026-04-15 |
| S_OPENAI65 | [CoreWeave Expands Agreement with OpenAI by up to $6.5B](https://www.coreweave.com/news/coreweave-expands-agreement-with-openai-by-up-to-6-5b) | 2025-09-25 |
| S_CORZ | [Core Scientific and CoreWeave Announce $1.2 Billion Expansion (8-K Ex.99.1)](https://www.sec.gov/Archives/edgar/data/1839341/000162828025008312/ex991-coreweavepressrelease.htm) | 2025-02-26 |
| S_APLD | [Applied Digital Announces 250MW AI Data Center Lease With CoreWeave](https://ir.applieddigital.com/news-events/press-releases/detail/123/) | 2025-06-02 |
| S_NVDA_FY26 | [NVIDIA Announces Financial Results for Fourth Quarter and Fiscal 2026 (8-K)](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000019/q4fy26pr.htm) | 2026-02-25 |
| S_SOFR | [SOFR daily rates — October 2026 (NY Fed 데이터 재게시, 10.16 3.88%)](https://www.sofrrate.com/sofr-rate/2026-10) | 2026-10-16 |
| S_META142 | [Form 8-K — Meta Order Form (up to ~$14.2B, through 2031-12-14)](https://www.sec.gov/Archives/edgar/data/1769628/000176962825000050/crwv-20250925.htm) | 2025-09-25 |
| S_NV_ORDER | [Form 8-K — NVIDIA Order Form ($6.3B initial value, through 2032-04-13)](https://www.sec.gov/Archives/edgar/data/1769628/000176962825000047/crwv-20250909.htm) | 2025-09-09 |
| S_ANTHROPIC | [CoreWeave Announces Multi-Year Agreement With Anthropic](https://coreweave.com/news/coreweave-announces-multi-year-agreement-with-anthropic) | 2026-04-10 |
| S_CAPACITY | [CoreWeave Continues to Contract New Compute Capacity at Higher Prices](https://investors.coreweave.com/news/news-details/2026/CoreWeave-Continues-to-Contract-New-Compute-Capacity-at-Higher-Prices/default.aspx) | 2026-09-17 |
| S_REUTERS_MS | [CoreWeave's AI contracts and the lenders financing its build-out (Reuters, 재게시)](https://www.marketscreener.com/news/coreweave-s-ai-contracts-and-the-lenders-financing-its-build-out-ce785dd3de80f12c) | 2026-10-15 |
| S_10Q2_LEASE | [CoreWeave 10-Q Q2 2026 — Leases](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000366/R14.htm) | 2026-08-12 |
| S_10Q2_CONC | [CoreWeave 10-Q Q2 2026 — Customer Concentration](https://www.sec.gov/Archives/edgar/data/1769628/000176962826000366/R38.htm) | 2026-08-12 |
| S_DBRG | [SoftBank Group — Completion of Acquisition of DigitalBridge](https://group.softbank/en/news/press/20260930) | 2026-09-30 |
| S_HRT | [Hudson River Signs Multibillion-Dollar CoreWeave Deal for AI Cloud (Bloomberg 제목)](https://www.bloomberg.com/news/articles/2026-08-20/hudson-river-signs-multibillion-dollar-coreweave-crwv-deal-for-ai-cloud) | 2026-08-20 |

## 8. 아직 확인하지 못한 데이터

- 기관별 대출 보유액 (모든 대주단) — 공시되지 않음
- 계약별 남은 공급 금액 (OpenAI·Meta·Jane Street·NVIDIA 약정 등) — 공시되지 않음
- Microsoft·Anthropic·Hudson River Trading 계약 금액, OpenAI 1차·3차 계약 기간
- DDTL 2.0 단일 가산금리, 리볼버 현재 가산금리, OEM 금융·Magnetar 대출의 표면금리
- DDTL 1.0·2.1 가산금리의 원공시 (현재 2차 출처, INFERRED)
- 차입금별 분할상환 스케줄과 대부분 계약의 차입 법인(SPV)
- CoreWeave의 연간 NVIDIA·Dell 구매액, NVIDIA 매출 중 CoreWeave 비중, NVIDIA HBM 매입 중 SK hynix 비중
- 2026년 3분기 10-Q (2026년 11월 공시 예정) — 공시 후 잔액·이자·RPO 갱신 필요
