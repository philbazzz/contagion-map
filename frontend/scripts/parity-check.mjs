/**
 * Checks that the in-browser engines (src/engine/*.ts, used by the standalone demo) give exactly
 * the same results as the Python engines on a broad set of scenarios.
 *
 *   cd frontend
 *   npm install
 *   npm run parity          (Python with the backend requirements must be on PATH)
 */
import * as esbuild from "esbuild";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const win = process.platform === "win32";
const venvPy = resolve(root, "backend", ".venv", win ? "Scripts/python.exe" : "bin/python");
const PY = existsSync(venvPy) ? venvPy : (win ? "python" : "python3");
const env = { ...process.env, MARKET_SCHEDULER: "false" };
console.log("parity python:", PY);

// one shared case list, run by both engines
const CASES = [];
const insts = ["ddtl_1", "ddtl_2", "ddtl_2_1", "ddtl_3", "ddtl_4", "ddtl_5", "notes_2030", "notes_2031_900", "notes_2032_eur",
  "conv_2032", "conv_2031", "oem_recourse", "magnetar_loan", "rcf"];
for (const id of insts) for (const rate of [9, 12, 15, 5]) for (const basis of ["stated", "effective"])
  CASES.push({ instrument_id: id, new_rate_pct: rate, basis, amount_usd_m: id === "rcf" ? 500 : null });
CASES.push({ instrument_id: "notes_2030", new_rate_pct: 12, success_ratio: 0.75, fee_pct: 1, new_tenor_years: 7 });
CASES.push({ instrument_id: "notes_2030", new_rate_pct: 12, capex_absorption_pct: 100, gpu_share_pct: 60 });
CASES.push({ instrument_id: "notes_2030", new_rate_pct: 12, capex_absorption_pct: 50 });
CASES.push({ instrument_id: "notes_2030", new_rate_pct: 8, capex_absorption_pct: 100, gpu_share_pct: 60 });
CASES.push({ instrument_id: "ddtl_3", new_rate_pct: 12, sofr_pct: 5.1, refi_date: "2027-03" });
CASES.push({ instrument_id: "ddtl_5_5", new_rate_pct: 12, amount_usd_m: 800 });
CASES.push({ instrument_id: "conv_2033", new_rate_pct: 9, amount_usd_m: 3700 });
CASES.push({ instrument_id: "ddtl_1", new_rate_pct: 12.375, compare_rates: [10, 13] });

const SHOCK_CASES = [
  { shock_bp: 50, benchmark: "sofr" },
  { shock_bp: 100, benchmark: "sofr" },
  { shock_bp: 200, benchmark: "sofr" },
  { shock_bp: 100, benchmark: "ust_10y" },
  { shock_bp: -50, benchmark: "sofr", sofr_pct: 5.1 },
];

const work = resolve(tmpdir(), `contagion-parity-${process.pid}`);
mkdirSync(work, { recursive: true });
const casesPath = resolve(work, "cases.json");
const shocksPath = resolve(work, "shocks.json");
const jsBundle = resolve(work, "run.cjs");
const jsOut = resolve(work, "js.json");
const pyOut = resolve(work, "py.json");
writeFileSync(casesPath, JSON.stringify(CASES), "utf8");
writeFileSync(shocksPath, JSON.stringify(SHOCK_CASES), "utf8");

const entry = `
import { readFileSync, writeFileSync } from "node:fs";
import { simulateRefinancing } from ${JSON.stringify(resolve(root, "frontend/src/engine/refinancing.ts"))};
import { simulateRateShock } from ${JSON.stringify(resolve(root, "frontend/src/engine/rateShock.ts"))};
import { networkStats, relationshipSummary, shortestPath } from ${JSON.stringify(resolve(root, "frontend/src/engine/relations.ts"))};
const net = JSON.parse(readFileSync(process.env.NET_PATH, "utf8"));
const cases = JSON.parse(readFileSync(process.env.CASES_PATH, "utf8"));
const shocks = JSON.parse(readFileSync(process.env.SHOCKS_PATH, "utf8"));
const out = {};
cases.forEach((c, i) => { try { out["r" + i] = simulateRefinancing(net, c); } catch (e) { out["r" + i] = { error: e.message }; } });
shocks.forEach((c, i) => { try { out["s" + i] = simulateRateShock(net, c); } catch (e) { out["s" + i] = { error: e.message }; } });
out.stats = networkStats(net, "coreweave");
for (const n of net.nodes) { out["rel_" + n.id] = relationshipSummary(net, "coreweave", n.id); out["p_sk_" + n.id] = shortestPath(net, "sk_hynix", n.id); }
writeFileSync(process.env.OUT_PATH, JSON.stringify(out), "utf8");
`;

const netPath = resolve(work, "network.json");
const netJson = execFileSync(PY, [resolve(root, "backend/export_network.py")], { cwd: root, env, maxBuffer: 64 << 20 }).toString();
writeFileSync(netPath, netJson, "utf8");

const built = await esbuild.build({
  stdin: { contents: entry, resolveDir: root, loader: "ts" },
  bundle: true, platform: "node", write: false, format: "cjs", logLevel: "error",
});
writeFileSync(jsBundle, built.outputFiles[0].text, "utf8");
execFileSync(process.execPath, [jsBundle], {
  env: { ...env, NET_PATH: netPath, CASES_PATH: casesPath, SHOCKS_PATH: shocksPath, OUT_PATH: jsOut },
  maxBuffer: 64 << 20,
});
const js = JSON.parse(readFileSync(jsOut, "utf8"));

const pyScript = resolve(work, "run_py.py");
writeFileSync(pyScript, `
import json, os, sys
sys.path.insert(0, ${JSON.stringify(resolve(root, "backend"))})
from app.service import load_network
from app.engine.refinancing import simulate_refinancing, RefiError
from app.engine.rate_shock import simulate_rate_shock, ShockError
from app.engine.relations import network_stats, relationship_summary, shortest_path
n = load_network()
cases = json.load(open(os.environ["CASES_PATH"], encoding="utf-8"))
shocks = json.load(open(os.environ["SHOCKS_PATH"], encoding="utf-8"))
out = {}
for i, c in enumerate(cases):
    try: out[f"r{i}"] = simulate_refinancing(n, **c)
    except RefiError as e: out[f"r{i}"] = {"error": str(e)}
for i, c in enumerate(shocks):
    try: out[f"s{i}"] = simulate_rate_shock(n, **c)
    except ShockError as e: out[f"s{i}"] = {"error": str(e)}
out["stats"] = network_stats(n, "coreweave")
for x in n["nodes"]:
    out["rel_" + x["id"]] = relationship_summary(n, "coreweave", x["id"])
    out["p_sk_" + x["id"]] = shortest_path(n, "sk_hynix", x["id"])
open(os.environ["OUT_PATH"], "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False))
`, "utf8");
execFileSync(PY, [pyScript], {
  cwd: root,
  env: { ...env, CASES_PATH: casesPath, SHOCKS_PATH: shocksPath, OUT_PATH: pyOut },
  maxBuffer: 64 << 20,
});
const py = JSON.parse(readFileSync(pyOut, "utf8"));

// Python prints 1.0 where JS prints 1; compare numbers by value
const canon = (x) => JSON.stringify(x, (_k, v) => (typeof v === "number" ? Math.round(v * 1e9) / 1e9 : v));
let bad = 0;
for (const k of new Set([...Object.keys(py), ...Object.keys(js)])) {
  if (canon(py[k]) !== canon(js[k])) {
    bad++;
    const a = canon(py[k]), b = canon(js[k]);
    let i = 0; while (i < a.length && a[i] === b[i]) i++;
    console.log("MISMATCH", k, "\n  py:", a.slice(Math.max(0, i - 80), i + 120), "\n  js:", (b || "").slice(Math.max(0, i - 80), i + 120));
  }
}
const nErr = Object.values(py).filter((v) => v && v.error).length;
console.log(bad ? `${bad} mismatches` : `parity OK (${Object.keys(py).length} results · ${CASES.length} refinancing + ${SHOCK_CASES.length} rate-shock cases, ${nErr} expected validation errors)`);
try { rmSync(work, { recursive: true, force: true }); } catch { /* ignore */ }
process.exit(bad ? 1 : 0);
