/**
 * Cross-platform-ish launcher: backend :8000 + frontend :5173 (http API mode).
 * On Windows prefer start.bat (handles PATH / health wait / cleanup).
 *
 *   npm start
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const win = process.platform === "win32";
const py = resolve(root, "backend", ".venv", win ? "Scripts/python.exe" : "bin/python");

if (!existsSync(py)) {
  console.error("[CONTAGION] backend/.venv missing. Run start_backend.bat (Windows) once, then npm start.");
  process.exit(1);
}

const children = [];
function killAll() {
  for (const c of children) {
    try {
      if (win) spawn("taskkill", ["/PID", String(c.pid), "/T", "/F"]);
      else c.kill("SIGTERM");
    } catch { /* ignore */ }
  }
}
process.on("SIGINT", () => { killAll(); process.exit(0); });
process.on("SIGTERM", () => { killAll(); process.exit(0); });

console.log("[CONTAGION] Backend http://127.0.0.1:8000");
const backend = spawn(py, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"], {
  cwd: resolve(root, "backend"),
  stdio: "inherit",
  env: process.env,
});
children.push(backend);

async function waitHealth(ms = 45000) {
  const start = Date.now();
  while (Date.now() - start < ms) {
    try {
      const r = await fetch("http://127.0.0.1:8000/api/health");
      if (r.ok) return true;
    } catch { /* retry */ }
    await new Promise((r) => setTimeout(r, 800));
  }
  return false;
}

const ok = await waitHealth();
if (!ok) console.warn("[CONTAGION] Backend health timeout — starting frontend anyway.");

console.log("[CONTAGION] Frontend http://127.0.0.1:5173  (VITE_API_MODE=http)");
const front = spawn(win ? "npm.cmd" : "npm", ["run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"], {
  cwd: resolve(root, "frontend"),
  stdio: "inherit",
  env: { ...process.env, VITE_API_MODE: "http", VITE_BASE: "./" },
  shell: win,
});
children.push(front);

front.on("exit", (code) => {
  killAll();
  process.exit(code ?? 0);
});
backend.on("exit", (code) => {
  if (code && code !== 0) console.error("[CONTAGION] Backend exited", code);
});
