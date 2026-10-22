import type { Api, MarketOverview, QuotesOverview } from "../types";

/** Talks to the FastAPI backend. In dev, Vite proxies /api to http://127.0.0.1:8000. */
const BASE = (import.meta as unknown as { env?: Record<string, string> }).env?.VITE_API_BASE || "";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`${path} → HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(BASE + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) {
    // surface the engine's Korean validation message (422) instead of a bare status code
    let detail = "";
    try { const j = await r.json(); detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch { /* not json */ }
    throw new Error(detail || `${path} → HTTP ${r.status}`);
  }
  return r.json() as Promise<T>;
}

const q = encodeURIComponent;

export const httpApi: Api = {
  kind: "http",
  health: () => get("/api/health"),
  network: () => get("/api/network"),
  stats: (origin) => get(`/api/stats?origin=${q(origin)}`),
  path: (a, b) => get(`/api/paths?a=${q(a)}&b=${q(b)}`),
  entity: (id, origin) => get(`/api/entities/${q(id)}?origin=${q(origin)}`),
  simulateRefinancing: (p) => post("/api/simulate/refinancing", p),
  simulateRateShock: (p) => post("/api/simulate/rate-shock", p),
  sources: () => get("/api/sources"),
  market: () => get("/api/market"),
  refreshMarket: async () => (await post<{ overview: MarketOverview }>("/api/market/refresh", {})).overview,
  quotes: () => get("/api/quotes"),
  quoteHistory: (id, period) => get(`/api/quotes/${q(id)}/history?period=${q(period)}`),
  refreshQuotes: async (opts) => {
    const eco = opts?.ecosystem === "datacenter_pf" ? "?ecosystem=datacenter_pf" : "";
    const body = await post<{ quotes: QuotesOverview; results?: Record<string, unknown> }>(`/api/quotes/refresh${eco}`, {});
    return body.quotes;
  },
  saveRun: (r) => post("/api/runs", r),
  listRuns: () => get("/api/runs"),
};
