#!/usr/bin/env python3
"""Fetch USD/KRW and US market caps for semiconductor expansion eligibility (≥ KRW 500B).

Writes frontend/public/data/pf/_us_mcap_eligibility.json and prints a summary.
Does not invent prices. Failed tickers are excluded with reason.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "data" / "_us_mcap_eligibility.json"

# Seed tickers (Yahoo). Private / unclear listing left out of fetch list.
SEEDS = [
    ("nvidia", "NVDA", "GPU"),
    ("amd", "AMD", "GPU/CPU"),
    ("intel", "INTC", "CPU/foundry"),
    ("broadcom", "AVGO", "custom/networking"),
    ("marvell", "MRVL", "custom/networking"),
    ("qualcomm", "QCOM", "custom/networking"),
    ("macom", "MTSI", "custom/networking"),
    ("maxlinear", "MXL", "custom/networking"),
    ("semtech", "SMTC", "custom/networking"),
    ("micron", "MU", "memory"),
    ("wdc", "WDC", "storage (SanDisk parent)"),
    ("lattice", "LSCC", "FPGA"),
    ("microchip", "MCHP", "embedded"),
    ("ambarella", "AMBA", "edge AI"),
    ("synaptics", "SYNA", "edge AI"),
    ("silabs", "SLAB", "edge AI"),
    ("ti", "TXN", "analog"),
    ("adi", "ADI", "analog"),
    ("diodes", "DIOD", "analog"),
    ("cirrus", "CRUS", "analog"),
    ("mps", "MPWR", "power"),
    ("power_integrations", "POWI", "power"),
    ("onsemi", "ON", "power"),
    ("aos", "AOSL", "power"),
    ("vishay", "VSH", "power"),
    ("wolfspeed", "WOLF", "power"),
    ("navitas", "NVTS", "power"),
    ("allegro", "ALGM", "auto/sensors"),
    ("indie", "INDI", "auto/sensors"),
    ("astera", "ALAB", "interconnect/IP"),
    ("credo", "CRDO", "interconnect/IP"),
    ("rambus", "RMBS", "interconnect/IP"),
    ("arteris", "AIP", "interconnect/IP"),
    ("sitime", "SITM", "timing/MEMS"),
    ("knowles", "KN", "timing/MEMS"),
    ("coherent", "COHR", "optical"),
    ("lumentum", "LITE", "optical"),
    ("aoi", "AAOI", "optical"),
    ("globalfoundries", "GFS", "foundry"),
    ("amkor", "AMKR", "packaging"),
    ("synopsys", "SNPS", "EDA"),
    ("cadence", "CDNS", "EDA"),
    ("applied_materials", "AMAT", "equipment"),
    ("lam_research", "LRCX", "equipment"),
    ("veeco", "VECO", "equipment"),
    ("acm_research", "ACMR", "equipment"),
    ("axcelis", "ACLS", "equipment"),
    ("kla", "KLAC", "metrology"),
    ("onto", "ONTO", "metrology"),
    ("teradyne", "TER", "test"),
    ("cohu", "COHU", "test"),
    ("aehr", "AEHR", "test"),
    ("formfactor", "FORM", "test"),
    ("keysight", "KEYS", "test"),
    ("bruker", "BRKR", "test"),
    ("thermo_fisher", "TMO", "test"),
    ("mks", "MKSI", "subsystems"),
    ("advanced_energy", "AEIS", "subsystems"),
    ("ichor", "ICHR", "subsystems"),
    ("ultra_clean", "UCTT", "subsystems"),
    ("enpro", "NPO", "subsystems"),
    ("entegris", "ENTG", "materials"),
    ("photronics", "PLAB", "materials"),
    ("axt", "AXTI", "materials"),
    ("element_solutions", "ESI", "materials"),
    ("rogers", "ROG", "materials"),
    ("materion", "MTRN", "materials"),
    ("dow", "DOW", "materials"),
    ("air_products", "APD", "materials"),
    ("corning", "GLW", "materials"),
    ("arrow", "ARW", "distribution"),
    ("avnet", "AVT", "distribution"),
    ("alphabet", "GOOGL", "downstream"),
    ("amazon", "AMZN", "downstream"),
    ("microsoft", "MSFT", "downstream"),
    ("meta", "META", "downstream"),
    ("apple", "AAPL", "downstream"),
    ("tesla", "TSLA", "downstream"),
    ("ibm", "IBM", "downstream"),
]

THRESHOLD_KRW = 500_000_000_000  # 500 billion KRW
PRIVATE_EXCLUDED = [
    {"id": "cerebras", "reason": "private — excluded from mcap-filtered US set"},
    {"id": "ambiq", "reason": "listing unclear / not treated as liquid US public seed without verified ticker"},
    {"id": "sandisk_standalone", "reason": "use Western Digital (WDC) as listed parent; SanDisk not separate listed entity for this pass"},
    {"id": "qnity", "reason": "ticker/listing not verified in this pass — research queue"},
]


def main() -> int:
    import yfinance as yf

    now = datetime.now(timezone.utc).isoformat()
    # USD/KRW via Yahoo KRW=X
    fx = yf.Ticker("KRW=X")
    fi = fx.fast_info
    usdkrw = float(getattr(fi, "last_price", None) or getattr(fi, "lastPrice", None) or 0)
    if not usdkrw:
        # fallback hist
        h = fx.history(period="5d")
        if h is not None and len(h):
            usdkrw = float(h["Close"].iloc[-1])
    if not usdkrw:
        raise SystemExit("USD/KRW fetch failed — refusing to invent FX")

    threshold_usd = THRESHOLD_KRW / usdkrw
    rows = []
    for eid, ticker, bucket in SEEDS:
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            mcap = getattr(info, "market_cap", None) or getattr(info, "marketCap", None)
            if mcap is None:
                # slow path
                inf = t.info or {}
                mcap = inf.get("marketCap")
            if mcap is None:
                rows.append({
                    "id": eid, "ticker": ticker, "bucket": bucket,
                    "status": "fetch_failed", "eligible": False,
                    "reason": "marketCap unavailable",
                })
                continue
            mcap = float(mcap)
            mcap_krw = mcap * usdkrw
            eligible = mcap_krw >= THRESHOLD_KRW
            rows.append({
                "id": eid, "ticker": ticker, "bucket": bucket,
                "status": "ok",
                "market_cap_usd": mcap,
                "market_cap_krw": mcap_krw,
                "eligible": eligible,
                "reason": None if eligible else f"below KRW 500B (≈ ${threshold_usd:,.0f})",
            })
        except Exception as e:  # noqa: BLE001
            rows.append({
                "id": eid, "ticker": ticker, "bucket": bucket,
                "status": "error", "eligible": False, "reason": str(e),
            })

    out = {
        "retrieved_at": now,
        "fx": {
            "pair": "USD/KRW",
            "rate": usdkrw,
            "source": "Yahoo Finance KRW=X (yfinance)",
            "formula": "market_cap_krw = market_cap_usd × usd_krw_rate",
            "threshold_krw": THRESHOLD_KRW,
            "threshold_usd_equiv": threshold_usd,
        },
        "private_or_unlisted_excluded": PRIVATE_EXCLUDED,
        "items": rows,
        "eligible_ids": [r["id"] for r in rows if r.get("eligible")],
        "excluded_ids": [r["id"] for r in rows if not r.get("eligible")],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"FX USD/KRW={usdkrw:.2f} @ {now}")
    print(f"eligible {len(out['eligible_ids'])} / {len(rows)}")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
