import { readFileSync } from "node:fs";
import { simulateRateShock } from "../src/engine/rateShock";
import type { Network } from "../src/types";

const net = JSON.parse(readFileSync("./public/data/network.json", "utf8")) as Network;

function run(label: string, params: Parameters<typeof simulateRateShock>[1]) {
  const r = simulateRateShock(net, { benchmark: "sofr", sofr_pct: null, ...params });
  const last = r.rounds[r.rounds.length - 1].node_states;
  const crit = Object.entries(last).filter(([, s]) => s.stress === "critical").map(([id]) => id);
  console.log(label, {
    mode: r.summary.crisis_mode,
    cw: r.summary.stress_level,
    high: r.summary.companies_at_or_above_high,
    critN: r.summary.companies_critical,
    sec: r.summary.secondary_stressed,
    sector: r.summary.sector_stressed,
    spv: r.summary.spv_critical,
    critIds: crit.sort(),
  });
  return { r, last };
}

const a = run("A cw_default +0bp", { shock_bp: 0, crisis_mode: "cw_default" });
if ((a.r.summary.spv_critical || 0) < 1) throw new Error("A: expected SPV critical");
if (!(a.r.summary.secondary_stressed || 0)) throw new Error("A: expected secondary lessors");
if (a.last.hut8?.stress === "critical") throw new Error("A: Hut8 should not be critical under CW-default-only");
if (a.last.soluna?.stress === "critical") throw new Error("A: Soluna should not be critical");

const b = run("B financing +500bp", {
  shock_bp: 500, crisis_mode: "financing",
  refi_availability: "restricted", project_financing: "unavailable", horizon_months: 12,
});
if ((b.r.summary.sector_stressed || 0) < 1) throw new Error("B: expected sector stress");

run("C combined +500bp", {
  shock_bp: 500, crisis_mode: "combined",
  refi_availability: "unavailable", project_financing: "unavailable", horizon_months: 12,
});

const c = simulateRateShock(net, {
  shock_bp: 500, benchmark: "sofr", sofr_pct: null, crisis_mode: "combined",
  refi_availability: "unavailable", project_financing: "unavailable", horizon_months: 12,
});
const nscale = c.rounds[c.rounds.length - 1].node_states.nscale;
if (nscale && nscale.stress !== "insufficient" && nscale.status !== "insufficient") {
  throw new Error("Nscale must remain insufficient-data");
}

// SPV critical without forcing parent auto-default label
const spv = c.sector_stress.find((s) => s.entity_id === "corz_finance_i");
if (spv && spv.parent_auto_default !== false) throw new Error("SPV must not auto-default parent");

console.log("ASSERTIONS OK");
