/**
 * Tests A–G: underwriting ≠ exposure, repaid, refinance, unknown, multi-role, large shock, CoreWeave smoke.
 * Run: node frontend/scripts/test_exposure_shock.mjs
 */
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const net = JSON.parse(readFileSync(join(root, "public/data/pf/network.json"), "utf8"));

const PAST = new Set([
  "repaid", "terminated", "historical", "withdrawn", "expired", "refinanced", "transferred",
  "FULLY_REPAID", "REFINANCED", "TRANSFERRED", "EXPIRED", "HISTORICAL_ONLY", "SECURITIZED",
]);
const NON_LOSS = new Set([
  "ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT", "ASSET_MANAGER",
  "TRUST_SERVICES", "PRIORITY_BENEFICIARY", "HISTORICAL_FINANCING",
]);
const NON_AMT = new Set(["facility_total_context", "fee_paid", "underwrite_commitment"]);
const LOSS = new Set([
  "PROJECT_LOAN", "ACQUISITION_LOAN", "CORPORATE_LOAN", "BRIDGE_LOAN", "DIRECT_LOAN",
  "MORTGAGE_LOAN", "PROJECT_FINANCE_LOAN", "EQUITY_INVESTMENT", "EQUITY_SPONSOR",
  "PREFERRED_EQUITY", "SHAREHOLDER_LOAN", "SUBORDINATED_INVESTMENT", "ABS_HOLDING",
  "CREDIT_ENHANCEMENT", "COMPLETION_GUARANTEE", "DEBT_ASSUMPTION", "LOAN_GUARANTEE",
  "FINANCIAL_GUARANTEE", "LIQUIDITY_COMMITMENT", "REFINANCING_UNDERWRITE", "SHARE_PLEDGE",
]);

function shockEligible(e) {
  if (e.shock_eligible === false) return false;
  if (NON_LOSS.has(e.relationship_type)) return false;
  if (NON_AMT.has(e.amount_type || "")) return false;
  const st = (e.exposure_status || e.relationship_status || "");
  if (PAST.has(st) || PAST.has(st.toUpperCase()) || PAST.has(st.toLowerCase())) return false;
  if ((st || "").toUpperCase() === "UNVERIFIED") return false;
  if (!LOSS.has(e.relationship_type) && e.impact_channel !== "financial") return false;
  return true;
}

function assert(cond, msg) {
  if (!cond) throw new Error("FAIL: " + msg);
  console.log("PASS:", msg);
}

// --- synthetic fixtures for A–E ---
const fixtures = [
  {
    id: "tA",
    relationship_type: "ARRANGER",
    amount_krw_eok: 5000,
    amount_type: "facility_total_context",
    relationship_status: "historical",
    exposure_status: "HISTORICAL_ONLY",
    shock_eligible: false,
  },
  {
    id: "tB",
    relationship_type: "PROJECT_LOAN",
    amount_krw_eok: 0,
    amount_type: "outstanding",
    relationship_status: "repaid",
    exposure_status: "FULLY_REPAID",
  },
  {
    id: "tC_old",
    relationship_type: "BRIDGE_LOAN",
    relationship_status: "refinanced",
    exposure_status: "REFINANCED",
    amount_krw_eok: 1000,
  },
  {
    id: "tC_new",
    relationship_type: "MORTGAGE_LOAN",
    relationship_status: "funded",
    exposure_status: "ACTIVE_CONFIRMED",
    amount_krw_eok: 1000,
    amount_type: "outstanding",
  },
  {
    id: "tD",
    relationship_type: "PROJECT_LOAN",
    amount_krw_eok: null,
    amount_type: "historical_outstanding",
    relationship_status: "unknown",
    exposure_status: "UNVERIFIED",
  },
  {
    id: "tE_arr",
    relationship_type: "ARRANGER",
    shock_eligible: false,
    exposure_status: "HISTORICAL_ONLY",
  },
  {
    id: "tE_loan",
    relationship_type: "PROJECT_LOAN",
    amount_krw_eok: 200,
    amount_type: "outstanding",
    relationship_status: "funded",
    exposure_status: "ACTIVE_CONFIRMED",
  },
  {
    id: "tE_guar",
    relationship_type: "CREDIT_ENHANCEMENT",
    contingent_obligation: true,
    relationship_status: "committed",
    exposure_status: "ACTIVE_AMOUNT_UNKNOWN",
  },
];

assert(!shockEligible(fixtures[0]), "Test A — arranger 5000억 does not propagate loan loss");
assert(!shockEligible(fixtures[1]), "Test B — fully repaid bridge/loan excluded");
assert(!shockEligible(fixtures[2]), "Test C — refinanced original edge terminated");
assert(shockEligible(fixtures[3]), "Test C — successor mortgage remains eligible");
assert(!shockEligible(fixtures[4]), "Test D — UNVERIFIED balance not verified-loss path");
assert(!shockEligible(fixtures[5]), "Test E — arranger role separate / no loss");
assert(shockEligible(fixtures[6]), "Test E — lender role can propagate");
assert(shockEligible(fixtures[7]), "Test E — guarantor contingent path eligible (conditional)");

// --- live network invariants ---
const arrangerLoss = net.edges.filter(
  (e) => e.relationship_type === "ARRANGER" && shockEligible(e),
);
assert(arrangerLoss.length === 0, "Live net: no ARRANGER edge is shock-eligible");

const repaidLoss = net.edges.filter(
  (e) => (e.relationship_status === "repaid" || e.exposure_status === "FULLY_REPAID") && shockEligible(e),
);
assert(repaidLoss.length === 0, "Live net: repaid edges not shock-eligible");

const facilityAsExposure = net.edges.filter(
  (e) => e.amount_type === "facility_total_context" && shockEligible(e),
);
assert(facilityAsExposure.length === 0, "Live net: facility_total_context never shock-eligible");

const eligible = net.edges.filter(shockEligible);
assert(eligible.length > 0, "Live net: some economic edges remain eligible (" + eligible.length + ")");

// Test F — compact UI contract: affected list should not require auto-expanded cards
const uiSrc = readFileSync(join(root, "src/components/PfAffectedCompanies.tsx"), "utf8");
assert(uiSrc.includes("SHOCK IMPACT"), "Test F — compact SHOCK IMPACT panel exists");
assert(uiSrc.includes("expandedId"), "Test F — details only on expand");
assert(!uiSrc.includes("defaultExpanded={true}"), "Test F — no auto-expand all");

// Test G — CoreWeave mode regression smoke (semi network still present)
const semiPath = join(root, "public/data/network.json");
const semi = JSON.parse(readFileSync(semiPath, "utf8"));
assert(Array.isArray(semi.nodes) && semi.nodes.length > 10, "Test G — CoreWeave/semi network intact");
assert(semi.nodes.some((n) => (n.id || "").includes("coreweave") || (n.name || "").toLowerCase().includes("coreweave")
  || (n.name_ko || "").includes("CoreWeave") || n.id === "coreweave"), "Test G — coreweave node present");

console.log("\nAll exposure/shock tests passed.");
console.log("Eligible economic edges:", eligible.length, "/", net.edges.length);
