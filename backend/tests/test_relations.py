"""Network checks from the v0.4 request (§19 네트워크)."""
from app.engine.refinancing import simulate_refinancing
from app.engine.relations import network_stats, shortest_path


def test_every_map_entity_has_a_relationship_path(network):
    # v0.3 bug: map showed links but engines used edge subsets -> "계산 경로에 없음"
    for n in network["nodes"]:
        assert shortest_path(network, "coreweave", n["id"]) is not None, n["id"]


def test_known_paths(network):
    p = shortest_path(network, "coreweave", "sk_hynix")
    assert p["nodes"] == ["coreweave", "nvidia", "sk_hynix"] and p["hops"] == 2
    assert shortest_path(network, "sk_hynix", "mufg")["hops"] == 3
    assert shortest_path(network, "microsoft", "microsoft")["hops"] == 0


def test_every_relationship_has_evidence(network):
    sids = {s["id"] for s in network["sources"]}
    for e in network["edges"]:
        assert e["source_status"] in ("VERIFIED", "INFERRED")
        assert e["source_ids"] and set(e["source_ids"]) <= sids
    assert not any(n.get("is_demo") for n in network["nodes"])  # DEMO entities removed in v0.4


def test_engine_only_uses_map_edges(network):
    edge_ids = {e["id"] for e in network["edges"]}
    r = simulate_refinancing(network, "ddtl_3", 15, capex_absorption_pct=50, gpu_share_pct=50)
    for rd in r["rounds"]:
        assert set(rd["active_edges"]) <= edge_ids
        assert set(rd["node_states"]) <= {n["id"] for n in network["nodes"]}


def test_stats_are_counted_not_typed(network):
    s = network_stats(network, "coreweave")
    assert s["entities"] == len(network["nodes"])
    assert s["direct"] + s["indirect"] + s["unconnected"] == len(network["nodes"]) - 1
    assert s["indirect"] == 2  # SK hynix, TSMC (via NVIDIA)
    assert s["financing_contracts"] == 17


def test_arranger_is_not_treated_as_holder(network):
    ms = next(e for e in network["edges"] if e["id"] == "f_morgan_stanley")
    assert ms["amount_usd_m"] is None  # no holding amount invented
    assert any("Arranger" in r or "Agent" in r for r in ms["roles"])


def test_debt_reconciles_to_filing(network):
    total = sum(x["principal_usd_m"] or 0 for x in network["financials"]["instruments"])
    assert total == network["financials"]["totals"]["principal_usd_m"] == 35551
    assert sum(m["usd_m"] for m in network["financials"]["maturities"]) == 35551


def test_no_demo_entities_remain(network):
    # v0.4: DEMO institutions and their invented exposures were deleted
    assert not any(n.get("is_demo") or n["group"] == "demo" for n in network["nodes"])
    assert all(e["source_status"] in ("VERIFIED", "INFERRED") for e in network["edges"])


def test_path_is_labelled_by_supply_channel(network):
    # CoreWeave-NVIDIA has supply, equity and backstop links; the GPU route must use the supply link
    p = shortest_path(network, "coreweave", "sk_hynix")
    first = next(e for e in network["edges"] if e["id"] == p["edges"][0])
    assert first["impact_channel"] == "supply_chain"
