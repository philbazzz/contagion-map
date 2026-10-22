"""Rate-shock engine: exposure classification and SOFR floating sensitivity."""
from __future__ import annotations

from app.engine.rate_shock import simulate_rate_shock
from app.service import load_network


def _net():
    load_network.cache_clear()
    return load_network()


def test_sofr_shock_scales_with_bp():
    net = _net()
    r50 = simulate_rate_shock(net, 50, "sofr")
    r100 = simulate_rate_shock(net, 100, "sofr")
    r200 = simulate_rate_shock(net, 200, "sofr")
    d50 = r50["summary"]["total_incremental_interest_usd_m"]
    d100 = r100["summary"]["total_incremental_interest_usd_m"]
    d200 = r200["summary"]["total_incremental_interest_usd_m"]
    assert d50 is not None and d100 is not None and d200 is not None
    assert abs(d100 - 2 * d50) < 0.02
    assert abs(d200 - 2 * d100) < 0.02
    float_prin = r100["summary"]["floating_sofr_principal_usd_m"]
    assert abs(d100 - float_prin * 100 / 10000) < 0.02
    assert r100["summary"]["direct_measurable"] == 1  # CoreWeave only
    assert r100["assessments"]["coreweave"]["exposure_class"] == "direct_computed"
    assert r100["assessments"]["nvidia"]["exposure_class"] == "potential_indirect"
    # lenders are transmission channels, not financial losses
    assert r100["assessments"]["blackstone"]["exposure_class"] == "transmission_channel"


def test_ust_does_not_auto_apply_to_sofr():
    net = _net()
    r = simulate_rate_shock(net, 100, "ust_10y")
    assert r["summary"]["total_incremental_interest_usd_m"] is None
    assert r["assessments"]["coreweave"]["exposure_class"] == "qualitative_refi"
    assert "hy_oas" not in __import__("app.engine.rate_shock", fromlist=["BENCHMARKS"]).BENCHMARKS


def test_zero_shock_zero_delta():
    net = _net()
    r = simulate_rate_shock(net, 0, "sofr")
    assert r["summary"]["total_incremental_interest_usd_m"] == 0.0


def test_negative_shock():
    net = _net()
    r = simulate_rate_shock(net, -100, "sofr")
    d = r["summary"]["total_incremental_interest_usd_m"]
    assert d is not None and d < 0


def test_stress_bands_differentiate_100_vs_300():
    net = _net()
    r100 = simulate_rate_shock(net, 100, "sofr")
    r300 = simulate_rate_shock(net, 300, "sofr")
    s100 = r100["origin_stress"]
    s300 = r300["origin_stress"]
    assert s100 and s300
    assert s100["score_delta_over_ocf"] is not None and s300["score_delta_over_ocf"] is not None
    assert s300["score_delta_over_ocf"] > s100["score_delta_over_ocf"] * 2.5
    assert s300["intensity"] > s100["intensity"]
    # Visual status tokens must differ when bands differ, or intensity must differ when same band
    st100 = r100["rounds"][0]["node_states"]["coreweave"]
    st300 = r300["rounds"][0]["node_states"]["coreweave"]
    assert st100.get("intensity") != st300.get("intensity") or st100["status"] != st300["status"]
    assert s300["critical_sofr_pct"] is not None
    assert s300["level"] in ("moderate", "high", "critical")
