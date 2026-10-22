/**
 * Builds demo/contagion-demo.html — a single self-contained page that runs the
 * same React app with the in-browser engine port (src/api/local.ts).
 * React is loaded from cdnjs (pinned 18.3.1); everything else is inlined.
 *
 *   npm run build:demo
 */
import * as esbuild from "esbuild";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
const out = resolve(root, "..", "demo", "contagion-demo.html");

const shims = {
  name: "react-globals",
  setup(build) {
    const map = {
      react: "module.exports = window.React;",
      "react-dom/client": "module.exports = window.ReactDOM;",
      "react/jsx-runtime":
        "var R = window.React; function jsx(t, p, k) { return R.createElement(t, k === undefined ? p : Object.assign({}, p, { key: k })); }" +
        " module.exports = { jsx: jsx, jsxs: jsx, Fragment: R.Fragment };",
    };
    build.onResolve({ filter: /^(react|react-dom\/client|react\/jsx-runtime)$/ }, (a) => ({ path: a.path, namespace: "shim" }));
    build.onLoad({ filter: /.*/, namespace: "shim" }, (a) => ({ contents: map[a.path], loader: "js" }));
  },
};

const result = await esbuild.build({
  entryPoints: [resolve(root, "src/demo.tsx")],
  bundle: true,
  minify: true,
  format: "iife",
  target: "es2020",
  jsx: "automatic",
  write: false,
  plugins: [shims],
  logLevel: "warning",
});
const js = result.outputFiles[0].text.replace(/<\/script/gi, "<\\/script");
const css = readFileSync(resolve(root, "src/styles.css"), "utf8");
// The demo embeds exactly what the backend loader assembles and validates
// (entities + relationships + financials + sources) — one dataset, no hand-made copy.
const network = execFileSync(process.platform === "win32" ? "python" : "python3", [resolve(root, "..", "backend", "export_network.py")],
  { env: { ...process.env, MARKET_SCHEDULER: "false" }, maxBuffer: 64 << 20 }).toString("utf8");
const data = JSON.stringify(JSON.parse(network)).replace(/</g, "\\u003c");

// Market data: only the redistributable snapshot exported by the backend
// (python backend/export_public_snapshot.py). HY OAS values are never embedded.
const snapPath = resolve(root, "..", "backend", "data", "market_public_snapshot.json");
let market;
try {
  market = JSON.parse(readFileSync(snapPath, "utf8"));
} catch {
  market = {
    snapshot_at: null, auto_update: false,
    usage_note: "시장 관측값은 시나리오 작성의 참고 정보입니다. 시뮬레이션 가정에 자동으로 대입하지 않습니다.",
    indicators: [
      { id: "hy_oas", name: "미국 하이일드 채권 가산금리 (HY OAS)", plain: "위험도가 높은 기업들이 국채보다 더 부담하는 추가 금리", unit: "bp",
        source: { name: "FRED (ICE BofA US High Yield Index OAS)", url: "https://fred.stlouisfed.org/series/BAMLH0A0HYM2" },
        status: "not_redistributable", status_ko: "공개 배포본에서는 표시하지 않음 (ICE 재배포 제한)", latest: null,
        caution: "로컬 앱(백엔드 실행 시)에서만 표시됩니다.", license: "ICE Data Indices 자료 · 제3자 공개 배포는 ICE 사전 승인 필요" },
      { id: "gpu_rent", name: "H100 GPU 임대 매물가", plain: "온라인 GPU 임대 플랫폼에 올라온 H100 매물의 1장·1시간 가격", unit: "USD / GPU·시간",
        source: { name: "Vast.ai 매물 조회 API", url: "https://docs.vast.ai/api-reference/search/search-offers" },
        status: "no_snapshot", status_ko: "저장된 스냅샷 없음 · 자동 갱신 안 됨", latest: null,
        caution: "로컬 백엔드에서 수집한 스냅샷을 내보낸 뒤 데모를 다시 빌드하면 표시됩니다." },
    ],
  };
}
const marketJson = JSON.stringify(market).replace(/</g, "\\u003c");

const html = `<title>CONTAGION Risk Universe</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
${css}
</style>
<div id="root"><div class="boot"><div class="wordmark">CONTAGION</div><p class="muted">Financial Risk Universe · 로딩 중…</p></div></div>
<script>window.__CONTAGION_NETWORK__ = ${data}; window.__CONTAGION_MARKET__ = ${marketJson};</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.3.1/umd/react.production.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.3.1/umd/react-dom.production.min.js"></script>
<script>
${js}
</script>
`;
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, html);
console.log(`demo written: ${out} (${(html.length / 1024).toFixed(0)} KB)`);
