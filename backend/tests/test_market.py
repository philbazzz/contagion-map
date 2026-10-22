"""Market collectors with a fake transport — no network, no real keys."""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.market.collectors import (UST_10Y_SERIES, build_vast_query, collect_gpu_rent, collect_ust_10y,
                                   percent_to_bp, summarize_offers)
from app.market.config import DEFAULT_GPU_CONDITION, Settings
from app.market.overview import MarketService, gpu_overview, ust_10y_overview
from app.market.store import Store

FRED_KEY = "fredSECRETkey123"
VAST_KEY = "vastSECRETkey456"


def make(tmp_path, fred=FRED_KEY, vast=VAST_KEY):
    st = Settings(fred_api_key=fred, vast_api_key=vast, db_path=tmp_path / "m.db", scheduler_enabled=False,
                  http_retries=2, manual_refresh_min_interval_sec=0)
    return st, Store(st.db_path)


class Fake:
    """Routes requests by URL fragment; records calls."""
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body))
        for frag, resp in self.routes.items():
            if frag in url:
                r = resp(url, body) if callable(resp) else resp
                if isinstance(r, Exception):
                    raise r
                status, payload = r
                return status, {}, json.dumps(payload).encode() if not isinstance(payload, bytes) else payload
        return 404, {}, b"{}"


def fred_routes(values):
    obs = [{"date": d, "value": v} for d, v in values]
    return {"series/observations": (200, {"observations": obs}),
            "fred/series?": (200, {"seriess": [{"last_updated": "2026-10-16 08:59:00-05", "observation_start": "2023-10-17",
                                                 "observation_end": values[-1][0], "units": "Percent"}]})}


# ------------------------------------------------------------------ UST 10Y (HY OAS removed from Contagion Map)
def test_percent_to_bp():
    assert percent_to_bp(3.23) == 323.0
    assert percent_to_bp(0.015) == 1.5


def test_ust_collect_and_overview(tmp_path):
    st, store = make(tmp_path)
    fake = Fake(fred_routes([("2026-10-14", "4.10"), ("2026-10-15", "4.15")]))
    res = collect_ust_10y(st, store, transport=fake, sleep=lambda s: None)
    assert res["status"] == "ok"
    ov = ust_10y_overview(store, st, today=date(2026, 10, 16))
    assert ov["latest"] == {"value": 4.15, "obs_date": "2026-10-15"}
    assert ov["change_vs_previous"] == pytest.approx(0.05)
    assert ov["unit"] == "%" and ov["status"] == "ok"
    assert ov["trend"]["d7"]["status"] == "insufficient"
    assert ov["history"]["stored_from"] == "2026-10-14"


def test_ust_missing_value_and_weekend(tmp_path):
    st, store = make(tmp_path)
    collect_ust_10y(st, store, transport=Fake(fred_routes([("2026-10-15", "4.15"), ("2026-10-16", ".")])), sleep=lambda s: None)
    ov = ust_10y_overview(store, st, today=date(2026, 10, 19))
    assert ov["status"] == "missing_value"
    assert ov["latest"]["obs_date"] == "2026-10-15"
    st2, store2 = make(tmp_path / "b")
    collect_ust_10y(st2, store2, transport=Fake(fred_routes([("2026-10-15", "4.15")])), sleep=lambda s: None)
    assert ust_10y_overview(store2, st2, today=date(2026, 10, 19))["status"] == "weekend_or_holiday"
    assert ust_10y_overview(store2, st2, today=date(2026, 10, 28))["status"] == "stale"


def test_ust_no_key_shows_no_number(tmp_path):
    st, store = make(tmp_path, fred="")
    res = collect_ust_10y(st, store, transport=Fake({}))
    assert res["status"] == "no_key"
    ov = ust_10y_overview(store, st)
    assert ov["status"] == "no_key" and ov["latest"] is None


def test_ust_auth_error_and_rate_limit(tmp_path):
    st, store = make(tmp_path)
    bad = Fake({"fred/series?": (400, {"error_code": 400, "error_message": "Bad Request. The value for variable api_key is not registered."})})
    assert collect_ust_10y(st, store, transport=bad, sleep=lambda s: None)["status"] == "auth_error"
    rl = Fake({"fred/series?": (429, {"error": "too many"})})
    assert collect_ust_10y(st, store, transport=rl, sleep=lambda s: None)["status"] == "rate_limited"


def test_ust_failure_keeps_last_good_value(tmp_path):
    st, store = make(tmp_path)
    collect_ust_10y(st, store, transport=Fake(fred_routes([("2026-10-14", "4.10"), ("2026-10-15", "4.15")])), sleep=lambda s: None)
    res = collect_ust_10y(st, store, transport=Fake({"fred": TimeoutError()}), sleep=lambda s: None)
    assert res["status"] == "timeout"
    ov = ust_10y_overview(store, st, today=date(2026, 10, 16))
    assert ov["status"] == "fetch_failed"
    assert ov["latest"]["value"] == 4.15 and ov["latest"]["obs_date"] == "2026-10-15"
    assert ov["last_error"]["code"] == "timeout"


def test_ust_retries_on_server_error(tmp_path):
    st, store = make(tmp_path)
    seq = iter([(503, {}), (200, {"seriess": [{}]})])
    fake = Fake({"fred/series?": lambda u, b: next(seq), "series/observations": (200, {"observations": [{"date": "2026-10-15", "value": "4.2"}]})})
    assert collect_ust_10y(st, store, transport=fake, sleep=lambda s: None)["status"] == "ok"


def test_ust_upsert_has_no_duplicates(tmp_path):
    st, store = make(tmp_path)
    r = fred_routes([("2026-10-14", "4.10"), ("2026-10-15", "4.15")])
    collect_ust_10y(st, store, transport=Fake(r), sleep=lambda s: None)
    collect_ust_10y(st, store, transport=Fake(r), sleep=lambda s: None)
    assert len(store.observations(UST_10Y_SERIES)) == 2


# ------------------------------------------------------------------ GPU
OFFERS = [
    {"gpu_name": "H100 SXM", "num_gpus": 1, "gpu_ram": 81559, "dph_total": 2.00, "dph_base": 1.95},
    {"gpu_name": "H100 SXM", "num_gpus": 2, "gpu_ram": 81559, "dph_total": 5.00, "dph_base": 4.9},   # 2.50 per GPU
    {"gpu_name": "H100 SXM", "num_gpus": 8, "gpu_ram": 81559, "dph_total": 24.0, "dph_base": 23.0},  # 3.00 per GPU
    {"gpu_name": "H100 SXM", "num_gpus": 4, "gpu_ram": 81559, "dph_total": 14.0, "dph_base": 13.0},  # 3.50 per GPU
    {"gpu_name": "H100 PCIE", "num_gpus": 1, "gpu_ram": 81559, "dph_total": 1.10},                   # other product
    {"gpu_name": "H100 SXM", "num_gpus": 1, "gpu_ram": 81559, "dph_total": 0.5, "is_bid": True},     # interruptible
]


def test_gpu_per_gpu_normalisation_and_quantiles():
    s = summarize_offers(OFFERS, DEFAULT_GPU_CONDITION)
    assert s["offer_count"] == 4
    assert s["median"] == pytest.approx(2.75)           # median of 2.0, 2.5, 3.0, 3.5
    assert s["p25"] == pytest.approx(2.375) and s["p75"] == pytest.approx(3.125)
    assert s["min"] == 2.0 and s["max"] == 3.5


def test_gpu_query_keeps_conditions_explicit():
    q = build_vast_query(DEFAULT_GPU_CONDITION)
    assert q["type"] == "ondemand"
    assert q["gpu_name"] == {"in": ["H100 SXM"]}
    assert q["num_gpus"] == {"gte": 1, "lte": 8}


def test_gpu_snapshot_daily_and_history(tmp_path):
    st, store = make(tmp_path)
    fake = Fake({"bundles": (200, {"offers": OFFERS})})
    assert collect_gpu_rent(st, store, transport=fake, sleep=lambda s: None, today="2026-10-19")["status"] == "ok"
    again = collect_gpu_rent(st, store, transport=fake, sleep=lambda s: None, today="2026-10-19")
    assert again.get("duplicate") is True and len(fake.calls) == 1   # no duplicate call or row
    assert fake.calls[0][2]["Authorization"] == f"Bearer {VAST_KEY}"
    ov = gpu_overview(store, st, today=date(2026, 10, 19))
    assert ov["latest"]["median"] == pytest.approx(2.75)
    assert ov["trend"]["d7"]["status"] == "insufficient" and ov["trend"]["d30"]["label"] == "이력 부족"
    cheaper = [dict(o, dph_total=o["dph_total"] * 0.9) for o in OFFERS]
    collect_gpu_rent(st, store, transport=Fake({"bundles": (200, {"offers": cheaper})}), sleep=lambda s: None, today="2026-10-26")
    ov2 = gpu_overview(store, st, today=date(2026, 10, 26))
    assert ov2["trend"]["d7"]["status"] == "ok"
    assert ov2["trend"]["d7"]["change_pct"] == pytest.approx(-10.0)


def test_gpu_invalid_key_and_no_offers(tmp_path):
    st, store = make(tmp_path)
    r = collect_gpu_rent(st, store, transport=Fake({"bundles": (404, {"error": "Invalid user key"})}), sleep=lambda s: None)
    assert r["status"] == "auth_error"
    r = collect_gpu_rent(st, store, transport=Fake({"bundles": (200, {"offers": []})}), sleep=lambda s: None, today="2026-10-20")
    assert r["status"] == "no_data"
    assert gpu_overview(store, st)["latest"] is None


# ------------------------------------------------------------------ service / safety
def test_keys_never_leak_into_payloads(tmp_path):
    st, store = make(tmp_path)
    fake = Fake({**fred_routes([("2026-10-15", "3.23")]), "bundles": (200, {"offers": OFFERS})})
    ms = MarketService(st, store, transport=fake)
    ms.manual_refresh()
    for payload in (ms.overview(use_cache=False), ms.public_snapshot()):
        text = json.dumps(payload, ensure_ascii=False)
        assert FRED_KEY not in text and VAST_KEY not in text
    # failure path too
    ms2 = MarketService(*make(tmp_path / "x"), transport=Fake({"fred": TimeoutError(), "bundles": TimeoutError()}))
    ms2.manual_refresh()
    assert FRED_KEY not in json.dumps(ms2.overview(use_cache=False), ensure_ascii=False)


def test_public_snapshot_has_no_hy_oas(tmp_path):
    st, store = make(tmp_path)
    ms = MarketService(st, store, transport=Fake(fred_routes([("2026-10-15", "4.12")])))
    ms.collect("ust_10y")
    snap = ms.public_snapshot()
    assert all(i["id"] != "hy_oas" for i in snap["indicators"])
    assert any(i["id"] == "ust_10y" for i in snap["indicators"])
    assert snap["auto_update"] is False


def test_due_logic_and_lock(tmp_path):
    st, store = make(tmp_path)
    ms = MarketService(st, store, transport=Fake(fred_routes([("2026-10-15", "4.12")])))
    assert ms.due("ust_10y") is True
    ms.collect("ust_10y")
    assert ms.due("ust_10y") is False                      # refreshed within refresh window
    holder = store.acquire("collect:ust_10y")
    assert ms.collect("ust_10y")["status"] == "busy"       # duplicate run prevented
    store.release("collect:ust_10y", holder)


def test_runs_roundtrip(tmp_path):
    _, store = make(tmp_path)
    r = store.save_run({"event": "gpu_cut", "origin": "coreweave", "interest": "sk_hynix",
                        "params": {"gpu_investment_cut": 0.7}, "market": {"gpu_rent": {"median": 2.75}},
                        "summary": {"interest_score": 1.26}})
    runs = store.list_runs()
    assert runs[0]["id"] == r["id"] and runs[0]["summary"]["interest_score"] == 1.26
