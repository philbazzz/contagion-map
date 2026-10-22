"""Validate secondary contagion under extreme SOFR shocks."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.engine.rate_shock import simulate_rate_shock  # noqa: E402
from app.service import load_network  # noqa: E402


def main() -> None:
    net = load_network()
    assert any(n["id"] == "galaxy_digital" for n in net["nodes"]), "galaxy_digital missing"
    print("nodes", len(net["nodes"]))
    for bp in (100, 300, 450, 500, 700):
        r = simulate_rate_shock(net, shock_bp=bp, benchmark="sofr")
        s = r["summary"]
        sec = r.get("secondary_stress") or []
        print(
            f"+{bp}bp CW={s['stress_level']} high={s['companies_at_or_above_high']} "
            f"crit={s['companies_critical']} sec={s['secondary_stressed']} "
            f"secCrit={s['secondary_critical']}"
        )
        for x in sec:
            print(f"   {x['entity_id']}: {x['level']} | {x['label_en']}")
        st2 = r["rounds"][2]["node_states"]
        stressed = {k: v.get("stress") for k, v in st2.items() if v.get("stress") in ("moderate", "high", "critical")}
        print("   stage2:", stressed)

    # Expectations at +700
    r700 = simulate_rate_shock(net, shock_bp=700, benchmark="sofr")
    assert r700["summary"]["stress_level"] == "critical"
    by = {x["entity_id"]: x["level"] for x in r700["secondary_stress"]}
    assert by.get("core_scientific") == "critical", by
    assert by.get("applied_digital") == "critical", by
    assert by.get("galaxy_digital") == "critical", by
    print("ASSERT +700 secondary critical OK")

    r300 = simulate_rate_shock(net, shock_bp=300, benchmark="sofr")
    by300 = {x["entity_id"]: x["level"] for x in r300["secondary_stress"]}
    assert "core_scientific" in by300, by300
    print("ASSERT +300 CORZ secondary OK:", by300)


if __name__ == "__main__":
    main()
