#!/usr/bin/env python3
"""Fetch observed quotes for the AI Data Center PF network into pf/quotes.json.

    python scripts/fetch_pf_quotes.py
    python scripts/fetch_pf_quotes.py --out frontend/public/data/pf/quotes.json

Uses the same collectors as semiconductor quotes (yfinance / FinanceDataReader).
Does not invent prices. Unlisted entities are marked 비상장.
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--network",
        default=str(ROOT / "frontend" / "public" / "data" / "pf" / "network.json"),
    )
    p.add_argument(
        "--out",
        default=str(ROOT / "frontend" / "public" / "data" / "pf" / "quotes.json"),
    )
    args = p.parse_args()

    net_path = Path(args.network)
    if not net_path.is_file():
        print("missing PF network:", net_path, flush=True)
        return 1

    net = json.loads(net_path.read_text(encoding="utf-8"))
    # Normalize exchange labels so coverage() accepts PF nodes
    for n in net.get("nodes") or []:
        ex = (n.get("exchange") or "").upper()
        if ex == "KRX" and n.get("ticker"):
            n["exchange"] = "KRX"  # already in KR_EXCHANGES
        if n.get("listed") and not n.get("ticker"):
            n["listed"] = False
            n["listing_note"] = (n.get("listing_note") or "") + " · 티커 미확인 — 비상장으로 표시"

    settings = Settings.load()
    settings.scheduler_enabled = False
    store = Store(settings.db_path)
    tg = qt.targets(net)

    us = tg.get("us") or []
    kr = tg.get("krx") or []
    print(f"PF collect US={len(us)} KR={len(kr)}", flush=True)

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
    out["ecosystem"] = "datacenter_pf"
    priced = sum(1 for i in out["items"] if i.get("price") is not None)
    listed = sum(1 for i in out["items"] if i.get("listed"))
    out["note"] = (
        f"AI Data Center PF 관측 시세 ({priced}/{listed} 상장사 가격). "
        "미국: yfinance 일간 종가 · 한국: FinanceDataReader/yfinance (KRX). "
        "결측은 비워 두며 0이나 모회사 시세로 대체하지 않습니다. 비상장은 '비상장'으로 표시합니다."
    )

    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", path, "priced", priced, "/", listed, "listed /", len(out["items"]), "nodes", flush=True)
    return 0 if priced > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
