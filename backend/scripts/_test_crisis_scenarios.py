"""Validate crisis modes A/B/C against local TS engine via Node is heavy — use Python mirror of key expectations.

For full parity the frontend TypeScript engine is authoritative for crisis_mode.
This script validates dataset presence and that SPV/parent separation is documented.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.service import load_network  # noqa: E402


def main() -> None:
    net = load_network()
    ids = {n["id"] for n in net["nodes"]}
    required = [
        "core_scientific", "applied_digital", "galaxy_digital",
        "cipher_digital", "whitefiber", "terawulf", "iren", "nscale",
        "nebius", "soluna", "hut8", "corz_finance_i", "galaxy_helios_ii", "macquarie",
    ]
    missing = [x for x in required if x not in ids]
    assert not missing, missing
    print("nodes", len(ids), "all required present")

    sector = json.loads((ROOT / "backend/data/sector_stress.json").read_text(encoding="utf-8"))
    assert "corz_finance_i" in sector["entities"]
    assert sector["entities"]["corz_finance_i"]["parent_id"] == "core_scientific"
    assert sector["entities"]["nscale"]["data_quality"] == "insufficient"
    assert sector["entities"]["soluna"]["resilience"] == "low_leverage"
    print("sector_stress.json OK")

    # Frontend engine test via a tiny node script
    print("Run frontend crisis tests separately via node")


if __name__ == "__main__":
    main()
