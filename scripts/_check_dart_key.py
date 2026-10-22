"""Check OPEN_DART_API_KEY is set without printing it."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.opendart.client import OpenDartClient  # noqa: E402

c = OpenDartClient()
print("configured", c.configured)
print("status", c.status())
