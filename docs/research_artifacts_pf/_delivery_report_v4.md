# Contagion Map expansion delivery (v4)

**As of:** 2026-10-21  
**FX:** USD/KRW = **1,323.79** (Yahoo `KRW=X` via yfinance)  
**Formula:** `market_cap_krw = market_cap_usd × usd_krw_rate`  
**US threshold:** KRW 500 billion (≈ USD 378M at this FX)

## Semiconductor ecosystem

| Metric | Before | After |
|--------|-------:|------:|
| Nodes | 87 | **151** |
| Edges | 121 | **128** |

### Companies added (US mcap-eligible seeds)
63 new listed US entities across GPU-adjacent, analog, power, interconnect, optical, foundry/packaging, EDA, equipment, metrology/test, subsystems, materials, distribution (see `_us_mcap_eligibility.json` + `backend/data/entities.json`).

Also ensured **Intel (`INTC`)** with packaging edge to Amkor.

### Confirmed relationships added
- `s_kla_tsmc`, `s_amat_tsmc`, `s_cadence_nvidia`, `s_gfs_amd`, `s_arrow_dist`, `s_intel_amkor`
- `s_astera_hyperscale` (**INFERRED** hyperscaler demand channel)

### Excluded / not fabricated
- **Cerebras** — private  
- **Ambiq** — ticker not verified for this pass  
- **SanDisk standalone** — use Western Digital (`wdc`)  
- **Qnity** — listing unverified → research queue  
- **No new CoreWeave edges** for newly added US semis (participation ≠ CW contract)

### US mcap filter note
All 79 fetched public tickers cleared KRW 500B at the retrieved FX/caps snapshot (`eligible 79/79`). Indie Semiconductor is near the floor (~KRW 562B). Re-run `scripts/fetch_us_mcap_eligibility.py` before relying on stale caps.

---

## Korean AI DC PF ecosystem

| Metric | Before | After |
|--------|-------:|------:|
| Company nodes | 200 | **230** |
| Edges | 106 | **123** |
| Projects (metadata) | 141 | **144** (+3 verified clusters) |

### Companies added (examples)
IBK기업은행, IBK투자증권, NH투자증권, 현대차증권, 하나캐피탈, 우리자산운용, 우리자산신탁, 퍼시픽자산운용, 와이드크릭·인마크·산은인프라·마스턴·캡스톤 AM, KB발해인프라, 맥쿼리한국인프라, 동양, 디씨플랫폼, 이도, 신영, DCITY부천PFV, 파인디씨PFV, CPPIB, 한전, SK가스, 드림마크원, 다우기술, 코스콤, 디씨브릿지, 청라IDC PFV placeholder, 퍼시픽써니 SPC placeholder, etc.

Many remain **연결관계 확인 필요** until project-specific evidence exists (by design).

### Projects added (company-only graph; SPCs are nodes)
1. **용인 죽전 퍼시픽써니** (`yongin_jukjeon_pacific`) — Pacific AM, CPPIB, 신한투자증권, 현대건설, LG CNS(임차 예정)  
2. **부천 삼정 AI 허브센터** (`bucheon_samjeong_ai`) — 동양, DCITY부천PFV, 디씨플랫폼, DL건설, 하나은행·경남은행·IBK·하나캐피탈  
3. **광주첨단 파인데이터센터** (`gwangju_fine_dc`) — 파인디씨PFV, 대우건설(시공·채무보증), KB발해(~100억), 하나·KB(공시상 채권자)

### Confirmed edges added
17 PF edges (see `_expansion_report_v4.json`). Syndicated totals are **not** assigned to each lender; notes state individual shares undisclosed.

### Research queue (not in confirmed exposure graph)
포항 AI Factory, 고양 삼송, 인천 원창/도화, 용인 덕성리, 부평 Digital Edge vs ESR/STACK, 안산 복수 프로젝트 분리 등 → `pf/research_queue.json`.

### Downgrades
Unsupported CW↔KR financial UNKNOWN edges flagged with verification gaps where present.

---

## UI changes
- Mode titles already: 코어위브 Contagion Map / AI DC Contagion Map  
- PF left panel: company-only list, role + **근거 상태** filters, **1홉/2홉**, confirmed project metadata → SPC focus  
- Detail: Korean plain-language relationship sentence; project-grouped dossier  
- Legend: verified vs inferred vs historical/proposed; contract vs shock-path note  
- Shock still compared to **+0 bp** baseline  

---

## Checks run
- `fetch_us_mcap_eligibility.py` — FX + caps written  
- `expand_ecosystems_v4.py` — data integrated  
- `validate_contagion_v4.py` — see `_validation_v4.json`  
- `npm run build` (run after this report)  

## Material gaps / conflicts
- 퍼시픽써니 **정확한 차주 등기상호** still placeholder (`pacific_sunny_spv`)  
- LG CNS 죽전 임차 = **예정** (proposed)  
- 부천·파인 **대주 개별 약정액** undisclosed  
- Astera→MSFT channel = **INFERRED**  
- Permit-only projects remain metadata-only (not company nodes)
