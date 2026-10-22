/**
 * Static (GitHub Pages) API — no Python server.
 * Calculations run in the browser via the TypeScript ports of the Python engines.
 * Market macros load from public/data/market.json (FRED snapshot via Actions).
 * Equity prices are not redistributed; TradingView widgets remain in the detail panel.
 */
import type { Api, MarketOverview, Network, QuotesOverview, RunRecord } from "../types";
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

export async function createStaticApi(): Promise<Api> {
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
    entity: async (id, origin) => entityLocal(net, id, origin),
    market: async () => cachedMarket,
    refreshMarket: async () => {
      try { cachedMarket = await loadJson<MarketOverview>("market.json"); } catch { /* keep last */ }
      return cachedMarket;
    },
    quotes: async () => cachedQuotes,
    refreshQuotes: async (opts) => {
      const name = opts?.ecosystem === "datacenter_pf" ? "pf/quotes.json" : "quotes.json";
      const prev = cachedQuotes;
      try {
        const next = await loadJson<QuotesOverview>(name);
        cachedQuotes = {
          ...next,
          retrieved_at: new Date().toISOString(),
          refresh_status: next.static ? "stale_retained" : "ok",
          refresh_detail: next.static
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
    quoteHistory: async (id, period) => ({
      entity: id, period, points: [], status: "not_redistributable",
      note: "공개 배포본에는 주가 이력을 재배포하지 않습니다. 상세 패널의 TradingView를 사용하세요.",
    }),
    saveRun: base.saveRun,
    listRuns: base.listRuns,
  };
}

/** For typed Runs — localStorage is already handled inside makeLocalApi. */
export type { RunRecord };
