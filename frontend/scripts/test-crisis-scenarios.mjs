/**
 * Quick crisis-mode assertions (runs against compiled logic via dynamic vite-node alternative).
 * Uses the TypeScript sources through `npx tsx` when available.
 */
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
const repo = resolve(root, "..");

const runner = `
import { readFileSync } from "node:fs";
import { simulateRateShock } from "./src/engine/rateShock.ts";

const net = JSON.parse(readFileSync("./public/data/network.json", "utf8"));

function run(label, params) {
  const r = simulateRateShock(net, { benchmark: "sofr", sofr_pct: null, ...params });
  const last = r.rounds[r.rounds.length - 1].node_states;
  const crit = Object.entries(last).filter(([, s]) => s.stress === "critical").map(([id]) => id);
  console.log(label, {
    mode: r.summary.crisis_mode,
    cw: r.summary.stress_level,
    high: r.summary.companies_at_or_above_high,
    crit: r.summary.companies_critical,
    sec: r.summary.secondary_stressed,
    sector: r.summary.sector_stressed,
    spv: r.summary.spv_critical,
    critIds: crit.sort(),
  });
  return r;
}

const a = run("A cw_default +0bp", { shock_bp: 0, crisis_mode: "cw_default" });
if (a.summary.spv_critical < 1) throw new Error("A: expected SPV critical");
if (!a.summary.secondary_stressed) throw new Error("A: expected secondary lessors");
// Parent must NOT auto-default solely because SPV is critical — CORZ may be secondary critical from lease, which is OK,
// but hut8 should stay out of critical under A-only.
const aLast = a.rounds[a.rounds.length - 1].node_states;
if (aLast.hut8?.stress === "critical") throw new Error("A: Hut8 should not be critical under CW-default-only");
if (aLast.soluna?.stress === "critical") throw new Error("A: Soluna should not be critical");

const b = run("B financing +500bp restricted/unavailable", {
  shock_bp: 500, crisis_mode: "financing",
  refi_availability: "restricted", project_financing: "unavailable", horizon_months: 12,
});
if ((b.summary.sector_stressed || 0) < 1) throw new Error("B: expected sector stress");

const c = run("C combined +500bp", {
  shock_bp: 500, crisis_mode: "combined",
  refi_availability: "unavailable", project_financing: "unavailable", horizon_months: 12,
});
if (c.summary.companies_critical <= a.summary.companies_critical) {
  console.warn("C crit count not strictly > A (may be equal if already maxed)", c.summary.companies_critical, a.summary.companies_critical);
}

const nscale = c.rounds[c.rounds.length - 1].node_states.nscale;
if (nscale && nscale.stress !== "insufficient" && nscale.status !== "insufficient") {
  throw new Error("Nscale must remain insufficient-data, not fake-safe or fake-critical");
}

console.log("ASSERTIONS OK");
`;

const tmp = resolve(root, "scripts", "_crisis_tmp.mts");
import { writeFileSync, unlinkSync } from "node:fs";
writeFileSync(tmp, runner);
try {
  execFileSync("npx", ["--yes", "tsx", tmp], {
    cwd: root,
    stdio: "inherit",
    env: { ...process.env, npm_config_devdir: undefined },
  });
} finally {
  try { unlinkSync(tmp); } catch { /* ignore */ }
}
