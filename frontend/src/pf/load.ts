import type { MarketOverview, Network, QuotesOverview } from "../types";
import type { PfBundle, PfProjectsFile } from "./types";
import { normalizeNetwork } from "./normalizeNetwork";

function dataRoot(): string {
  const base = (import.meta.env.BASE_URL as string) || "./";
  return (base.endsWith("/") ? base : `${base}/`) + "data/pf";
}

async function loadJson<T>(name: string): Promise<T> {
  const url = `${dataRoot()}/${name}?t=${Date.now()}`;
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`PF ${name} → HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

/** Roster-only quotes when snapshot missing — never fabricate prices. */
function emptyPfQuotes(net: Network): QuotesOverview {
  return {
    static: true,
    ecosystem: "datacenter_pf",
    items: net.nodes.map((n) => ({
      entity: n.id,
      listed: !!n.listed,
      ticker: n.ticker,
      exchange: n.exchange,
      listing_note: n.listing_note,
      provider: null,
      symbol: n.ticker,
      status: n.listed ? "unavailable" : "unlisted",
      status_ko: n.listed
        ? "시세 미수집 — start.bat(백엔드) 또는 python scripts/fetch_pf_quotes.py"
        : "비상장",
      price: null,
      change_pct: null,
      change: null,
    })),
    fx: { source: "", rates: {} },
    providers: {},
    keys: {},
    note: "PF 시세 스냅샷이 없습니다. 결측을 0으로 채우지 않습니다.",
  };
}

export async function loadPfBundle(): Promise<PfBundle> {
  const [rawNetwork, projects, market, quotes] = await Promise.all([
    loadJson<Network>("network.json"),
    loadJson<PfProjectsFile>("projects.json"),
    loadJson<MarketOverview>("market.json").catch(() => null),
    loadJson<QuotesOverview>("quotes.json").catch(() => null),
  ]);
  // DART-integrated records often omit roles/key_drivers/source_ids —
  // DetailPanel/hover read `.length` and crashed the map on PFV click.
  const network = normalizeNetwork(rawNetwork);

  const byId = new Map((quotes?.items || []).map((q) => [q.entity, q]));
  const items = network.nodes.map((n) => {
    const q = byId.get(n.id);
    if (q) {
      if (!n.listed) {
        return {
          ...q,
          listed: false,
          price: null,
          change: null,
          change_pct: null,
          status: "unlisted",
          status_ko: "비상장",
        };
      }
      if (q.price === 0 && q.status !== "ok") {
        return { ...q, price: null, change: null, change_pct: null };
      }
      return q;
    }
    return {
      entity: n.id,
      listed: !!n.listed,
      ticker: n.ticker,
      exchange: n.exchange,
      listing_note: n.listing_note,
      provider: null,
      symbol: n.ticker,
      status: n.listed ? "unavailable" : "unlisted",
      status_ko: n.listed ? "시세 미수집" : "비상장",
      price: null,
      change_pct: null,
      change: null,
    };
  });
  const merged: QuotesOverview = quotes
    ? { ...quotes, items, ecosystem: "datacenter_pf" }
    : emptyPfQuotes(network);
  return { network, projects, market, quotes: merged };
}
