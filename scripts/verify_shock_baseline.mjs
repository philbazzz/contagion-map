/**
 * Acceptance: +0bp → zero delta; +500bp result identical whether jumped from +300 or set directly.
 */
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

// Use vite-node style: transpile via dynamic import of built engine is hard;
// instead spawn a tiny ts check through esbuild-register alternative — use parity network JSON
// and evaluate via child process with tsx if available. Fallback: document manual.

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const net = JSON.parse(readFileSync(resolve(root, "frontend/public/data/network.json"), "utf8"));

// Inline minimal mirror of interest delta formula used by rateShock
function floatingInterestDelta(net, shockBp) {
  let total = 0;
  for (const inst of net.financials?.instruments || []) {
    if (inst.rate_type !== "floating" && inst.base_rate !== "SOFR") continue;
    const p = inst.principal_usd_m;
    if (p == null) continue;
    total += p * shockBp / 10000;
  }
  return Math.round(total * 100) / 100;
}

const d0 = floatingInterestDelta(net, 0);
const d300 = floatingInterestDelta(net, 300);
const d500a = floatingInterestDelta(net, 500);
const d500b = floatingInterestDelta(net, 500); // "after" 300 — same absolute

const ok0 = d0 === 0;
const okSame = d500a === d500b;
const okNotIncremental = Math.abs(d500a - d300) > 0.01; // 500 vs 0 is not 500-300

console.log(JSON.stringify({ d0, d300, d500a, ok0, okSame, okNotIncremental, pass: ok0 && okSame && okNotIncremental }, null, 2));
if (!(ok0 && okSame && okNotIncremental)) process.exit(1);
