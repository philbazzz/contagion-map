"""Fallback API server using only the Python standard library (+ pydantic).

Use this ONLY if FastAPI cannot be installed. It serves the same endpoints
through the same service layer, so results are identical to app/main.py.

    python serve_simple.py            -> http://127.0.0.1:8000
"""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pydantic import ValidationError  # noqa: E402

from app import service  # noqa: E402
from app.engine.refinancing import RefiError  # noqa: E402
from app.models import RefinancingRequest  # noqa: E402
from urllib.parse import parse_qs, urlparse  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):  # noqa: N802
        self._send(204, {})

    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        p = u.path.rstrip("/")
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if p == "/api/market":
            return self._send(200, service.market().overview())
        if p == "/api/market/public-snapshot":
            return self._send(200, service.market().public_snapshot())
        if p == "/api/runs":
            return self._send(200, service.list_runs(int(q.get("limit", 20))))
        if p == "/api/quotes":
            return self._send(200, service.market().quotes())
        if p.startswith("/api/quotes/") and p.endswith("/history"):
            period = q.get("period", "1M")
            if period not in ("1D", "1M", "3M", "6M", "1Y"):
                return self._send(400, {"detail": "period must be 1D, 1M, 3M, 6M or 1Y"})
            data = service.market().quote_history(p.split("/")[3], period)
            return self._send(200, data) if data else self._send(404, {"detail": "unknown entity"})
        if p == "/api/stats":
            data = service.get_stats(q.get("origin", "coreweave"))
            return self._send(200, data) if data else self._send(404, {"detail": "unknown entity"})
        if p == "/api/paths":
            data = service.get_path(q.get("a", ""), q.get("b", ""))
            return self._send(200, data) if data else self._send(404, {"detail": "unknown entity"})
        if p == "/api/health":
            return self._send(200, service.health())
        if p == "/api/network":
            return self._send(200, service.get_network())
        if p == "/api/sources":
            return self._send(200, service.get_sources())
        if p.startswith("/api/entities/"):
            data = service.get_entity(p.rsplit("/", 1)[1], origin=q.get("origin", "coreweave"))
            return self._send(200, data) if data else self._send(404, {"detail": "unknown entity"})
        self._send(404, {"detail": "not found"})

    def do_POST(self):  # noqa: N802
        u = urlparse(self.path)
        p = u.path.rstrip("/")
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            if p == "/api/simulate/refinancing":
                return self._send(200, service.run_refinancing(RefinancingRequest(**body)))
            if p == "/api/quotes/refresh":
                return self._send(200, service.market().refresh_quotes())
            if p == "/api/market/refresh":
                return self._send(200, service.market().manual_refresh(q.get("source")))
            if p == "/api/runs":
                return self._send(200, service.save_run(body))
        except ValidationError as exc:
            return self._send(422, {"detail": json.loads(exc.json())})
        except RefiError as exc:
            return self._send(422, {"detail": str(exc)})
        except KeyError as exc:
            return self._send(404, {"detail": str(exc)})
        except ValueError as exc:
            return self._send(422, {"detail": str(exc)})
        self._send(404, {"detail": "not found"})

    def log_message(self, fmt, *args):
        sys.stderr.write("[api] " + (fmt % args) + "\n")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"CONTAGION fallback API on http://127.0.0.1:{port}")
    m = service.market()
    if m.settings.scheduler_enabled:
        m.start_thread()  # same due-check logic as the FastAPI scheduler
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
