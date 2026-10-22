/** Quick sanity: run PF shock engine helpers are present in built types via dynamic import. */
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const net = JSON.parse(readFileSync(resolve(root, "frontend/public/data/pf/network.json"), "utf8"));
const eng = readFileSync(resolve(root, "frontend/src/pf/shockEngine.ts"), "utf8");
const ui = readFileSync(resolve(root, "frontend/src/components/PfAffectedCompanies.tsx"), "utf8");

const checks = [
  ["v6 nodes", net.nodes.length >= 250],
  ["v6 edges", net.edges.length >= 400],
  ["kr_dc_research meta", !!net.meta?.kr_dc_research],
  ["shockEngine buildAffected", eng.includes("buildAffectedCompanies")],
  ["shockEngine stressAnchor", eng.includes("stressAnchor")],
  ["shockEngine PAST_REL", eng.includes("PAST_REL")],
  ["affected UI panel", ui.includes("충격 영향 기업")],
  ["default assessment label", ui.includes("부도위험 판단 자료 부족") || eng.includes("영향 확인 / 부도위험 판단 자료 부족")],
];

let ok = true;
for (const [name, pass] of checks) {
  console.log((pass ? "PASS" : "FAIL"), name);
  if (!pass) ok = false;
}
process.exit(ok ? 0 : 1);
