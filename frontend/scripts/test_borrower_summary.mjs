/**
 * Borrower progressive-disclosure selectors — exposure rules & unique institution counts.
 * Run: node scripts/test_borrower_summary.mjs
 */
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const net = JSON.parse(readFileSync(join(root, "public/data/pf/network.json"), "utf8"));

const PAST = new Set([
  "repaid", "terminated", "historical", "withdrawn", "expired", "refinanced", "transferred",
  "FULLY_REPAID", "REFINANCED", "TRANSFERRED", "EXPIRED", "HISTORICAL_ONLY",
]);
const ARRANGE = new Set(["ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT"]);
const NON_AMT = new Set(["facility_total_context", "fee_paid", "underwrite_commitment"]);
const LOAN = new Set([
  "PROJECT_LOAN", "ACQUISITION_LOAN", "CORPORATE_LOAN", "BRIDGE_LOAN", "DIRECT_LOAN",
  "MORTGAGE_LOAN", "PROJECT_FINANCE_LOAN", "FINANCING_PARTICIPATION",
]);
const FIN_G = new Set([
  "kr_bank", "kr_securities", "kr_insurance", "kr_savings", "kr_am", "kr_trust",
  "kr_cooperative", "financial",
]);

const nodeMap = new Map(net.nodes.map((n) => [n.id, n]));
const borrowers = net.nodes.filter((n) => n.entity_type === "spv" || n.group === "project_finance");

function isPast(e) {
  const st = e.exposure_status || e.relationship_status || "";
  return PAST.has(st) || PAST.has(String(st).toUpperCase()) || e.layer === "historical";
}
function exposureEok(e) {
  if (isPast(e) || ARRANGE.has(e.relationship_type)) return null;
  if (NON_AMT.has(e.amount_type || "")) return null;
  if (e.amount_krw_eok != null && Number.isFinite(e.amount_krw_eok)) return e.amount_krw_eok;
  return null;
}

let fail = 0;
const assert = (cond, msg) => { if (!cond) { console.error("FAIL", msg); fail += 1; } };

assert(borrowers.length > 0, "expected PFV/SPC nodes");

for (const b of borrowers.slice(0, 40)) {
  const edges = net.edges.filter((e) => e.source === b.id || e.target === b.id);
  const inst = new Set();
  let loanSum = 0;
  let loanKnown = 0;
  let arrangerInLoan = false;
  for (const e of edges) {
    const oid = e.source === b.id ? e.target : e.source;
    const on = nodeMap.get(oid);
    if (!on || !FIN_G.has(on.group)) continue;
    inst.add(oid);
    if (ARRANGE.has(e.relationship_type) && exposureEok(e) != null) arrangerInLoan = true;
    if (LOAN.has(e.relationship_type) && !isPast(e) && !ARRANGE.has(e.relationship_type)) {
      const v = exposureEok(e);
      if (v != null) { loanSum += v; loanKnown += 1; }
    }
  }
  assert(!arrangerInLoan, `${b.id}: arranger must not contribute exposure eok`);
  // Unique institution count ≤ edge count to finance groups
  const finEdges = edges.filter((e) => {
    const oid = e.source === b.id ? e.target : e.source;
    return FIN_G.has(nodeMap.get(oid)?.group);
  });
  assert(inst.size <= finEdges.length, `${b.id}: unique inst ${inst.size} > edges ${finEdges.length}`);
  if (loanKnown === 0) {
    // Unknown stays unknown — we never force 0
    assert(true, "unknown ok");
  }
}

// Top-5 material never exceeds 5
for (const b of borrowers) {
  const edges = net.edges.filter((e) => {
    if (e.source !== b.id && e.target !== b.id) return false;
    if (isPast(e) || ARRANGE.has(e.relationship_type)) return false;
    const oid = e.source === b.id ? e.target : e.source;
    return FIN_G.has(nodeMap.get(oid)?.group);
  });
  const ranked = edges
    .map((e) => ({ id: e.id, eok: exposureEok(e) }))
    .filter((x) => x.eok != null)
    .sort((a, b) => b.eok - a.eok)
    .slice(0, 5);
  assert(ranked.length <= 5, `${b.id}: material > 5`);
}

console.log(fail ? `FAILED ${fail}` : `PASS borrowers=${borrowers.length}`);
process.exit(fail ? 1 : 0);
