"""Financial-calculation checks from the v0.4 request (§19 금융 계산)."""
import copy

import pytest

from app.engine.refinancing import RefiError, existing_rate, simulate_refinancing

RED = {"defaulted", "origin_default"}


def run(net, **kw):
    kw.setdefault("instrument_id", "notes_2030")
    kw.setdefault("new_rate_pct", 12.0)
    return simulate_refinancing(net, **kw)


def test_fixed_coupon_delta_is_principal_times_rate_gap(network):
    r = run(network)
    # 2030 notes: $2,000M at 9.25% coupon (VERIFIED) -> 12%
    assert r["existing_rate"]["rate_pct"] == 9.25 and r["existing_rate"]["basis"] == "stated"
    assert r["result"]["annual_interest_existing_usd_m"] == pytest.approx(185.0)
    assert r["result"]["annual_interest_new_usd_m"] == pytest.approx(240.0)
    assert r["result"]["annual_interest_delta_usd_m"] == pytest.approx(55.0)
    assert r["result"]["rate_change_bp"] == pytest.approx(275.0)


def test_rate_cut_lowers_cost(network):
    r = run(network, new_rate_pct=8.0)
    assert r["result"]["annual_interest_delta_usd_m"] == pytest.approx(-25.0)
    # no propagation when the burden falls
    assert r["rounds"][3]["active_edges"] == [] and "nvidia" not in r["rounds"][3]["node_states"]


def test_only_target_instrument_changes(network):
    a = run(network, instrument_id="notes_2030", new_rate_pct=15)
    b = run(network, instrument_id="ddtl_3", new_rate_pct=15)
    # each result is computed on its own principal only, never on total debt ($35,551M)
    assert a["result"]["amount_usd_m"] == 2000 and b["result"]["amount_usd_m"] == 2215
    assert a["result"]["annual_interest_delta_usd_m"] == pytest.approx(2000 * (15 - 9.25) / 100)
    # the dataset itself is not mutated by a run
    before = copy.deepcopy(network["financials"])
    run(network, instrument_id="ddtl_4", new_rate_pct=20)
    assert network["financials"] == before


def test_floating_uses_sofr_plus_spread_and_floor(network):
    insts = {x["id"]: x for x in network["financials"]["instruments"]}
    ex = existing_rate(insts["ddtl_3"], "stated", 3.89)
    assert ex["rate_pct"] == pytest.approx(7.89) and "SOFR" in ex["formula"]
    ex0 = existing_rate(insts["ddtl_5"], "stated", -0.5 + 0.5)  # SOFR 0 -> floor 0
    assert ex0["rate_pct"] == pytest.approx(4.5)
    r = run(network, instrument_id="ddtl_3", new_rate_pct=12, sofr_pct=4.0)
    assert r["existing_rate"]["rate_pct"] == pytest.approx(8.0)
    assert r["result"]["annual_interest_delta_usd_m"] == pytest.approx(2215 * 4 / 100)


def test_effective_rate_basis_and_fallback(network):
    r = run(network, basis="effective")
    assert r["existing_rate"]["rate_pct"] == 10.0 and r["existing_rate"]["basis"] == "effective"
    # DDTL 2.0 spread is not disclosed as a single value -> falls back to 10-Q effective rate, with a warning
    r2 = run(network, instrument_id="ddtl_2", new_rate_pct=12)
    assert r2["existing_rate"]["basis"] == "effective" and r2["existing_rate"]["fallback"]
    assert any("유효이자율" in w for w in r2["warnings"])


def test_inferred_spread_is_labelled(network):
    r = run(network, instrument_id="ddtl_1", new_rate_pct=12)
    assert r["existing_rate"]["status"] == "INFERRED"
    assert any("분할상환" in w for w in r["warnings"])


def test_success_ratio_fee_and_funding_need(network):
    r = run(network, success_ratio=0.75, fee_pct=1.0)
    assert r["result"]["refinanced_usd_m"] == pytest.approx(1500)
    assert r["result"]["funding_need_usd_m"] == pytest.approx(500)
    assert r["result"]["one_off_fee_usd_m"] == pytest.approx(15)
    assert r["result"]["annual_interest_delta_usd_m"] == pytest.approx(1500 * 2.75 / 100)


def test_schedule_prorates_partial_years_and_repays_principal(network):
    r = run(network, refi_date="2030-06", new_tenor_years=2)
    rows = {x["year"]: x for x in r["schedule"]}
    assert rows[2030]["months"] == 7 and rows[2031]["months"] == 12 and rows[2032]["months"] == 5
    assert rows[2030]["interest_delta_usd_m"] == pytest.approx(55 * 7 / 12, abs=1e-3)
    assert rows[2032]["principal_usd_m"] == pytest.approx(2000)
    assert sum(x["months"] for x in r["schedule"]) == 24


def test_comparison_uses_same_debt_and_assumptions(network):
    r = run(network, success_ratio=0.9, fee_pct=0.5)
    a, b, c = r["comparison"]
    assert [a["new_rate_pct"], b["new_rate_pct"], c["new_rate_pct"]] == [9.0, 12.0, 15.0]
    assert a["refinanced_usd_m"] == b["refinanced_usd_m"] == c["refinanced_usd_m"] == pytest.approx(1800)
    assert b["annual_interest_delta_usd_m"] - a["annual_interest_delta_usd_m"] == pytest.approx(1800 * 3 / 100)


def test_no_downstream_numbers_without_assumptions(network):
    r = run(network)
    assert r["assumption_chain"]["capex_cut_usd_m"] is None
    final = r["rounds"][-1]["node_states"]
    assert final["nvidia"]["category"] == "relationship_only"
    assert final["sk_hynix"]["status"] == "potential"
    assert r["assessments"]["sk_hynix"]["values"] == []


def test_assumption_chain_math(network):
    r = run(network, capex_absorption_pct=100, gpu_share_pct=60)
    ch = r["assumption_chain"]
    assert ch["capex_cut_usd_m"] == pytest.approx(55.0)
    assert ch["gpu_purchase_cut_usd_m"] == pytest.approx(33.0)
    assert ch["gpu_cut_vs_nvidia_revenue_pct"] == pytest.approx(33.0 / 215900 * 100, abs=1e-6)
    assert r["assessments"]["nvidia"]["category"] == "assumed"
    # SK hynix still has no number: its share of NVIDIA HBM purchases is not public
    assert r["assessments"]["sk_hynix"]["category"] == "relationship_only"


def test_financial_and_industrial_kept_apart_and_never_red(network):
    r = run(network, new_rate_pct=30, capex_absorption_pct=100, gpu_share_pct=100)
    for rd in r["rounds"]:
        assert not (RED & {s["status"] for s in rd["node_states"].values()})
    # lenders are contract parties with no computed loss
    r3 = run(network, instrument_id="ddtl_3", new_rate_pct=15)
    assert r3["rounds"][0]["node_states"]["morgan_stanley"]["status"] == "contract_party"
    assert r3["assessments"]["morgan_stanley"]["values"] == []


def test_input_validation(network):
    with pytest.raises(RefiError):
        run(network, instrument_id="nope")
    with pytest.raises(RefiError):
        run(network, new_rate_pct=50)
    with pytest.raises(RefiError):  # DDTL 5.5 has no disclosed balance at 6/30
        run(network, instrument_id="ddtl_5_5")
    ok = run(network, instrument_id="ddtl_5_5", amount_usd_m=1000)
    assert ok["existing_rate"]["rate_pct"] == pytest.approx(network["financials"]["market_inputs"]["sofr_pct"] + 5.5)


def test_inferred_existing_rate_warns(network):
    r = run(network, instrument_id="ddtl_1")  # spread 9.62% is a secondary-source value
    assert r["existing_rate"]["status"] == "INFERRED"
    assert any("INFERRED" in w for w in r["warnings"])


def test_assumed_values_appear_only_from_their_stage(network):
    r = run(network, capex_absorption_pct=100, gpu_share_pct=60)
    nv = r["assessments"]["nvidia"]
    assert {v["round"] for v in nv["values"]} == {3}            # GPU Supply Chain (S4)
    assert "nvidia" not in r["rounds"][2]["node_states"]      # not yet at S3
    assert r["rounds"][3]["node_states"]["nvidia"]["status"] == "assumed"
