import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { httpApi } from "./api/http";
import { createStaticApi } from "./api/static";
import type { Api } from "./types";
import "./styles.css";

/**
 * Default: static mode (GitHub Pages / vite preview) — no Python server.
 * Local backend: set VITE_API_MODE=http when starting Vite (see start_frontend.bat).
 */
async function boot(): Promise<Api> {
  const mode = (import.meta as unknown as { env?: Record<string, string> }).env?.VITE_API_MODE || "static";
  if (mode === "http") {
    try {
      await httpApi.health();
      return httpApi;
    } catch {
      console.warn("Backend unreachable — falling back to static data API");
    }
  }
  return createStaticApi();
}

const root = createRoot(document.getElementById("root")!);
root.render(
  <StrictMode>
    <div className="boot"><div className="wordmark">CONTAGION</div><p className="muted">불러오는 중…</p></div>
  </StrictMode>,
);

boot()
  .then((api) => {
    root.render(
      <StrictMode>
        <App api={api} />
      </StrictMode>,
    );
  })
  .catch((e) => {
    root.render(
      <StrictMode>
        <div className="boot boot-error">
          <div className="wordmark">CONTAGION</div>
          <p>정적 데이터를 불러오지 못했습니다: {String((e as Error)?.message || e)}</p>
          <p className="muted">배포 전 <code>npm run prepare:static</code>으로 data JSON을 생성했는지 확인하세요.</p>
        </div>
      </StrictMode>,
    );
  });
