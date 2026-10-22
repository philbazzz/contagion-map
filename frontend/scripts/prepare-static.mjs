/**
 * Assembles static JSON for GitHub Pages / vite preview (no running backend).
 *
 *   node scripts/prepare-static.mjs
 *
 * Writes:
 *   public/data/network.json   — validated network from backend/export_network.py
 *   public/data/market.json    — FRED-safe placeholder (Actions overwrites with live FRED)
 *   public/data/quotes.json    — ticker roster without redistributed vendor prices
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
const repo = resolve(root, "..");
const outDir = resolve(root, "public", "data");
mkdirSync(outDir, { recursive: true });

function resolvePython() {
  const win = process.platform === "win32";
  const candidates = [
    resolve(repo, "backend", ".venv", win ? "Scripts/python.exe" : "bin/python"),
    resolve(repo, ".venv", win ? "Scripts/python.exe" : "bin/python"),
    win ? "python" : "python3",
  ];
  for (const c of candidates) {
    if (c === "python" || c === "python3") return c;
    if (existsSync(c)) return c;
  }
  return win ? "python" : "python3";
}
const PY = resolvePython();
const env = { ...process.env, MARKET_SCHEDULER: "false", PYTHONIOENCODING: "utf-8" };
console.log("using python:", PY);

const networkPath = resolve(outDir, "network.json");
let network;
try {
  const networkRaw = execFileSync(PY, [resolve(repo, "backend", "export_network.py")], {
    env, maxBuffer: 64 << 20, encoding: "utf8",
  });
  network = JSON.parse(networkRaw);
  writeFileSync(networkPath, JSON.stringify(network, null, 0), "utf8");
} catch (e) {
  if (!existsSync(networkPath)) throw e;
  console.warn("export_network failed — keeping existing public/data/network.json:", e?.message || e);
  network = JSON.parse(readFileSync(networkPath, "utf8"));
}
console.log("network.json", network.nodes?.length, "nodes", network.edges?.length, "edges");

// Sector financing stress inputs (Shock tab contagion)
const sectorSrc = resolve(repo, "backend", "data", "sector_stress.json");
if (existsSync(sectorSrc)) {
  const sectorRaw = readFileSync(sectorSrc, "utf8");
  writeFileSync(resolve(outDir, "sector_stress.json"), sectorRaw, "utf8");
  writeFileSync(resolve(root, "src", "data", "sector_stress.json"), sectorRaw, "utf8");
}

/** Observed equity quotes via existing backend collectors (yfinance / FDR). Set FETCH_QUOTES=0 to skip. */
const quotesPath = resolve(outDir, "quotes.json");
const fetchQuotes = process.env.FETCH_QUOTES !== "0";
let quotesWritten = false;
if (fetchQuotes) {
  try {
    execFileSync(PY, [resolve(repo, "scripts", "fetch_quotes_snapshot.py"), "--out", quotesPath], {
      env, maxBuffer: 64 << 20, encoding: "utf8", stdio: ["ignore", "inherit", "inherit"],
    });
    quotesWritten = existsSync(quotesPath);
  } catch (e) {
    console.warn("fetch_quotes_snapshot failed — writing empty roster:", e?.message || e);
  }
}
if (!quotesWritten) {
  const quotes = {
    generated_at: new Date().toISOString(),
    demo: false,
    static: true,
    items: (network.nodes || []).map((n) => ({
      entity: n.id,
      listed: !!n.listed,
      ticker: n.ticker,
      exchange: n.exchange,
      listing_note: n.listing_note,
      provider: null,
      symbol: n.ticker,
      status: n.listed ? "unavailable" : "unlisted",
      status_ko: n.listed
        ? "시세 미수집 — npm run prepare:static (FETCH_QUOTES=1) 또는 start.bat"
        : "비상장",
      price: null,
      change_pct: null,
      change: null,
    })),
    fx: { source: "", rates: {} },
    providers: {},
    keys: {},
    note: "관측 시세가 아직 없습니다. 로컬에서 prepare:static이 yfinance/FDR로 quotes.json을 채웁니다. 숫자는 만들지 않습니다.",
  };
  writeFileSync(quotesPath, JSON.stringify(quotes, null, 0), "utf8");
}

// PF ecosystem quotes (separate network — do not reuse semiconductor entity IDs alone)
const pfQuotesPath = resolve(outDir, "pf", "quotes.json");
mkdirSync(resolve(outDir, "pf"), { recursive: true });
if (fetchQuotes) {
  try {
    execFileSync(PY, [resolve(repo, "scripts", "fetch_pf_quotes.py"), "--out", pfQuotesPath], {
      env, maxBuffer: 64 << 20, encoding: "utf8", stdio: ["ignore", "inherit", "inherit"],
    });
  } catch (e) {
    console.warn("fetch_pf_quotes failed:", e?.message || e);
  }
}
if (!existsSync(pfQuotesPath)) {
  const pfNetPath = resolve(outDir, "pf", "network.json");
  let pfNodes = [];
  if (existsSync(pfNetPath)) {
    try { pfNodes = JSON.parse(readFileSync(pfNetPath, "utf8")).nodes || []; } catch { /* empty */ }
  }
  writeFileSync(pfQuotesPath, JSON.stringify({
    generated_at: new Date().toISOString(),
    static: true,
    ecosystem: "datacenter_pf",
    items: pfNodes.map((n) => ({
      entity: n.id, listed: !!n.listed, ticker: n.ticker, exchange: n.exchange,
      provider: null, symbol: n.ticker,
      status: n.listed ? "unavailable" : "unlisted",
      status_ko: n.listed ? "시세 미수집 — python scripts/fetch_pf_quotes.py" : "비상장",
      price: null, change_pct: null, change: null,
    })),
    fx: { source: "", rates: {} }, providers: {}, keys: {},
    note: "PF 시세 미수집. 결측을 0으로 채우지 않습니다.",
  }, null, 0), "utf8");
}

const marketPath = resolve(outDir, "market.json");
const fredPath = resolve(repo, "backend", "data", "market_public_snapshot.json");
let market;
if (existsSync(fredPath)) {
  try { market = JSON.parse(readFileSync(fredPath, "utf8")); } catch { market = null; }
}
if (!market) {
  market = {
    snapshot_at: null,
    generated_at: new Date().toISOString(),
    auto_update: false,
    usage_note: "관측 시장 지표(국채)와 좌측 금리 충격 시나리오는 별개입니다. 주식 수치는 재배포 제한으로 공개 배포본에 넣지 않습니다.",
    indicators: [
      {
        id: "ust_10y", name: "미국 10년물 국채 금리", plain: "장기 시장금리 벤치마크 (FRED DGS10)",
        unit: "%", source: { name: "FRED (DGS10)", url: "https://fred.stlouisfed.org/series/DGS10" },
        status: "never", status_ko: "아직 수집 안 함 · GitHub Actions에서 FRED_API_KEY로 갱신",
        latest: null, caution: "관측값이며 시나리오 가정이 아닙니다.",
      },
      {
        id: "ust_2y", name: "미국 2년물 국채 금리", plain: "단기·중기 시장금리 벤치마크 (FRED DGS2)",
        unit: "%", source: { name: "FRED (DGS2)", url: "https://fred.stlouisfed.org/series/DGS2" },
        status: "never", status_ko: "아직 수집 안 함 · GitHub Actions에서 FRED_API_KEY로 갱신",
        latest: null, caution: "관측값이며 시나리오 가정이 아닙니다.",
      },
    ],
  };
}
writeFileSync(marketPath, JSON.stringify(market, null, 0), "utf8");
console.log("market.json · quotes.json ready →", outDir);
