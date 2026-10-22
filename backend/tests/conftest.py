import copy
import os
import sys
import tempfile
from pathlib import Path

# tests never call real APIs, never start the scheduler and never touch the real database
os.environ["MARKET_SCHEDULER"] = "false"
os.environ["MARKET_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test_market.db")
os.environ["FRED_API_KEY"] = ""
os.environ["VASTAI_API_KEY"] = ""

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.service import load_network  # noqa: E402


@pytest.fixture
def network():
    return copy.deepcopy(load_network())
