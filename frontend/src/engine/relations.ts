/** Port of backend/app/engine/relations.py — keep the two in step (npm run parity). */
import type { NetEdge, Network, PathResult, RelationSummary, NetworkStats } from "../types";

const PATH_STATUSES = new Set(["VERIFIED", "INFERRED"]);
const FINANCING_KINDS = new Set(["term_loan", "revolver", "senior_notes", "convertible", "other_loan"]);
const INDUSTRIAL_CHANNELS = new Set(["supply_chain", "customer", "facility", "contract"]);

type Step = { edge: NetEdge; to: string };

/** same order as backend/app/engine/relations.py CHANNEL_RANK */
const CHANNEL_RANK: Record<string, number> = { supply_chain: 0, financial: 1, equity: 2, customer: 3, facility: 4, contract: 5 };

export function adjacency(net: Network): Map<string, Step[]> {
  const adj = new Map<string, Step[]>();
  const push = (k: string, s: Step) => { if (!adj.has(k)) adj.set(k, []); adj.get(k)!.push(s); };
  for (const e of net.edges) {
    if (!PATH_STATUSES.has(e.source_status)) continue;
    push(e.source, { edge: e, to: e.target });
    push(e.target, { edge: e, to: e.source });
  }
  for (const list of adj.values()) {
    list.sort((a, b) => {
      const va = a.edge.source_status !== "VERIFIED" ? 1 : 0, vb = b.edge.source_status !== "VERIFIED" ? 1 : 0;
      if (va !== vb) return va - vb;
      const ca = CHANNEL_RANK[a.edge.impact_channel] ?? 9, cb = CHANNEL_RANK[b.edge.impact_channel] ?? 9;
      if (ca !== cb) return ca - cb;
      return a.edge.id < b.edge.id ? -1 : a.edge.id > b.edge.id ? 1 : 0;
    });
  }
  return adj;
}

export function shortestPath(net: Network, a: string, b: string): PathResult | null {
  const ids = new Set(net.nodes.map((n) => n.id));
  if (!ids.has(a) || !ids.has(b)) return null;
  if (a === b) return { nodes: [a], edges: [], hops: 0, statuses: [] };
  const adj = adjacency(net);
  const prev = new Map<string, [string | null, NetEdge | null]>([[a, [null, null]]]);
  const q: string[] = [a];
  let found = false;
  while (q.length && !found) {
    const cur = q.shift()!;
    for (const st of adj.get(cur) || []) {
      if (prev.has(st.to)) continue;
      prev.set(st.to, [cur, st.edge]);
      if (st.to === b) { found = true; break; }
      q.push(st.to);
    }
  }
  if (!prev.has(b)) return null;
  const nodes = [b];
  const edges: NetEdge[] = [];
  let cur = b;
  while (prev.get(cur)![0] !== null) {
    const [p, e] = prev.get(cur)!;
    edges.push(e!);
    nodes.push(p!);
    cur = p!;
  }
  nodes.reverse();
  edges.reverse();
  return { nodes, edges: edges.map((e) => e.id), hops: edges.length, statuses: edges.map((e) => e.source_status) };
}

export function hopDistances(net: Network, origin: string): Map<string, number> {
  const adj = adjacency(net);
  const dist = new Map<string, number>([[origin, 0]]);
  const q = [origin];
  while (q.length) {
    const cur = q.shift()!;
    for (const st of adj.get(cur) || []) {
      if (!dist.has(st.to)) { dist.set(st.to, dist.get(cur)! + 1); q.push(st.to); }
    }
  }
  return dist;
}

export function networkStats(net: Network, origin: string): NetworkStats {
  const dist = hopDistances(net, origin);
  const others = net.nodes.map((n) => n.id).filter((i) => i !== origin);
  const insts = net.financials?.instruments || [];
  return {
    origin,
    entities: net.nodes.length,
    direct: others.filter((i) => dist.get(i) === 1).length,
    indirect: others.filter((i) => (dist.get(i) ?? 0) >= 2).length,
    unconnected: others.filter((i) => !dist.has(i)).length,
    financing_contracts: insts.filter((x) => FINANCING_KINDS.has(x.kind)).length,
    industrial_relationships: net.edges.filter((e) => INDUSTRIAL_CHANNELS.has(e.impact_channel)).length,
    financial_relationships: net.edges.filter((e) => e.impact_channel === "financial" || e.impact_channel === "equity").length,
    note: "공개자료로 확인된 기업·기관만 집계한 값이며, CoreWeave 생태계 전체 규모가 아닙니다.",
  };
}

export function relationshipSummary(net: Network, origin: string, entityId: string): RelationSummary {
  const path = shortestPath(net, origin, entityId);
  const direct = net.edges.filter((e) => {
    const s = new Set([e.source, e.target]);
    return s.size === new Set([origin, entityId]).size && s.has(origin) && s.has(entityId);
  });
  let kind: RelationSummary["kind"];
  if (entityId === origin) kind = "origin";
  else if (path === null) kind = "unconfirmed";
  else if (path.hops === 1) kind = "direct";
  else kind = "indirect";
  return { kind, path, direct_edges: direct.map((e) => e.id) };
}
