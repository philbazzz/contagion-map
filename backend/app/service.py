"""Framework-independent service layer.

Both the FastAPI app (main.py) and the zero-dependency fallback server (serve_simple.py)
call these functions, so results are identical. The 3D map, the relationship paths and the
refinancing engine all read the ONE network assembled here, which removes the v0.3 cause of
"계산 경로에 없음" (the map and the engines used different edge subsets).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .engine.rate_shock import ShockError, simulate_rate_shock
from .engine.refinancing import RefiError, next_maturity_id, simulate_refinancing
from .engine.relations import network_stats, relationship_summary, shortest_path
from .models import CommercialContract, Entity, Instrument, RateShockRequest, RefinancingRequest, Relationship, Source

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_ORIGIN = "coreweave"

_market = None


def market():
    """Lazily created market-data service (SQLite + collectors)."""
    global _market
    if _market is None:
        from .market.overview import MarketService
        _market = MarketService()
    return _market


def save_run(run: dict) -> dict:
    """Store a run's inputs, the market data shown at run time and its key results (for reproduction)."""
    if not run.get("event"):
        raise ValueError("event is required")
    return market().store.save_run(run)


def list_runs(limit: int = 20) -> list:
    return market().store.list_runs(limit)


def _read(name: str, data_dir: Path) -> dict:
    return json.loads((data_dir / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=4)
def load_network(data_dir: str = str(DATA_DIR)) -> dict:
    d = Path(data_dir)
    ent = _read("entities.json", d)
    rel = _read("relationships.json", d)
    fin = _read("financials.json", d)
    src = _read("sources.json", d)
    con = _read("contracts.json", d)
    nodes = [Entity.model_validate(x).model_dump() for x in ent["entities"]]
    edges = [Relationship.model_validate(x).model_dump() for x in rel["relationships"]]
    fin["instruments"] = [Instrument.model_validate(x).model_dump() for x in fin["instruments"]]
    sources = [Source.model_validate(x).model_dump() for x in src["sources"]]
    contracts = [CommercialContract.model_validate(x).model_dump() for x in con["contracts"]]
    profiles_path = d / "profiles.json"
    profiles = _read("profiles.json", d) if profiles_path.exists() else {"profiles": {}}
    net = {
        "meta": ent["meta"], "sources": sources, "nodes": nodes, "edges": edges,
        "financials": fin, "contracts": contracts, "profiles": profiles.get("profiles") or {},
    }
    _check_integrity(net)
    net["meta"]["next_maturity_id"] = next_maturity_id(net)
    return net


def _check_integrity(net: dict) -> None:
    ids = [n["id"] for n in net["nodes"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate entity id")
    idset = set(ids)
    sids = {s["id"] for s in net["sources"]}
    seen = set()
    for e in net["edges"]:
        if e["id"] in seen:
            raise ValueError(f"duplicate relationship id {e['id']}")
        seen.add(e["id"])
        if e["source"] not in idset or e["target"] not in idset:
            raise ValueError(f"relationship {e['id']} references unknown entity")
        if e["source_status"] in ("VERIFIED", "INFERRED") and not e["source_ids"]:
            raise ValueError(f"relationship {e['id']} has no source")
    inst_ids = {x["id"] for x in net["financials"]["instruments"]}
    for x in net["financials"]["instruments"]:
        for p in x["participants"]:
            if p["entity"] not in idset:
                raise ValueError(f"instrument {x['id']} participant {p['entity']} unknown")
    com_ids = {c["id"] for c in net["contracts"]}
    for c in net["contracts"]:
        if c["counterparty"] not in idset:
            raise ValueError(f"contract {c['id']} counterparty {c['counterparty']} unknown")
        if c["status"] in ("VERIFIED", "INFERRED") and not c["source_ids"]:
            raise ValueError(f"contract {c['id']} has no source")
    for e in net["edges"]:
        for c in e["commercial_ids"]:
            if c not in com_ids:
                raise ValueError(f"relationship {e['id']} cites unknown commercial contract {c}")
    for item in net["nodes"] + net["edges"] + net["financials"]["instruments"] + net["contracts"]:
        for s in item.get("source_ids", []):
            if s not in sids:
                raise ValueError(f"{item['id']} cites unknown source {s}")
    for e in net["edges"]:
        for c in e["contract_ids"]:
            if c not in inst_ids:
                raise ValueError(f"relationship {e['id']} cites unknown contract {c}")


def health() -> dict:
    net = load_network()
    return {"status": "ok", "nodes": len(net["nodes"]), "edges": len(net["edges"]),
            "instruments": len(net["financials"]["instruments"]), "as_of": net["meta"].get("as_of")}


def get_network() -> dict:
    return load_network()


def get_stats(origin: str = DEFAULT_ORIGIN) -> Optional[dict]:
    net = load_network()
    if origin not in {n["id"] for n in net["nodes"]}:
        return None
    return network_stats(net, origin)


def get_sources() -> dict:
    net = load_network()
    counts = {"VERIFIED": 0, "INFERRED": 0, "ASSUMED": 0, "UNKNOWN": 0}
    for item in net["nodes"] + net["edges"]:
        counts[item["source_status"]] = counts.get(item["source_status"], 0) + 1
    return {"sources": net["sources"], "status_counts": counts, "meta": net["meta"]}


def get_path(a: str, b: str) -> Optional[dict]:
    net = load_network()
    ids = {n["id"] for n in net["nodes"]}
    if a not in ids or b not in ids:
        return None
    return {"from": a, "to": b, "path": shortest_path(net, a, b)}


def get_entity(entity_id: str, origin: str = DEFAULT_ORIGIN) -> Optional[dict]:
    net = load_network()
    nodes = {n["id"]: n for n in net["nodes"]}
    if entity_id not in nodes or origin not in nodes:
        return None
    links = [dict(e, counterpart=nodes[e["target"] if e["source"] == entity_id else e["source"]]["name"])
             for e in net["edges"] if entity_id in (e["source"], e["target"])]
    contracts = [x for x in net["financials"]["instruments"]
                 if any(p["entity"] == entity_id for p in x["participants"]) or (entity_id == "coreweave")]
    return {"entity": nodes[entity_id], "links": links, "contracts": [x["id"] for x in contracts],
            "relation": relationship_summary(net, origin, entity_id)}


def run_refinancing(req: RefinancingRequest) -> dict:
    return simulate_refinancing(load_network(), **req.model_dump())


def run_rate_shock(req: RateShockRequest) -> dict:
    return simulate_rate_shock(load_network(), **req.model_dump())


__all__ = ["RefiError", "ShockError"]
