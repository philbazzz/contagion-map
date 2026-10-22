# 코어위브 Contagion Map / AI DC Contagion Map

두 가지 생태계를 전환해 탐색합니다.

- **코어위브 Contagion Map** — AI Semiconductor (CoreWeave 중심)
- **AI DC Contagion Map** — 한국 AI 데이터센터 PF (회사 노드만)

금리·차환·PF 충격은 사용자 시나리오이며 예측·투자 의견이 아닙니다. 공시로 확인되지 않은 값은 UNKNOWN으로 두고 숫자를 만들지 않습니다.

> 차환금리·투자 축소는 사용자 가정이며 결과는 예측이나 투자 의견이 아닙니다. 공시로 확인되지 않은 값은 UNKNOWN으로 두고 숫자를 만들지 않습니다.

---

## 0. v0.5 변경 요약 (2차 작업: 시세 · 모드 · 계약 장부 · 시각화)

| 영역 | 내용 |
|---|---|
| 모드 분리 | 상단 **NETWORK / MARKET / SHOCK**. NETWORK는 연결 구조, MARKET은 실제 관측 주가, SHOCK은 가상 차환 충격을 보여 줍니다. 모드를 바꿔도 노드 위치와 카메라는 그대로이고, MARKET 색(상승 빨강 · 하락 파랑)과 SHOCK 색은 섞이지 않습니다. |
| 주가 · 원화 환산 | 미국 상장 20종목은 Finnhub, SK hynix는 금융위원회(KRX 일간 종가), 환율은 한국수출입은행에서 받습니다. 해외 주가는 **원화 환산가를 크게** 보여 주고 현지가·등락률·환율·기준 시각을 함께 표시합니다. 1M~1Y 차트는 날짜별 환율로 환산합니다. 비상장 기업은 '비상장', 무료 제공처가 지원하지 않는 거래소(도쿄·유럽)는 '미지원'으로 표시합니다. |
| 계약 장부 | `contracts.json`에 고객·용량 약정·임차 계약 12건(체결일 · 금액 · 금액 기준 · 종료일 · 남은 기간 · 출처)을 넣었습니다. 계약별 남은 금액은 공시되지 않아 '미공시'로 둡니다. 수주잔고(RPO) $103.7B의 시기별 비율, 3분기 신규 약정, 미개시 임차 약정, 고객 집중도(익명)도 함께 보여 줍니다. |
| 금융기관별 차입 | 금융기관 11곳을 추가해 26곳이 됐습니다. 은행을 누르면 **Lending** 섹션에 그 은행이 참여한 계약의 역할 · 잔액 · 약정액 · 금리 · 만기 · 남은 기간이 나옵니다. 개요의 **Lenders** 표는 기관별 참여 계약 수 · 계약 잔액 합계(보유액 아님) · 만기 범위를 보여 줍니다. |
| 시각화 | **SHOCK 단계 재생**: 새로 활성화되는 관계마다 빛이 출발 기업에서 도착 기업까지 차례로 이동합니다. 도착한 순간 대상 기업의 상태가 켜지고 파동이 퍼지며, 단계마다 카메라가 관련 기업을 천천히 비추고 관련 없는 기업은 흐려집니다. 단계 시간은 연결선 수와 설명 길이에 맞춰 늘어납니다. **패널 흐름도**: CoreWeave → … → 기업 경로를 관계 이름 · 금액 · 근거와 함께 세로로 그리고, 계약은 체결부터 만기까지 막대로 그리며 '오늘'을 표시합니다. |

## 1. v0.4 변경 요약 (1차 작업: 데이터 · 계산 · 경로)

| 영역 | v0.3 | v0.4 |
|---|---|---|
| 데이터 구조 | `network.json` 한 파일에 기업·관계·가정 수치 혼재 | `entities` · `relationships` · `financials` · `sources` 4개 파일로 분리, 로딩 시 참조 무결성 검사 |
| 관계망 | 노드 20 (DEMO 5 포함) · 관계 24 | 노드 27 · 관계 32 · 금융계약 19 · 출처 30, **DEMO 기관 전부 삭제** |
| 금융계약 | 금액 없는 '대출 참여' 6건 | 10-Q 차입금 표 19건: 잔액 · 약정액 · 금리(고정/SOFR+가산) · 유효이자율 · 만기 · 차입자 · 담보 · 참여기관 역할(Administrative Agent / Arranger / Bookrunner / Lender) |
| '계산 경로에 없음' | 지도와 엔진이 다른 연결선 집합을 사용 → 19곳 중 15곳 '경로 없음' | 지도와 엔진이 같은 관계 데이터 사용. **관계 경로(A)**와 **계산 상태(B 계산 · C 가정 · D 관계만 · E 미확인)**를 분리 표시 |
| 지표 | 주문 충격 35점 · 전달계수 0.6 등 점수 | 점수 전부 제거. USD · % · bp · hop만 사용 |
| 계산 | 근거 없는 계수를 단계마다 곱함 | 추가 이자 = 차환 금액 × 성공 비율 × (신규 금리 − 기존 비교금리). 그 뒤는 사용자가 가정을 입력할 때만 계산 |
| 시나리오 | GPU 구매 감소 · 신용손실(DEMO) · 서비스 차질 | **Refinancing Shock** 하나: 차입금 선택, 9/12/15% 비교, 연도별 이자·원리금, 6단계 전파 |
| 화면 | — | 상단 집계(기업 · 직접 · 간접 · 계약 · 산업 관계, 데이터에서 자동 계산), 계약별 탐색, 두 기업 간 최단 관계 경로, 만기 구조, 계수 전수표 |

## 2. 원인 분석 요약

- **'계산 경로에 없음'**: v0.3 엔진은 시나리오마다 `impact_channel`이 맞고 `dependency_ratio`가 있는 연결선만 사용했습니다(GPU 5개 · 서비스 4개 · 신용 DEMO 5개). 지도는 24개를 모두 그렸기 때문에, 연결선이 보이는 기업도 엔진에서는 경로가 없었습니다. 또 '관계 있음'과 '계산 가능'이 한 상태로 표시됐습니다.
- **근거 없는 계수**: 의존도 9개(5~50%), 전달계수 2개(0.6 · 1.0), 출발 점수(감소율 × 100), DEMO 익스포저 · 회수율 · 자본이 모두 출처 없는 가정이었습니다. 전체 목록과 처리 결과는 앱의 **Data & Sources → Model Inputs**와 [docs/DATA_NOTES.md](docs/DATA_NOTES.md)에 있습니다.

## 3. 계산 모델

```
기존 비교금리  = 표면금리: 고정 쿠폰 또는 SOFR(하한 적용) + 가산금리
               유효이자율: 10-Q 공시값 (표면금리 미공시 시 자동 사용, 경고 표시)
추가 연간 이자 = 차환 금액 × 차환 성공 비율 × (신규 금리 − 기존 비교금리)
자금조달 필요액 = 차환 금액 × (1 − 성공 비율)
6개월 비교     = 추가 이자 ÷ 2 ÷ 2026 상반기 영업현금흐름   (기간 일치)
연도별 표      = 차환 시점부터 월할, 신규 차입은 일시상환 가정
--- 아래는 사용자가 값을 넣을 때만 계산 (비우면 '잠재 경로 · 미산정') ---
CAPEX 축소     = 추가 이자 × CAPEX 흡수율
GPU 구매 감소  = CAPEX 축소 × GPU 비중   → NVIDIA FY2026 매출 대비 %
```

- 금리는 선택한 차입금 하나에만 적용하고, 다른 차입금은 바뀌지 않습니다.
- 금리가 내려가면 비용 감소로 계산합니다. 이 경우 투자 축소 경로는 생기지 않습니다.
- 예를 들어 2030 Senior Notes(9.25%, $2.00B)를 12%로 바꾸면 추가 이자는 +$55M/년입니다. 상반기 영업현금흐름 대비로는 +0.75%(6개월 기준)입니다.
- SK hynix · TSMC · Dell은 관계는 확인되지만 금액을 계산할 공개 데이터가 없습니다. 그래서 'D · 관계만 확인'으로 표시하고, 필요한 데이터를 함께 안내합니다.
- 붉은색(부도)은 계산된 손실이 있을 때만 쓰므로 이 시나리오에서는 나타나지 않습니다.

## 4. 폴더 구조

```
contagion/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                 FastAPI (API + 시장 지표 스케줄러)
│  │  ├─ service.py              데이터 로딩 · 무결성 검사 · 조회
│  │  ├─ models.py               Entity · Relationship · Instrument · Source 스키마
│  │  ├─ engine/refinancing.py   차환 계산 · 6단계 · 기업별 계산 상태(B~E)
│  │  ├─ engine/relations.py     관계 경로 · 최단 경로 · 집계
│  │  └─ market/                 HY OAS · GPU 임대료 (v0.2) · quotes.py 주가·환율 (v0.5)
│  ├─ data/                      entities · relationships · financials · contracts · sources (.json)
│  ├─ tests/                     pytest 52개 (차환 계산 · 관계망 · 주가·환율 모의 · 시장 수집 모의 · API)
│  ├─ export_network.py          데이터 묶음 출력 (데모 빌드 · 일치 검사용)
│  ├─ serve_simple.py            FastAPI 없이 쓰는 대체 서버
│  └─ .env.example               API 키 변수 이름만
├─ frontend/
│  ├─ src/App.tsx · components/  화면 (Viz.tsx: 흐름도 · 타임라인 · 주가 차트)
│  ├─ src/engine/                Python 엔진의 브라우저 포트 (데모용, 결과 동일 검증)
│  ├─ src/universe/Universe.ts   3D 렌더러
│  └─ scripts/build-demo.mjs · parity-check.mjs
├─ demo/contagion-demo.html      서버 없이 열리는 단독 데모
└─ docs/DATA_NOTES.md · MARKET_DATA.md · EXTENSION_MEMO.md
```

## 5. 실행 · 배포

### 권장: GitHub Pages (방문자는 서버 불필요)

배포·Pages 설정 절차는 **[docs/GITHUB_PAGES.md](docs/GITHUB_PAGES.md)** 를 따르세요.  
요약: Source = GitHub Actions, (선택) Secrets에 `FRED_API_KEY`, push 시 `.github/workflows/pages.yml`이 정적 빌드를 배포합니다.

로컬에서 배포본과 동일하게: **`preview.bat`** (한 번 클릭 · Python은 빌드 시 network export에만 사용).

### 로컬 실행 (Windows) — 기본 한 줄

준비물: Python 3.10+ (python.org), Node.js 18+.

```bat
start.bat
```

**백엔드 `:8000` + 프론트 `:5173`를 함께** 띄웁니다 (`VITE_API_MODE=http`). Market의 **지금 조회**가 실제 시세 재수집을 수행합니다. Ctrl+C로 프론트를 종료하면 백엔드도 정리합니다.

최초 1회 venv가 없으면 `start_backend.bat`가 의존성을 설치합니다. 완료 후 `start.bat`을 다시 실행하세요.

| 명령 | 용도 |
|---|---|
| **`start.bat`** | **권장** — 백엔드+프론트 (시세·API 포함) |
| `start_backend.bat` | FastAPI만 (`:8000`) · `start.bat`이 내부적으로 사용 |
| `preview.bat` | 정적 빌드 미리보기 (`:4173`, GitHub Pages와 동일) |
| `run_tests.bat` | 백엔드 pytest |

PF 시세만 CLI로 갱신할 때:

```bat
backend\.venv\Scripts\python.exe scripts\fetch_pf_quotes.py
```

선택 API 키: `backend/.env` (`backend/.env.example`). yfinance/FDR 일간 종가는 키 없이 동작합니다.  
**GitHub Pages 공개본에는 Yahoo/Finnhub/KRX 수치를 넣지 않습니다** — [docs/MARKET_DATA.md](docs/MARKET_DATA.md) §8.

## 6. 테스트 · 검증 명령

```bash
cd backend && pytest -q            # 또는 run_tests.bat
cd frontend && npm run typecheck
cd frontend && npm run parity      # Python 엔진 ↔ 브라우저 엔진 결과 비교
cd frontend && npm run build:demo  # 데모 재생성 (Python 필요)
```

## 7. API

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/network` · `/api/sources` · `/api/health` | 데이터 묶음 · 출처 · 상태 |
| GET | `/api/stats?origin=coreweave` | 상단 집계 (데이터에서 계산) |
| GET | `/api/paths?a=&b=` | 두 기업 간 최단 관계 경로 |
| GET | `/api/entities/{id}?origin=` | 기업 상세 · 관계 · 참여 계약 |
| POST | `/api/simulate/refinancing` | `{instrument_id, new_rate_pct, amount_usd_m?, basis, refi_date?, success_ratio, fee_pct, new_tenor_years, sofr_pct?, capex_absorption_pct?, gpu_share_pct?, compare_rates?}` |
| GET/POST | `/api/market` · `/api/market/refresh` · `/api/runs` | 시장 지표 · 실행 기록 |
| GET | `/api/quotes` | 기업별 최신 시세 · 원화 환산 · 상태 (비상장 · 미지원 · 키 미설정 구분) |
| GET | `/api/quotes/{id}/history?period=1M\|3M\|6M\|1Y` | 종가 이력 (날짜별 환율 원화 값, 1D는 미지원 안내) |
| POST | `/api/quotes/refresh` | 환율 · 미국 · KRX 수동 조회 (5분 제한) |

## 8. 검증 결과 (이 환경에서 실제 실행)

| 항목 (요청서 19장) | 결과 | 방법 |
|---|---|---|
| 공시 수치 정확성 | 통과 | 10-Q 차입금 표·만기 표·이자 표, DDTL 3.0·4.0 보도자료, DDTL 5.0·5.5 8-K, NVIDIA 8-K 원문과 대조 |
| 차환 대상 차입금만 금리 변경 | 통과 | 테스트: 다른 차입금 이자 불변 |
| 신규 금리 이자부담 정확성 | 통과 | 2030 Notes $2,000M × (12 − 9.25)% = +$55M, 9/12/15% 비교 일치 |
| 금리 하락 시 비용 감소 | 통과 | 9% → −$5M, 투자 축소 경로 미생성 |
| 금리 유형 · 기간 | 통과 | 고정/변동(SOFR 하한), 유효이자율 대체, 월할 연도표, 성공 비율·수수료 |
| 금융 계산과 산업 영향 분리 | 통과 | 가정 미입력 시 공급망 금액 없음, 붉은 부도 상태 없음 |
| 지도와 엔진 데이터 일치 · 근거 없는 관계 없음 | 통과 | 모든 기업에 관계 경로 존재, VERIFIED/INFERRED 관계는 출처 필수, DEMO 없음 |
| 직접 · 간접 구분 | 통과 | 직접 24 · 간접 2 (데이터에서 계산) |
| 애니메이션과 계산 일치 | 통과 | 단계별 표시값이 해당 단계 이후에만 나타남 (NVIDIA 가정값 S4부터) |
| Python ↔ 브라우저 엔진 | 통과 | 120개 차환 케이스 + 관계 경로 전체 필드 비교, 불일치 0 |
| 화면 | 통과 | 1440 · 1280 · 1920 · 1024(우측 오버레이) · 390(가로 스크롤 없음), 콘솔 오류 0 |
| v0.5 티커 매핑 | 통과 | 미국 20종목 → Finnhub, 000660 → KRX, 도쿄 · 유럽 9곳 → 미지원, 비상장 → 주가 없음 |
| v0.5 USD → KRW 환산 | 통과 | 모의 응답: $150 × 1,430원 = 214,500원, JPY(100) 953.21 → 9.5321원, '1,430' 쉼표 처리 |
| v0.5 한국 주가 원화 | 통과 | 000660 종가 그대로 원화, 전일 대비 계산 |
| v0.5 오류 처리 | 통과 | 키 미설정 · 종목 미지원(가격 0) · 서버 오류 · 인증 실패에서 가격을 만들지 않음. 실패 시 마지막 정상값과 시각 유지, 키는 헤더로만 보내고 응답 · 오류에 노출 없음 |
| v0.5 과거 원화 차트 | 통과 | 날짜별 환율 사용, 환율 없는 날은 비움(현재 환율로 채우지 않음), 주말에는 직전 영업일 고시 |
| v0.5 MARKET / SHOCK 분리 | 통과 | Network→Market→Shock→Network 전환 후 지도 픽셀 차이 0.2%(별·입자 움직임 수준)로 노드 위치·카메라 유지, MARKET에는 시뮬레이션 색 없음, 실행하면 SHOCK로 전환, 모의 시세 DB로 MARKET 렌더링 확인 |
| v0.5 단계 애니메이션 | 통과 | S4에서 빛이 이동하는 중(0.9초)과 도착 후(3.7초)를 캡처해, 도착 전에는 NVIDIA 상태가 꺼져 있고 도착 후 'GPU 구매 −$33M (가정)'이 켜지는 것을 확인 |

## 9. 남은 작업과 제한

- **시세 연동: 코드 구현 완료, 실제 수신 검증은 아직 안 됨.** 이 환경은 외부 API 접속이 막혀 있습니다. 그래서 공식 문서의 응답 형식으로 만든 모의 응답으로 검증했습니다. PC에서 키를 넣고 처음 조회할 때 응답 형식을 확인해야 하며, 특히 금융위원회 응답 필드와 수출입은행 새 도메인을 확인해야 합니다.
- 미국 종목 차트는 Finnhub 무료 플랜에 과거 일봉이 없어, 앱이 수집한 날부터 이력이 쌓입니다. 도쿄 · 유럽 상장 금융기관 9곳은 무료 제공처가 없어 시세를 표시하지 않습니다.
- **3차 작업 예정**: 시나리오 비교 화면 고도화, 성능 최적화 등.
- 기관별 대출 보유액, 차입금별 분할상환 스케줄, CoreWeave의 NVIDIA·Dell 구매액은 공시되지 않아 계산하지 않습니다. 확인하지 못한 항목 목록은 [docs/DATA_NOTES.md](docs/DATA_NOTES.md) 7장에 있습니다.
- 재무 수치는 2026.6.30 10-Q 기준입니다. 3분기 10-Q가 공시되면(2026년 11월 예정) `financials.json`을 갱신해야 합니다.
- 이 환경에서는 `npm install` · `pip install fastapi`를 할 수 없었습니다. 그래서 FastAPI 경로는 같은 service 계층을 쓰는 대체 서버로, 프런트 타입 검사는 임시 타입 정의로 검증했습니다. PC에서 처음 실행할 때 `run_tests.bat`과 `npm run typecheck`를 한 번 돌려 주세요.
