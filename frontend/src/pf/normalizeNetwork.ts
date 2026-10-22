/**
 * Ensure PF/semi network payloads satisfy the renderer/detail-panel data contract.
 * Incomplete DART-integrated nodes/edges often omit array fields — that caused
 * "Cannot read properties of undefined (reading 'length')" on PFV click.
 */
import type { NetEdge, NetNode, Network } from "../types";

function asStringArray(v: unknown): string[] {
  if (Array.isArray(v)) return v.filter((x) => typeof x === "string") as string[];
  if (typeof v === "string" && v.trim()) return [v];
  return [];
}

export function normalizeNode(n: NetNode): NetNode {
  return {
    ...n,
    roles: asStringArray((n as { roles?: unknown }).roles),
    key_drivers: asStringArray(n.key_drivers),
    source_ids: asStringArray(n.source_ids),
  };
}

export function normalizeEdge(e: NetEdge): NetEdge {
  return {
    ...e,
    roles: asStringArray(e.roles),
    source_ids: asStringArray(e.source_ids),
    contract_ids: asStringArray(e.contract_ids),
    commercial_ids: asStringArray((e as { commercial_ids?: unknown }).commercial_ids),
  };
}

export function normalizeNetwork(net: Network): Network {
  const nodes = (net.nodes || []).map(normalizeNode);
  const edges = (net.edges || []).map(normalizeEdge);
  const financials = net.financials || {
    as_of: net.meta?.as_of || "",
    instruments: [],
    totals: { principal_usd_m: 0, recourse_net_usd_m: 0, nonrecourse_net_usd_m: 0, source_ids: [] },
    maturity_buckets: [],
    metrics: [],
  };
  return {
    ...net,
    nodes,
    edges,
    contracts: Array.isArray(net.contracts) ? net.contracts : [],
    sources: Array.isArray(net.sources) ? net.sources : [],
    financials: {
      ...financials,
      instruments: Array.isArray(financials.instruments) ? financials.instruments : [],
    },
  };
}

/** Report incomplete records without mutating (for audits/tests). */
export function auditNetworkArrays(net: Network): {
  badNodes: { id: string; missing: string[] }[];
  badEdges: { id: string; missing: string[] }[];
} {
  const badNodes: { id: string; missing: string[] }[] = [];
  const badEdges: { id: string; missing: string[] }[] = [];
  for (const n of net.nodes || []) {
    const missing: string[] = [];
    if (!Array.isArray(n.key_drivers)) missing.push("key_drivers");
    if (!Array.isArray(n.source_ids)) missing.push("source_ids");
    if ((n as { roles?: unknown }).roles !== undefined && !Array.isArray((n as { roles?: unknown }).roles)) {
      missing.push("roles");
    }
    if (missing.length) badNodes.push({ id: n.id, missing });
  }
  for (const e of net.edges || []) {
    const missing: string[] = [];
    if (!Array.isArray(e.roles)) missing.push("roles");
    if (!Array.isArray(e.source_ids)) missing.push("source_ids");
    if (!Array.isArray(e.contract_ids)) missing.push("contract_ids");
    if (missing.length) badEdges.push({ id: e.id, missing });
  }
  return { badNodes, badEdges };
}
