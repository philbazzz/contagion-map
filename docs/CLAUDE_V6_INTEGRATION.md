# Claude v6 integration (2026-10-21)

## Integrated from `claude/`

| Artifact | Action |
|----------|--------|
| `scripts/build_kr_dc_v6.py`, `kr_dc_ledger.py`, `report_kr_dc_v6.py`, `validate_kr_dc_v6.py` | Copied into `scripts/` |
| `scripts/data/pf_v5_baseline/` | Copied (rebuild baseline) |
| Built `network.json` / `projects.json` + `kr_dc_*` | Replaced active `frontend/public/data/pf/` (v5 backup: `network.v5.bak.json`) |
| `KR_DC_RESEARCH_V6.md` | Copied to `docs/` |
| shockEngine SPV anchor + skip repaid/historical | Merged into active `shockEngine.ts` |
| SourcesView `KrDcResearch` | Merged into active Sources view |
| LpResize / shock affected-companies UI | Implemented in active app (Claude zip lacked the full shock results panel) |

## Not blindly overwritten

- Active finance-first filters (institution / stage / amount / directness) kept in `PfScenarioBuilder`.
- Active `PfCompanyProjects` finance dossier kept.
- Semiconductor ecosystem data untouched.

## Open DART

- Server module: `backend/app/opendart/`
- Routes: `/api/opendart/status`, `sync-corp-codes`, `company`, `disclosures`, `filing/{rcept_no}`
- Env: `OPEN_DART_API_KEY=` in `backend/.env.example` (empty placeholder). Cache under `backend/data/opendart_cache/` (gitignored).
- Key is **not** configured until you set it locally in `backend/.env`. Status currently reports `configured: false`.

## Left panel

- Default width 420px; drag range 320–640px; persists; collapse to 48px; wraps long names; fires `contagion:lp-resize` for the network canvas.

## PF Shock results

- Panel **충격 영향 기업** groups by impact category (not default ratings).
- Distinguishes contingent guarantees, SPC vs parent, missing amounts → `영향 확인 / 부도위험 판단 자료 부족`.
- Selecting a company highlights transmission edges (`impact_edge_ids`).
- Baseline = +0bp / CAPEX 0% / CW normal — reset clears incremental effects.

## Checks run

- `validate_kr_dc_v6.py` — core PASS (print encoding noise at end on Windows cp949)
- `node scripts/verify_pf_shock_affected.mjs` — PASS
- `/api/opendart/status` — responds (key not set)
- Frontend :5173 / backend :8000 — up
