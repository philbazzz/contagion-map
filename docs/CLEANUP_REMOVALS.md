# Cleanup removals (2026-10-22)

## Removed from working tree (verified unused / regenerable)

| Path | Approx. size | Justification |
|---|---|---|
| `claude/` | 11.0 MB | Full extracted duplicate of the repo plus Claude v6 research bundle. Not imported by frontend, backend, or active scripts. Recoverable in the Desktop checkpoint. |
| `tmp_dc.html` | 0.10 MB | Temporary debug HTML dump; no route or build reference. |
| `tmp_edges.txt` | <0.01 MB | Temporary debug output; no reference. |
| `frontend/dist/` | 2.3 MB | Regenerable Vite production output. |
| `**/__pycache__/` | regenerable | Python bytecode caches (including under `.venv`); recreated on import. |

## Moved

| From | To | Reason |
|---|---|---|
| `DATA_CENTER_PF_AUDIT.md` | `docs/DATA_CENTER_PF_AUDIT.md` | Keep research audit; avoid root clutter. |

## Retained (uncertain or required)

| Path | Reason |
|---|---|
| `demo/` + `frontend/src/demo.tsx` + `frontend/scripts/build-demo.mjs` | Optional offline demo; `npm run build:demo` entry. |
| `backend/data/opendart_cache/` | Not required for static runtime UI; required to re-run DART note research without re-download. Kept on disk and in checkpoint; **excluded from distribution ZIP**. |
| Intermediate `docs/*` extracts / reconciliations + `scripts/patch_*.py` | Needed to reproduce disclosure → graph mappings. |
| Active SPA (`frontend/src/main.tsx` → `App.tsx`), PF + semi datasets | Core product. |
| `backend/.env` | Local credentials left untouched on disk; **excluded from ZIP** (`.env.example` included). |

## Not removed (would change behavior or coverage)

- Application `network.json` / PF datasets / entity–relationship counts.
- Shock engines, filters, or graph schema.
- Dependency lockfiles.
MOVED public/data/pf/kr_dc_relationships.json -> docs/research_artifacts_pf/kr_dc_relationships.json (research artifact; not loaded by SPA)
MOVED public/data/pf/kr_dc_relationships.csv -> docs/research_artifacts_pf/kr_dc_relationships.csv (research artifact; not loaded by SPA)
MOVED public/data/pf/kr_dc_entity_status.json -> docs/research_artifacts_pf/kr_dc_entity_status.json (research artifact; not loaded by SPA)
MOVED public/data/pf/kr_dc_entity_status.csv -> docs/research_artifacts_pf/kr_dc_entity_status.csv (research artifact; not loaded by SPA)
MOVED public/data/pf/kr_dc_changelog.json -> docs/research_artifacts_pf/kr_dc_changelog.json (research artifact; not loaded by SPA)
MOVED public/data/pf/kr_dc_open_issues.json -> docs/research_artifacts_pf/kr_dc_open_issues.json (research artifact; not loaded by SPA)
MOVED public/data/pf/dc_namepf_dash.json -> docs/research_artifacts_pf/dc_namepf_dash.json (research artifact; not loaded by SPA)
MOVED public/data/pf/dc_namepf_permits.json -> docs/research_artifacts_pf/dc_namepf_permits.json (research artifact; not loaded by SPA)
MOVED public/data/pf/dc_namepf_projects.json -> docs/research_artifacts_pf/dc_namepf_projects.json (research artifact; not loaded by SPA)
MOVED public/data/pf/dc_namepf_geo.json -> docs/research_artifacts_pf/dc_namepf_geo.json (research artifact; not loaded by SPA)
MOVED public/data/pf/_company_only_report.json -> docs/research_artifacts_pf/_company_only_report.json (research artifact; not loaded by SPA)
MOVED public/data/pf/_expansion_report_v3.md -> docs/research_artifacts_pf/_expansion_report_v3.md (research artifact; not loaded by SPA)
MOVED public/data/pf/_expansion_report_v4.json -> docs/research_artifacts_pf/_expansion_report_v4.json (research artifact; not loaded by SPA)
MOVED public/data/pf/_delivery_report_v4.md -> docs/research_artifacts_pf/_delivery_report_v4.md (research artifact; not loaded by SPA)
MOVED public/data/pf/_finance_delivery_v5.md -> docs/research_artifacts_pf/_finance_delivery_v5.md (research artifact; not loaded by SPA)
MOVED public/data/pf/_validation_v6.json -> docs/research_artifacts_pf/_validation_v6.json (research artifact; not loaded by SPA)
MOVED public/data/pf/_finance_validation_v5.json -> docs/research_artifacts_pf/_finance_validation_v5.json (research artifact; not loaded by SPA)
MOVED public/data/pf/_finance_expansion_v5_report.json -> docs/research_artifacts_pf/_finance_expansion_v5_report.json (research artifact; not loaded by SPA)
MOVED public/data/pf/_validation_v4.json -> docs/research_artifacts_pf/_validation_v4.json (research artifact; not loaded by SPA)
MOVED public/data/pf/research_queue.json -> docs/research_artifacts_pf/research_queue.json (research artifact; not loaded by SPA)
REMOVED public/data/pf/network.v5.bak.json (488.6 KB) superseded backup; recoverable in checkpoint
REMOVED public/data/pf/projects.v5.bak.json (308.6 KB) superseded backup; recoverable in checkpoint
MOVED public/data/pf/market.json -> docs/research_artifacts_pf/pf_market.json (SPA loads public/data/market.json)

## Size measurements

| Metric | Before | After |
|---|---|---|
| Full working tree | 403.0 MB | ~330 MB (still includes local `node_modules` / `.venv` / `opendart_cache`) |
| Source excl. node_modules/.venv/dist | 78.8 MB | ~12.0 MB (excl. opendart_cache) |
| Vite `dist/` total | 6.03 MB | **3.45 MB** |
| JS bundle (gzip) | 162.01 kB | 162.01 kB (unchanged code) |
| Distribution ZIP | — | **2.11 MB** (`contagion-map-clean-v0.5.1.zip`) |

Entity/relationship counts unchanged: semi 151/128 · PF 365/701.
