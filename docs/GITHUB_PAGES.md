# GitHub Pages 배포 안내

Contagion Map은 **정적 사이트**로 GitHub Pages에 배포됩니다. 방문자는 Python·Node를 실행할 필요가 없습니다.

## 동작 방식

| 기능 | Pages에서 |
|---|---|
| 행성 네트워크 · 관계 · 상세 패널 | `network.json` (빌드 시 `export_network.py`로 생성) |
| 금리 충격 · 차환 · 노출 분류 | 브라우저 TypeScript 엔진 (`frontend/src/engine/*`, Python과 parity 검증) |
| 국채 금리 (10Y · 2Y) | `market.json` — GitHub Actions + FRED API (재배포 가능) |
| 주식 **수치** 시세 | **포함하지 않음** (Finnhub · Yahoo · KRX 재배포 제한) |
| 종목별 차트 · 시세 UI | 상세 패널 **TradingView** 위젯 (임베드, 데이터 추출 없음) |

자세한 라이선스·대안은 [MARKET_DATA.md](MARKET_DATA.md) §8을 보세요.

## 저장소에서 Pages 켜기

1. 이 저장소를 GitHub에 push합니다 (`main` 또는 `master`).
2. **Settings → Pages → Build and deployment → Source** 를 **GitHub Actions** 로 선택합니다.
3. (권장) **Settings → Secrets and variables → Actions** 에 `FRED_API_KEY` 를 추가합니다  
   ([FRED API Keys](https://fredaccount.stlouisfed.org/apikeys)).
4. `.github/workflows/pages.yml` 이 push / 수동 실행 시 `frontend/dist` 를 배포합니다.
5. 사이트 URL: `https://<user>.github.io/<repo>/`  
   워크플로는 `VITE_BASE=/${{ github.event.repository.name }}/` 를 사용합니다.  
   사용자/조직 사이트(`username.github.io`)면 Repository variable `VITE_BASE` 를 `/` 로 두고 워크플로를 그에 맞게 수정하세요.

## 로컬에서 배포본과 동일하게 보기

```bat
preview.bat
```

또는:

```bat
cd frontend
set VITE_API_MODE=static
set VITE_BASE=./
npm run build
npx vite preview --host 127.0.0.1 --port 4173
```

개발 중(핫 리로드, 기본 정적 모드):

```bat
start_frontend.bat
```

로컬 FastAPI + 실시간 시세(키 필요):

```bat
start_backend.bat
set VITE_API_MODE=http
start_frontend.bat
```

## FRED 스냅샷 주기 갱신

`.github/workflows/market-fred.yml` 이 평일 스케줄로 `frontend/public/data/market.json` 을 커밋합니다.  
시크릿이 없으면 워크플로는 경고만 남기고 종료합니다.
