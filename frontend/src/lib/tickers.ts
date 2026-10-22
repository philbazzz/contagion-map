/**
 * TradingView Single Ticker symbols for Contagion Map entities.
 * Format: {EXCHANGE}:{TICKER} — verified against TradingView symbol pages.
 *
 * Free widget embeds do NOT redistribute all markets (e.g. KRX, TSE return
 * "이 심볼은 트레이딩뷰에서만 볼 수 있습니다"). Those fall back to the project's
 * existing quote APIs (Finnhub / data.go.kr) when keys are configured.
 */

import type { NetNode } from "../types";

/** Project exchange label → TradingView exchange prefix */
const EXCHANGE_TV: Record<string, string> = {
  Nasdaq: "NASDAQ",
  NYSE: "NYSE",
  KOSPI: "KRX",
  KOSDAQ: "KRX",
  TSE: "TSE",
  BME: "BME",
  "Euronext Paris": "EURONEXT",
  XETRA: "XETR",
  LSE: "LSE",
};

/**
 * Free TradingView Single Ticker embeds verified in-browser (2026-10).
 * KRX / TSE fail with licensing restriction on the free widget.
 */
const TV_EMBED_OK = new Set(["NASDAQ", "NYSE", "EURONEXT", "XETR", "BME", "LSE"]);

/**
 * Explicit entity → TradingView symbol overrides.
 * Prefer this table for verification; fall back to exchange+ticker when absent.
 */
const ENTITY_TV: Record<string, string> = {
  coreweave: "NASDAQ:CRWV",
  nvidia: "NASDAQ:NVDA",
  sk_hynix: "KRX:000660",
  tsmc: "NYSE:TSM",
  dell: "NYSE:DELL",
  microsoft: "NASDAQ:MSFT",
  alphabet: "NASDAQ:GOOGL",
  amazon: "NASDAQ:AMZN",
  oracle: "NYSE:ORCL",
  amd: "NASDAQ:AMD",
  samsung: "KRX:005930",
  qualcomm: "NASDAQ:QCOM",
  tesla: "NASDAQ:TSLA",
  jusung_eng: "KRX:036930",
  hanmi_semi: "KRX:042700",
  isu_petasys: "KRX:007660",
  ls_electric: "KRX:010120",
  hd_hyundai_electric: "KRX:267260",
  hyosung_heavy: "KRX:298040",
  doosan_enerbility: "KRX:034020",
  sk_telecom: "KRX:017670",
  naver: "KRX:035420",
  samsung_sds: "KRX:018260",
  kt: "KRX:030200",
  lg_electronics: "KRX:066570",
  arista: "NYSE:ANET",
  vertiv: "NYSE:VRT",
  equinix: "NASDAQ:EQIX",
  meta: "NASDAQ:META",
  core_scientific: "NASDAQ:CORZ",
  applied_digital: "NASDAQ:APLD",
  galaxy_digital: "NASDAQ:GLXY",
  cipher_digital: "NASDAQ:CIFR",
  whitefiber: "NASDAQ:WYFI",
  terawulf: "NASDAQ:WULF",
  iren: "NASDAQ:IREN",
  nebius: "NASDAQ:NBIS",
  soluna: "NASDAQ:SLNH",
  hut8: "NASDAQ:HUT",
  macquarie: "ASX:MQG",
  blackstone: "NYSE:BX",
  morgan_stanley: "NYSE:MS",
  mufg: "TSE:8306",
  jpmorgan: "NYSE:JPM",
  goldman: "NYSE:GS",
  wells_fargo: "NYSE:WFC",
  bbva: "BME:BBVA",
  credit_agricole: "EURONEXT:ACA",
  smbc: "TSE:8316",
  pnc: "NYSE:PNC",
  societe_generale: "EURONEXT:GLE",
  citi: "NYSE:C",
  deutsche_bank: "XETR:DBK",
  us_bank: "NYSE:USB",
  blackrock: "NYSE:BLK",
  pimco: "XETR:ALV", // listing_note: Allianz SE (parent)
  carlyle: "NASDAQ:CG",
  great_elm: "NASDAQ:GECC",
  barclays: "LSE:BARC",
  jefferies: "NYSE:JEF",
  mizuho: "TSE:8411",
};

export type TvQuote = {
  symbol: string;
  currency: string | null;
  exchangeLabel: string;
  /** False when TradingView free widgets refuse to embed this market */
  embeddable: boolean;
};

/** Resolve TradingView symbol for a network node. Null if unlisted or unmappable. */
export function tradingViewQuote(n: NetNode): TvQuote | null {
  if (!n.listed || !n.ticker) return null;
  const symbol = ENTITY_TV[n.id] || fromExchangeTicker(n.exchange, n.ticker);
  if (!symbol) return null;
  const prefix = symbol.split(":")[0];
  return {
    symbol,
    currency: n.quote_currency,
    exchangeLabel: n.exchange || prefix,
    embeddable: TV_EMBED_OK.has(prefix),
  };
}

function fromExchangeTicker(exchange: string | null, ticker: string): string | null {
  if (!exchange) return null;
  const tv = EXCHANGE_TV[exchange];
  if (!tv) return null;
  return `${tv}:${ticker}`;
}
