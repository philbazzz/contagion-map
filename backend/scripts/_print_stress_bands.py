from app.service import load_network
from app.engine.rate_shock import simulate_rate_shock

net = load_network()
for bp in (0, 50, 100, 200, 300, 450):
    r = simulate_rate_shock(net, bp, "sofr")
    s = r["origin_stress"]
    st = r["rounds"][0]["node_states"]["coreweave"]
    score = (s["score_delta_over_ocf"] or 0) * 100
    print(
        f"+{bp:3d}bp  level={s['level']:10s} score={score:5.2f}%  "
        f"intensity={s['intensity']:.3f}  status={st['status']}  "
        f"crit_sofr={s['critical_sofr_pct']}"
    )
