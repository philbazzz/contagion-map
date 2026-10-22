# Contagion Map — source package

This archive is a **source package**, not a standalone executable. You must install dependencies and build locally.

## Contents

- `frontend/` — React + Vite SPA (CoreWeave / AI Semiconductor + AI Data Center PF)
- `backend/` — FastAPI API, market/quotes helpers, data loaders (optional for static mode)
- `scripts/` — data refresh, DART research patches, coverage rebuild
- `docs/` — coverage tables, cleanup log, data notes
- `demo/` — optional offline demo (build with `npm run build:demo` in `frontend/`)
- `start.bat` / `start_backend.bat` / `preview.bat` — Windows launch helpers
- `backend/.env.example` — API key placeholders (copy to `backend/.env`)

## Requirements

- Node.js 18+ LTS
- Python 3.10+ (for backend / quote scripts)
- Optional API keys listed in `backend/.env.example`

## Quick start (static frontend only)

Application datasets under `frontend/public/data/` are already included. A Python venv is optional for a first static build.

```bat
cd frontend
npm install
set FETCH_QUOTES=0
npm run build
npm run preview
```

Open the printed local URL (default http://127.0.0.1:4173/).

If `prepare:static` cannot import backend Python packages, it keeps the bundled `network.json` and continues.

## Full local stack (API + Vite)

```bat
start.bat
```

Or:

```bat
start_backend.bat
cd frontend
npm install
set VITE_API_MODE=http
npm run dev
```

## Tests

```bat
run_tests.bat
```

Frontend schema/exposure checks:

```bat
cd frontend
node scripts/test_pfv_click_schema.mjs
node scripts/test_exposure_shock.mjs
```

## Not included in this ZIP

- `node_modules/`, `backend/.venv/`
- `.git/`
- Real `backend/.env` credentials
- `backend/data/opendart_cache/` (large DART ZIP cache; re-fetch with `OPEN_DART_API_KEY`)
- Prior checkpoints and nested archives

## Version

See `frontend/package.json` (`version` field) and archive filename `contagion-map-clean-v*`.
