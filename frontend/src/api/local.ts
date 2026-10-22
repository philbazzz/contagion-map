/**
 * In-browser API for the standalone single-file demo (no server). It runs the TypeScript ports
 * of the backend engines (src/engine/*.ts); scripts/parity-check.mjs verifies they match Python.
 */
import type { Api, EntityDetail, MarketOverview, Network, QuotesOverview, RunRecord } from "../types";
import { simulateRefinancing, nextMaturityId } from "../engine/refinancing";
import { simulateRateShock } from "../engine/rateShock";
import { networkStats, relationshipSummary, shortestPath } from "../engine/relations";

export function entityLocal(net: Network, id: string, origin = "coreweave"): EntityDetail {
  const nodes = new Map(net.nodes.map((n) => [n.id, n]));
  const node = nodes.get(id);
  if (!node || !nodes.has(origin)) throw new Error(`unknown entity: ${id}`);
  const links = net.edges.filter((e) => e.source === id || e.target === id)
    .map((e) => ({ ...e, counterpart: nodes.get(e.source === id ? e.target : e.source)!.name }));
  const contracts = net.financials.instruments.filter((x) => id === "coreweave" || x.participants.some((p) => p.entity === id)).map((x) => x.id);
  return { entity: node, links, contracts, relation: relationshipSummary(net, origin, id) };
}

/**
 * The public demo carries NO share prices: Finnhub's terms and the KRX data licence (공공누리 제4유형) do not
 * allow redistribution. Every listed entity is reported with that status; no number is ever made up.
 */
export function demoQuotes(net: Network): QuotesOverview {
  return {
    demo: true,
    items: net.nodes.map((n) => ({
      entity: n.id, listed: n.listed, ticker: n.ticker, exchange: n.exchange, listing_note: n.listing_note, provider: null, symbol: n.ticker,
      status: n.listed ? "not_redistributable" : "unlisted",
      status_ko: n.listed ? "공개 데모에는 시세 미포함 (제공처 약관 · KRX 재배포 금지)" : "비상장",
    })),
    fx: { source: "한국수출입은행 매매기준율", rates: {} },
    providers: {}, keys: {},
    note: "공개 데모에는 시세와 환율을 넣지 않습니다. 로컬 앱에서 API 키를 설정하면 표시됩니다.",
  };
}

export function makeLocalApi(net: Network, market: MarketOverview | null): Api {
  if (net.meta.next_maturity_id === undefined) net.meta.next_maturity_id = nextMaturityId(net);
  const statusCounts = () => {
    const c: Record<string, number> = { VERIFIED: 0, INFERRED: 0, ASSUMED: 0, UNKNOWN: 0 };
    for (const x of [...net.nodes, ...net.edges]) c[x.source_status] = (c[x.source_status] || 0) + 1;
    return c;
  };
  const KEY = "contagion.runs.v2";
  let mem: RunRecord[] = [];
  try { mem = JSON.parse(localStorage.getItem(KEY) || "[]"); } catch { mem = []; }
  return {
    kind: "local",
    health: async () => ({ status: "ok", nodes: net.nodes.length, edges: net.edges.length, as_of: net.meta.as_of }),
    network: async () => net,
    stats: async (origin) => networkStats(net, origin),
    path: async (a, b) => ({ from: a, to: b, path: shortestPath(net, a, b) }),
    entity: async (id, origin) => entityLocal(net, id, origin),
    simulateRefinancing: async (p) => simulateRefinancing(net, p),
    simulateRateShock: async (p) => simulateRateShock(net, p),
    sources: async () => ({ sources: net.sources, status_counts: statusCounts(), meta: net.meta }),
    market: async () => market,
    refreshMarket: async () => market,
    quotes: async () => demoQuotes(net),
    quoteHistory: async (id, period) => ({ entity: id, period, points: [], status: "not_redistributable", note: "공개 데모에는 시세 이력을 넣지 않습니다." }),
    refreshQuotes: async () => demoQuotes(net),
    saveRun: async (r) => {
      const rec = { ...r, id: Math.random().toString(36).slice(2, 10), created_at: new Date().toISOString() };
      mem = [rec, ...mem].slice(0, 30);
      try { localStorage.setItem(KEY, JSON.stringify(mem)); } catch { /* storage unavailable: keep in memory */ }
      return rec;
    },
    listRuns: async () => mem,
  };
}
