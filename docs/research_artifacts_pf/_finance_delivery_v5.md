# AI DC PF Finance Expansion — Delivery Report (v5)

## Summary

The AI DC Contagion Map now surfaces **news-backed financial exposures** (who → which project → which instrument → amount type) for Korean data-center PF. Data is consumed by `frontend/public/data/pf/network.json` + `projects.json`; UI filters and dossiers read the same graph.

## Counts

| Metric | Value |
|--------|------:|
| Nodes | 235 |
| Edges | 143 |
| Financial / credit edges | 62 |
| Institutions with finance edges | 34 |
| Finance participants (incl. PFV/SPC) | 56 |
| Projects with `financing_disclosed` | 13 |
| Nodes added this pass | 5 (`magna_pfv`, `camsquare_first_spc`, `k1_premier_reit`, `korealand_trust`, `lotte_innovate`) |
| Edges added this pass | 20 |
| Edges enriched this pass | 35 |

### By institution group (finance participants)

- KR bank / capital: 12  
- KR securities: 10  
- Financial (misc capital): 6  
- KR construction: 5  
- KR insurance: 3  
- KR AM / REIT: 3  
- KR trust / savings / mutual aid: 1 each  
- Project finance SPV/SPC: 14  

### By financing stage (typed edges)

- main_pf: 30  
- equity: 8  
- bridge: 2  
- securitization: 2  
- operating_refinancing: 2  
- construction: 1  
- unset (legacy / non-KR or pending enrich): 16  

## Representative money paths (implemented)

1. **Casequare Gasan** — Dealsite lender list with institution amounts (e.g. 동양생명 70억, 농협 40억, 한투 후순위 70억); 마운틴리치제일차 ABS + **유안타 인수확약**; 키움 리파이낸싱 = underwrite (not funded loan).  
2. **Camsquare Ansan** — 삼성증권 주관(시설 8340억 ≠ 보유) → **캄스퀘어제일차 ABSTB** → PFV; 삼성 신용보강 6800억 한도; 행정공제회 에쿼티 1300억.  
3. **Magna Deogi (new)** — 8 named lenders, facility 2730억, **no per-lender split**; GS 지분·EPC·책임준공; 케이원프리미어리츠 41.67%; 하나증권 주관·지분.  
4. **Yongin Camsquare bridge** — 한화투자 530 / SK증권 70; 롯데이노베이트 위탁운영.  
5. **Bucheon** — 4 lenders named, amounts undisclosed (facility 1590억).  
6. **Fine DC** — 대우 채무인수 보증 2959억 (contingent); KB발해 100억; 현대차증권 주선·셀다운.

## Corrections to prior modeling

- Arranger / facility totals no longer presented as retained funded exposure (`facility_total_context`).  
- Kiwoom Casequare 3800억 typed as `underwrite_commitment` + contingent.  
- Samsung Ansan 8340억 arranger separated from ABSTB credit-support path.  
- Construction contract values kept distinct from unpaid receivables / guarantees.  
- Unknown amounts stored as `null` + “금액 미공개”, never `0`.

## Remaining gaps (unnamed / undisclosed)

- Magna / Bucheon / Fine: named lenders without individual allocations.  
- Camsquare Ansan: tranche B/C ultimate lenders largely unnamed; admin mutual path partially “투자 경로 미공개”.  
- Many permit-only projects still have no financing edges (not claimed as complete census).  
- Current outstanding balances generally **현재 잔액 미확인**.

## UI

- Finance-first filters: institution type, financing stage, instrument path, amount disclosed, direct/indirect, evidence status.  
- Company dossier: project → path → amount type → article link.  
- SPV selection: participant roster by role (bridge / main PF / insurance·mutual / funds / securities / EPC / ops).  
- Default exposure filter: `confirmed_dc`.  
- Shock scenarios remain separate from article facts (no invented loss rates).

## Validation

`scripts/validate_pf_finance_v5.py` — **PASSED** (syndicate non-double-count, Magna/Casequare/Camsquare/Yuanta/Daewoo/Kiwoom checks).

## How to re-apply data

```bash
backend/.venv/Scripts/python.exe scripts/expand_pf_finance_exposures_v5.py
backend/.venv/Scripts/python.exe scripts/validate_pf_finance_v5.py
```

Note: `npm run prepare:static` refreshes semiconductor `public/data/network.json` only; it does **not** overwrite `public/data/pf/`.
