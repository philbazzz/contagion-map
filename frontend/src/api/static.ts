/**
 * Static (GitHub Pages) API — no Python server.
 * Calculations run in the browser via the TypeScript ports of the Python engines.
 * Market macros load from public/data/market.json (FRED snapshot via Actions).
 * Equity prices are not redistributed; TradingView widgets remain in the detail panel.
 */
import type { Api, MarketOverview, Network, QuoteHistory, QuotesOverview, RunRecord } from "../types";
import { entityLocal, makeLocalApi } from "./local";

function dataRoot(): string {
  const base = (import.meta.env.BASE_URL as string) || "./";
  return (base.endsWith("/") ? base : `${base}/`) + "data";
}

async function loadJson<T>(name: string): Promise<T> {
  const url = `${dataRoot()}/${name}?t=${Date.now()}`;
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`${name} → HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

/**
 * Optional live quote server (Render). Build with VITE_LIVE_API=https://xxx.onrender.com
 * Only Market quotes / macro refresh go there; everything else stays in the browser,
 * and any failure falls back to the bundled JSON snapshot.
 */
let LIVE = ((import.meta.env.VITE_LIVE_API as string) || "").replace(/\/+$/, "");
const COLD_START_MS = 90_000; // free-tier server may need ~30–60s to wake up

async function liveFetch<T>(path: string, method: "GET" | "POST" = "GET"): Promise<T> {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), COLD_START_MS);
  try {
    const r = await fetch(LIVE + path, {
      method, signal: ctl.signal, cache: "no-store",
      headers: method === "POST" ? { "Content-Type": "application/json" } : undefined,
      body: method === "POST" ? "{}" : undefined,
    });
    if (!r.ok) throw new Error(`${path} → HTTP ${r.status}`);
    return (await r.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export async function createStaticApi(): Promise<Api> {
  // Server address can be changed without rebuilding: data/live.json → {"api": "https://xxx.onrender.com"}
  if (!LIVE) {
    try {
      const cfg = await loadJson<{ api?: string }>("live.json");
      if (cfg?.api && /^https:\/\//.test(cfg.api)) LIVE = cfg.api.replace(/\/+$/, "");
    } catch { /* no live server configured — snapshot mode */ }
  }
  // Wake the free-tier server in the background so the first 조회 is fast.
  if (LIVE) liveFetch("/api/health").catch(() => undefined);

  const [net, market, quotes] = await Promise.all([
    loadJson<Network>("network.json"),
    loadJson<MarketOverview>("market.json").catch(() => null),
    loadJson<QuotesOverview>("quotes.json").catch(() => null),
  ]);
  const base = makeLocalApi(net, market);
  const emptyQuotes = (): QuotesOverview => ({
    static: true,
    items: net.nodes.map((n) => ({
      entity: n.id, listed: n.listed, ticker: n.ticker, exchange: n.exchange, listing_note: n.listing_note,
      provider: null, symbol: n.ticker,
      status: n.listed ? "unavailable" : "unlisted",
      status_ko: n.listed ? "시세 미수집 — prepare:static 또는 백엔드 새로고침" : "비상장",
    })),
    fx: { source: "", rates: {} }, providers: {}, keys: {},
    note: "관측 시세 JSON이 비어 있습니다. npm run prepare:static 으로 yfinance/FDR 스냅샷을 생성하세요.",
  });

  let cachedQuotes = quotes || emptyQuotes();
  let cachedMarket = market;

  return {
    ...base,
    kind: "static",
    live: !!LIVE,
    entity: async (id, origin) => entityLocal(net, id, origin),
    market: async () => cachedMarket,
    refreshMarket: async () => {
      if (LIVE) {
        try {
          const body = await liveFetch<{ overview: MarketOverview }>("/api/market/refresh", "POST");
          if (body?.overview) { cachedMarket = body.overview; return cachedMarket; }
        } catch { /* fall back to snapshot */ }
      }
      try { cachedMarket = await loadJson<MarketOverview>("market.json"); } catch { /* keep last */ }
      return cachedMarket;
    },
    quotes: async () => cachedQuotes,
    refreshQuotes: async (opts) => {
      const pf = opts?.ecosystem === "datacenter_pf";
      const name = pf ? "pf/quotes.json" : "quotes.json";
      const prev = cachedQuotes;
      if (LIVE) {
        try {
          const body = await liveFetch<{ quotes: QuotesOverview }>(
            `/api/quotes/refresh${pf ? "?ecosystem=datacenter_pf" : ""}`, "POST");
          if (body?.quotes) {
            cachedQuotes = { ...body.quotes, retrieved_at: body.quotes.retrieved_at || new Date().toISOString() };
            return cachedQuotes;
          }
        } catch { /* server asleep/unreachable — fall back to bundled snapshot below */ }
      }
      try {
        const next = await loadJson<QuotesOverview>(name);
        cachedQuotes = {
          ...next,
          retrieved_at: new Date().toISOString(),
          refresh_status: LIVE ? "stale_retained" : (next.static ? "stale_retained" : "ok"),
          refresh_detail: LIVE
            ? "시세 서버에 연결하지 못해 저장된 시세를 표시합니다. 잠시 후 다시 조회해 주세요."
            : next.static
              ? "정적 배포본 — 서버 재수집 없이 quotes.json을 다시 읽었습니다. 실시간 갱신은 start.bat(백엔드)를 사용하세요."
              : "정적 파일을 다시 불러왔습니다.",
        };
      } catch {
        cachedQuotes = {
          ...prev,
          retrieved_at: new Date().toISOString(),
          refresh_status: "stale_retained",
          refresh_detail: "조회 실패 — 이전에 불러온 시세를 유지합니다.",
        };
      }
      return cachedQuotes;
    },
    quoteHistory: async (id, period) => {
      if (LIVE) {
        try {
          return await liveFetch<QuoteHistory>(`/api/quotes/${encodeURIComponent(id)}/history?period=${encodeURIComponent(period)}`);
        } catch { /* fall through */ }
      }
      return {
      entity: id, period, points: [], status: "not_redistributable",
      note: "공개 배포본에는 주가 이력을 재배포하지 않습니다. 상세 패널의 TradingView를 사용하세요.",
      };
    },
    saveRun: base.saveRun,
    listRuns: base.listRuns,
  };
}

/** For typed Runs — localStorage is already handled inside makeLocalApi. */
export type { RunRecord };
