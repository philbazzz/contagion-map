"""Settings loaded from environment variables or backend/.env (never shipped)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader (KEY=VALUE lines). Existing environment variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _flag(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None or v == "":
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


DEFAULT_GPU_CONDITION = {
    "gpu_name": ["H100 SXM"],        # Vast.ai model label; PCIe / NVL are separate products
    "min_gpu_ram_mb": 79000,          # 80GB class
    "rental_type": "ondemand",        # never mixed with interruptible ("bid")
    "num_gpus_min": 1,
    "num_gpus_max": 8,                # price normalised to 1 GPU · 1 hour
    "verified_only": True,
    "region": "ALL",                  # two-letter country codes, or ALL
    "allocated_storage_gb": 1,        # smallest disk so the storage add-on in dph_total stays negligible
    "limit": 500,
}


@dataclass
class Settings:
    fred_api_key: str = ""
    vast_api_key: str = ""
    finnhub_api_key: str = ""        # US-listed quotes (Finnhub)
    data_go_kr_key: str = ""         # KRX daily close (금융위원회_주식시세정보, 공공데이터포털)
    koreaexim_api_key: str = ""      # KRW exchange rates (한국수출입은행)
    open_dart_api_key: str = ""      # Open DART (금융감독원) — server-side only
    db_path: Path = BACKEND_DIR / "data" / "market.db"
    http_timeout: float = 15.0
    http_retries: int = 3
    scheduler_enabled: bool = True
    check_interval_sec: int = 1800
    hy_refresh_hours: float = 12.0
    gpu_refresh_hours: float = 24.0
    retry_after_failure_min: float = 60.0
    manual_refresh_min_interval_sec: int = 300
    us_quote_refresh_min: float = 15.0     # Finnhub free plan: 60 calls/min, 30/s
    krx_refresh_hours: float = 6.0         # daily close, published the next business day after 13:00 KST
    fx_refresh_hours: float = 6.0          # Eximbank publishes once per business day
    gpu_condition: dict = field(default_factory=lambda: dict(DEFAULT_GPU_CONDITION))
    hy_public_export: bool = False   # ICE data: internal use only unless ICE grants permission

    @classmethod
    def load(cls) -> "Settings":
        _load_dotenv(BACKEND_DIR / ".env")
        cond = dict(DEFAULT_GPU_CONDITION)
        raw = os.environ.get("GPU_CONDITION_JSON", "").strip()
        if raw:
            try:
                cond.update(json.loads(raw))
            except json.JSONDecodeError:
                pass
        db = os.environ.get("MARKET_DB_PATH", "").strip()
        return cls(
            fred_api_key=os.environ.get("FRED_API_KEY", "").strip(),
            vast_api_key=os.environ.get("VASTAI_API_KEY", "").strip(),
            finnhub_api_key=os.environ.get("FINNHUB_API_KEY", "").strip(),
            data_go_kr_key=os.environ.get("DATA_GO_KR_SERVICE_KEY", "").strip(),
            koreaexim_api_key=os.environ.get("KOREAEXIM_API_KEY", "").strip(),
            open_dart_api_key=os.environ.get("OPEN_DART_API_KEY", "").strip(),
            db_path=Path(db) if db else BACKEND_DIR / "data" / "market.db",
            scheduler_enabled=_flag("MARKET_SCHEDULER", True),
            gpu_condition=cond,
            hy_public_export=_flag("HY_OAS_PUBLIC_EXPORT", False),
        )

    def secrets(self) -> list:
        # Values only — never expose key names/values via API responses that embed this list blindly
        return [s for s in (self.fred_api_key, self.vast_api_key, self.finnhub_api_key,
                            self.data_go_kr_key, self.koreaexim_api_key, self.open_dart_api_key) if s]
