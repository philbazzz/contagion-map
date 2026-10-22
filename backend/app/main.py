"""CONTAGION — Financial Risk Universe : FastAPI backend (v0.5).

Run:  uvicorn app.main:app --reload --port 8000   (from the backend folder)
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import service
from .engine.rate_shock import ShockError
from .engine.refinancing import RefiError
from .models import RateShockRequest, RefinancingRequest


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = None
    m = service.market()
    if m.settings.scheduler_enabled:
        # checks the last collection time on startup, then every 30 minutes
        task = asyncio.create_task(m.run_forever())
    yield
    if task:
        task.cancel()


app = FastAPI(title="CONTAGION — Financial Risk Universe API", version="0.5.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return service.health()


@app.get("/api/network")
def network():
    return service.get_network()


@app.get("/api/entities/{entity_id}")
def entity(entity_id: str, origin: str = "coreweave"):
    data = service.get_entity(entity_id, origin=origin)
    if data is None:
        raise HTTPException(status_code=404, detail=f"unknown entity: {entity_id}")
    return data


@app.get("/api/stats")
def stats(origin: str = "coreweave"):
    data = service.get_stats(origin)
    if data is None:
        raise HTTPException(status_code=404, detail=f"unknown entity: {origin}")
    return data


@app.get("/api/paths")
def paths(a: str, b: str):
    data = service.get_path(a, b)
    if data is None:
        raise HTTPException(status_code=404, detail="unknown entity")
    return data


@app.post("/api/simulate/refinancing")
def simulate_refinancing(req: RefinancingRequest):
    try:
        return service.run_refinancing(req)
    except RefiError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/api/simulate/rate-shock")
def simulate_rate_shock(req: RateShockRequest):
    try:
        return service.run_rate_shock(req)
    except ShockError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/sources")
def sources():
    return service.get_sources()


@app.get("/api/market")
def market_overview():
    return service.market().overview()


@app.post("/api/market/refresh")
def market_refresh(source: Optional[str] = None):
    if source not in (None, "ust_10y", "ust_2y", "gpu_rent", "fx", "quotes_us", "quotes_krx"):
        raise HTTPException(status_code=400, detail="unknown source")
    return service.market().manual_refresh(source)


@app.get("/api/quotes")
def quotes():
    """Latest stored share prices + KRW conversion for every entity (unlisted / unsupported marked, never priced)."""
    return service.market().quotes()


@app.get("/api/quotes/{entity_id}/history")
def quote_history(entity_id: str, period: str = "1M"):
    if period not in ("1D", "1M", "3M", "6M", "1Y"):
        raise HTTPException(status_code=400, detail="period must be 1D, 1M, 3M, 6M or 1Y")
    data = service.market().quote_history(entity_id, period)
    if data is None:
        raise HTTPException(status_code=404, detail="unknown entity")
    return data


@app.post("/api/quotes/refresh")
def quotes_refresh(ecosystem: Optional[str] = None):
    """Refresh observed equity quotes.

    ecosystem=datacenter_pf — collect against the PF company network and write
    frontend/public/data/pf/quotes.json (used by the AI DC Contagion Map).
    Default — semiconductor CoreWeave network (existing behaviour).
    """
    if ecosystem in ("datacenter_pf", "pf", "ai_dc"):
        return service.market().refresh_pf_quotes()
    return service.market().refresh_quotes()


@app.get("/api/market/public-snapshot")
def market_public_snapshot():
    return service.market().public_snapshot()


@app.post("/api/runs")
def save_run(run: dict = Body(...)):
    try:
        return service.save_run(run)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/runs")
def list_runs(limit: int = 20):
    return service.list_runs(limit)


@app.get("/api/opendart/status")
def opendart_status():
    """Whether Open DART is configured. Never returns the API key."""
    from .opendart import get_client
    return get_client().status()


@app.post("/api/opendart/sync-corp-codes")
def opendart_sync_corp_codes():
    from .opendart import OpenDartError, get_client
    try:
        return get_client().sync_corp_codes()
    except OpenDartError as exc:
        raise HTTPException(status_code=503 if not exc.configured else 502, detail=str(exc))


@app.get("/api/opendart/company")
def opendart_company(name: str):
    from .opendart import OpenDartError, get_client
    try:
        return get_client().company_list(name)
    except OpenDartError as exc:
        raise HTTPException(status_code=503 if not exc.configured else 502, detail=str(exc))


@app.get("/api/opendart/disclosures")
def opendart_disclosures(corp_code: str, bgn_de: str, end_de: str, pblntf_ty: Optional[str] = None):
    from .opendart import OpenDartError, get_client
    try:
        return get_client().disclosure_list(corp_code=corp_code, bgn_de=bgn_de, end_de=end_de, pblntf_ty=pblntf_ty)
    except OpenDartError as exc:
        raise HTTPException(status_code=503 if not exc.configured else 502, detail=str(exc))


@app.get("/api/opendart/filing/{rcept_no}")
def opendart_filing(rcept_no: str):
    from .opendart import get_client
    return get_client().verify_edge_rcept(rcept_no)
