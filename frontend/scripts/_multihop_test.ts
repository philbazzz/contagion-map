/**
 * Multi-hop contagion validation:
 * 1) Synthetic A→B→C→D→E chain (orders 1..4)
 * 2) Real CW-default path including order-3 pathway to MS/JPM
 */
import { readFileSync } from "node:fs";
import { propagateContagion, propagateSyntheticChain } from "../src/engine/multiHopContagion";
import { simulateRateShock } from "../src/engine/rateShock";
import type { Network } from "../src/types";

// ---- Synthetic ----
const syn = propagateSyntheticChain(["A", "B", "C", "D", "E"], 6);
const by = Object.fromEntries(syn.events.map((e) => [e.entity_id, e]));
console.log("SYNTHETIC", syn.events.map((e) => `${e.entity_id}@L${e.order}:${e.level}/${e.impact_kind}`));
if (by.B?.order !== 1) throw new Error(`B should be order 1, got ${by.B?.order}`);
if (by.C?.order !== 2) throw new Error(`C should be order 2, got ${by.C?.order}`);
if (by.D?.order !== 3) throw new Error(`D should be order 3, got ${by.D?.order}`);
if (by.E?.order !== 4) throw new Error(`E should be order 4, got ${by.E?.order}`);
if (syn.max_order_reached < 3) throw new Error("synthetic max order < 3");
console.log("SYNTHETIC ORDERS OK");

// Cycle: should terminate
const cycleNet = {
  meta: { name: "c", as_of: "", currency_unit: "USD", disclaimer: "", status_legend: {} },
  sources: [],
  nodes: ["A", "B", "C"].map((id) => ({
    id, name: id, group: "demo", sector: "", entity_type: "company", role: "", description: "",
    listed: false, ticker: null, exchange: null, quote_currency: null, listing_note: null,
    display_size: 3, source_status: "ASSUMED" as const, source_ids: [], key_drivers: [],
  })),
  edges: [
    { id: "e0", source: "A", target: "B", relationship_type: "LESSOR", impact_channel: "facility" as const,
      label: "", impact_label: "", source_status: "ASSUMED" as const, source_ids: [], contract_ids: [],
      commercial_ids: [], amount_usd_m: null, amount_note: "", roles: [], explanation: "" },
    { id: "e1", source: "B", target: "C", relationship_type: "PARENT_SPV", impact_channel: "financial" as const,
      label: "", impact_label: "", source_status: "ASSUMED" as const, source_ids: [], contract_ids: [],
      commercial_ids: [], amount_usd_m: null, amount_note: "", roles: [], explanation: "" },
    { id: "e2", source: "C", target: "B", relationship_type: "PARENT_SPV", impact_channel: "financial" as const,
      label: "", impact_label: "", source_status: "ASSUMED" as const, source_ids: [], contract_ids: [],
      commercial_ids: [], amount_usd_m: null, amount_note: "", roles: [], explanation: "" },
  ],
  financials: {} as Network["financials"],
  contracts: [],
} as Network;

// Temporarily rely on synthetic lessor for B via propagateSynthetic — for cycle use propagateContagion after injecting
import { CW_LESSOR_EXPOSURES } from "../src/engine/secondaryContagion";
const prev = [...CW_LESSOR_EXPOSURES];
CW_LESSOR_EXPOSURES.length = 0;
CW_LESSOR_EXPOSURES.push({
  entity_id: "B", name: "B", tier: "sole_segment", contract_value_usd_m: 1,
  concentration_note: "syn", source_ids: [], edge_prefer: "facility",
});
try {
  const cyc = propagateContagion(cycleNet, "A", "critical", 500, { maxOrder: 6 });
  console.log("CYCLE events", cyc.events.length, "stopped", cyc.stopped_reason);
  if (cyc.events.length > 20) throw new Error("cycle blew up");
  console.log("CYCLE OK");
} finally {
  CW_LESSOR_EXPOSURES.length = 0;
  CW_LESSOR_EXPOSURES.push(...prev);
}

// ---- Real network ----
const net = JSON.parse(readFileSync("./public/data/network.json", "utf8")) as Network;
const r = simulateRateShock(net, {
  shock_bp: 0, benchmark: "sofr", sofr_pct: null, crisis_mode: "cw_default",
});
console.log("REAL cw_default", {
  orders: `${r.summary.order1}/${r.summary.order2}/${r.summary.order3_plus}`,
  max: r.summary.max_contagion_order,
  quant: r.summary.quantified_contagion,
  path: r.summary.pathway_only,
  stages: r.rounds.length,
});
if ((r.summary.max_contagion_order || 0) < 3) {
  console.warn("WARN: max order < 3 — listing events:");
  console.log(r.contagion.events.map((e) => `${e.entity_id}@${e.order}:${e.impact_kind}/${e.level}`));
  throw new Error("Expected at least order-3 pathway (MS/JPM) under CW default");
}
if (r.rounds.length < 6) throw new Error(`Expected 6 replay stages, got ${r.rounds.length}`);

const o3 = r.contagion.events.filter((e) => e.order >= 3);
const pathwayBanks = o3.filter((e) =>
  (e.entity_id === "morgan_stanley" || e.entity_id === "jpmorgan") && e.impact_kind === "pathway");
if (!pathwayBanks.length) {
  console.log("order3 events", o3);
  throw new Error("Expected MS/JPM as order-3 pathway (not quantified bank default)");
}
// Banks must NOT be critical
for (const b of pathwayBanks) {
  if (b.level === "critical" || b.level === "high") throw new Error("Bank must not shatter from arranger role");
}

const mac = r.contagion.events.find((e) => e.entity_id === "macquarie");
if (mac && mac.order !== 2) console.warn("Macquarie order", mac.order, mac);
if (mac && mac.level === "critical") throw new Error("Macquarie must not auto-critical");

console.log("REAL PATH OK", {
  o3: o3.map((e) => `${e.entity_id}:${e.impact_kind}`),
  mac: mac ? `${mac.order}/${mac.level}` : "n/a",
});

// Replay stages include order-3 content in stage index 3
const stage3 = r.rounds[3];
if (!stage3.title.includes("3rd")) throw new Error(`Stage 3 title unexpected: ${stage3.title}`);
console.log("REPLAY STAGES OK", r.rounds.map((x) => x.title_ko));

console.log("ALL ASSERTIONS OK");
