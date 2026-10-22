"""Write the redistributable market snapshot used by the public HTML demo.

    python export_public_snapshot.py      -> data/market_public_snapshot.json

HY OAS (ICE BofA) values are excluded unless HY_OAS_PUBLIC_EXPORT=true AND you
hold ICE's permission. API keys are never written.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.market.overview import MarketService  # noqa: E402

if __name__ == "__main__":
    ms = MarketService()
    snap = ms.public_snapshot()
    text = json.dumps(snap, ensure_ascii=False, indent=2)
    for secret in ms.settings.secrets():
        assert secret not in text, "refusing to export: secret found in payload"
    out = Path(__file__).resolve().parent / "data" / "market_public_snapshot.json"
    out.write_text(text, encoding="utf-8")
    print(f"written {out}")
