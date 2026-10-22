"""Fetch observed US/KR daily closes into frontend/public/data/quotes.json.

Uses the existing backend collectors (yfinance for NYSE/Nasdaq, FinanceDataReader
or yfinance for KOSPI/KOSDAQ). Does not invent prices.

    python scripts/fetch_quotes_snapshot.py --out frontend/public/data/quotes.json

Requires: backend venv with yfinance (+ FinanceDataReader recommended).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.market import quotes as qt  # noqa: E402
from app.market.config import Settings  # noqa: E402
from app.market.store import Store  # noqa: E402
from app.service import load_network  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    args = p.parse_args()

    settings = Settings.load()
    settings.scheduler_enabled = False
    store = Store(settings.db_path)
    net = load_network()
    tg = qt.targets(net)

    us = tg.get("us") or []
    kr = tg.get("krx") or []
    print(f"collect US={len(us)} KR={len(kr)}", flush=True)

    us_res = qt.collect_us_quotes(settings, store, us) if us else {"status": "skip", "ok": 0}
    print("US", us_res.get("status"), "ok", us_res.get("ok"), flush=True)

    kr_res = qt.collect_krx(settings, store, kr) if kr else {"status": "skip", "ok": 0}
    print("KR", kr_res.get("status"), "ok", kr_res.get("ok"), flush=True)

    try:
        fx_res = qt.collect_fx(settings, store)
        print("FX", fx_res.get("status"), flush=True)
    except Exception as e:  # noqa: BLE001
        print("FX skip:", e, flush=True)

    out = qt.overview(store, settings, net)
    out["static"] = True
    out["demo"] = False
    priced = sum(1 for i in out["items"] if i.get("price") is not None)
    out["note"] = (
        f"관측 시세 스냅샷 ({priced}개 종목 가격 포함). "
        "미국: yfinance 일간 종가 · 한국: FinanceDataReader/yfinance. "
        "금리 충격 시나리오와 무관합니다. 결측은 비워 두며 숫자를 만들지 않습니다."
    )

    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", path, "priced", priced, "/", len(out["items"]), flush=True)
    return 0 if priced > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
