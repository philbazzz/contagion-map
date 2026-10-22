"""Print the assembled network (entities + relationships + financials + sources) as JSON.

Used by frontend/scripts/build-demo.mjs and parity-check.mjs so the standalone demo and the
browser engine read exactly what the backend loader validated — one dataset, no copies.

    python backend/export_network.py > network.json
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MARKET_SCHEDULER", "false")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.service import load_network  # noqa: E402

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(load_network(), ensure_ascii=False))
