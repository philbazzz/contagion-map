"""API tests. FastAPI tests run when FastAPI is installed; the fallback server
is always tested over real HTTP."""
import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest


def _check_contract(get, post):
    qs = get("/api/quotes")  # unlisted / unsupported never get invented prices
    for it in qs["items"]:
        if it.get("status") in ("unlisted", "not_supported"):
            assert it.get("price") is None
    assert {it["status"] for it in qs["items"]} <= {
        "no_key", "unlisted", "not_supported", "pending", "ok", "stale", "bad_response", "partial",
    }
    assert get("/api/quotes/nvidia/history?period=1D")["status"] == "not_supported"
    assert get("/api/health")["status"] == "ok"
    net = get("/api/network")
    assert len(net["nodes"]) >= 20 and len(net["edges"]) >= 25 and net["financials"]["instruments"]
    ent = get("/api/entities/sk_hynix")
    assert ent["entity"]["name"] == "SK hynix"
    assert ent["relation"]["path"]["nodes"] == ["coreweave", "nvidia", "sk_hynix"]
    assert ent["relation"]["kind"] == "indirect"
    assert len(get("/api/sources")["sources"]) >= 10
    st = get("/api/stats")
    assert st["entities"] == len(net["nodes"]) and st["indirect"] >= 2
    assert get("/api/paths?a=sk_hynix&b=mufg")["path"]["hops"] == 3

    a = post("/api/simulate/refinancing", {"instrument_id": "notes_2030", "new_rate_pct": 12})
    b = post("/api/simulate/refinancing", {"instrument_id": "notes_2030", "new_rate_pct": 15})
    assert a["result"]["annual_interest_delta_usd_m"] == pytest.approx(55.0)
    assert b["result"]["annual_interest_delta_usd_m"] == pytest.approx(115.0)
    assert len(a["rounds"]) == 6 and a["rounds"][0]["title"].startswith("STAGE 1")

    mk = get("/api/market")
    ids = {i["id"]: i for i in mk["indicators"]}
    assert "hy_oas" not in ids
    assert "ust_10y" in ids and "ust_2y" in ids
    pub = get("/api/market/public-snapshot")
    assert pub["auto_update"] is False
    assert all(i["id"] != "hy_oas" for i in pub["indicators"])

    saved = post("/api/runs", {"event": "refinancing", "origin": "coreweave", "interest": "sk_hynix",
                               "params": {"instrument_id": "notes_2030", "new_rate_pct": 12},
                               "summary": {"annual_interest_delta_usd_m": 55.0}})
    assert any(r["id"] == saved["id"] for r in get("/api/runs"))


def test_fastapi_app():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from app.main import app
    client = TestClient(app)

    def get(p):
        r = client.get(p)
        assert r.status_code == 200, r.text
        return r.json()

    def post(p, body):
        r = client.post(p, json=body)
        assert r.status_code == 200, r.text
        return r.json()

    _check_contract(get, post)
    assert client.get("/api/entities/unknown").status_code == 404
    assert client.post("/api/simulate/refinancing", json={"instrument_id": "notes_2030", "new_rate_pct": 99}).status_code == 422
    assert client.post("/api/simulate/refinancing", json={"instrument_id": "ddtl_5_5", "new_rate_pct": 9}).status_code == 422


def test_fallback_server():
    from serve_simple import Handler
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{port}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def get(p):
        with opener.open(base + p) as r:
            return json.loads(r.read())

    def post(p, body):
        req = urllib.request.Request(base + p, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with opener.open(req) as r:
            return json.loads(r.read())

    try:
        _check_contract(get, post)
    finally:
        srv.shutdown()
