/** Entry for the standalone single-file demo: same App, in-browser engine port, saved market snapshot. */
import { createRoot } from "react-dom/client";
import App from "./App";
import { makeLocalApi } from "./api/local";
import type { MarketOverview, Network } from "./types";

declare global {
  interface Window { __CONTAGION_NETWORK__: Network; __CONTAGION_MARKET__: MarketOverview | null }
}

createRoot(document.getElementById("root")!).render(
  <App api={makeLocalApi(window.__CONTAGION_NETWORK__, window.__CONTAGION_MARKET__ || null)} />,
);
