"""Open DART (opendart.fss.or.kr) API client with disk cache and retries.

API key is read from OPEN_DART_API_KEY (backend/.env). Never log or return the key.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from ..market.config import BACKEND_DIR, _load_dotenv

CACHE_DIR = BACKEND_DIR / "data" / "opendart_cache"
BASE = "https://opendart.fss.or.kr/api"


class OpenDartError(Exception):
    def __init__(self, message: str, *, code: str = "error", configured: bool = True):
        super().__init__(message)
        self.code = code
        self.configured = configured


def _key() -> str:
    _load_dotenv(BACKEND_DIR / ".env")
    return (os.environ.get("OPEN_DART_API_KEY") or "").strip()


class OpenDartClient:
    def __init__(self, api_key: str | None = None, cache_dir: Path = CACHE_DIR, timeout: float = 20.0):
        self.api_key = (api_key if api_key is not None else _key()).strip()
        self.cache_dir = cache_dir
        self.timeout = timeout
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def status(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "cache_dir": "data/opendart_cache",
            "note": None if self.configured else "Set OPEN_DART_API_KEY in backend/.env (server-side only).",
        }

    def _cache_path(self, endpoint: str, params: dict[str, str]) -> Path:
        blob = endpoint + "?" + urllib.parse.urlencode(sorted((k, v) for k, v in params.items() if k != "crtfc_key"))
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]
        safe = endpoint.replace("/", "_")
        return self.cache_dir / f"{safe}_{h}.json"

    def _get(self, endpoint: str, params: dict[str, str], *, max_retries: int = 3) -> dict[str, Any]:
        if not self.api_key:
            raise OpenDartError(
                "OPEN_DART_API_KEY is not configured in backend/.env",
                code="not_configured",
                configured=False,
            )
        cache = self._cache_path(endpoint, params)
        if cache.exists():
            try:
                return json.loads(cache.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        q = dict(params)
        q["crtfc_key"] = self.api_key
        url = f"{BASE}/{endpoint}.json?{urllib.parse.urlencode(q)}"
        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "contagion-opendart/1.0"})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                data = json.loads(raw)
                # Never persist the key; response itself does not include it
                cache.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                return data
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code in (429, 500, 502, 503, 504) and attempt + 1 < max_retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise OpenDartError(f"Open DART HTTP {e.code}", code="http_error") from e
            except Exception as e:  # noqa: BLE001
                last_err = e
                if attempt + 1 < max_retries:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                raise OpenDartError(str(e), code="request_failed") from e
        raise OpenDartError(str(last_err or "request failed"), code="request_failed")

    def company_list(self, corp_name: str) -> dict[str, Any]:
        """Resolve corp code by name (corpCode download is XML; use list for search via company.json if available).

        Open DART primary lookup uses corpCode.xml. We also accept a known corp_code directly.
        """
        # Prefer cached corp codes index if present
        index = self.cache_dir / "corp_codes_index.json"
        if index.exists():
            try:
                rows = json.loads(index.read_text(encoding="utf-8"))
                hits = [r for r in rows if corp_name.replace(" ", "") in (r.get("corp_name") or "").replace(" ", "")]
                return {"status": "ok", "source": "cache_index", "list": hits[:50]}
            except json.JSONDecodeError:
                pass
        return {
            "status": "index_missing",
            "note": "Run POST /api/opendart/sync-corp-codes to download corpCode.xml once, then search.",
            "list": [],
            "query": corp_name,
        }

    def disclosure_list(
        self,
        *,
        corp_code: str,
        bgn_de: str,
        end_de: str,
        pblntf_ty: str | None = None,
        page_count: int = 100,
        page_no: int = 1,
    ) -> dict[str, Any]:
        params = {
            "corp_code": corp_code,
            "bgn_de": bgn_de,
            "end_de": end_de,
            "page_count": str(page_count),
            "page_no": str(page_no),
        }
        if pblntf_ty:
            params["pblntf_ty"] = pblntf_ty
        return self._get("list", params)

    def document_meta(self, rcept_no: str) -> dict[str, Any]:
        """Return viewer URL + cached list hit if any. Document body requires separate download API."""
        return {
            "rcept_no": rcept_no,
            "viewer_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}",
            "note": "Full document text is not mirrored into the browser; open the viewer URL or use server-side download.",
        }

    def download_document_zip(self, rcept_no: str, *, max_retries: int = 3) -> bytes:
        """Download filing original as ZIP bytes (OpenDART /api/document.xml). Never logs the key."""
        if not self.api_key:
            raise OpenDartError("OPEN_DART_API_KEY is not configured", code="not_configured", configured=False)
        cache = self.cache_dir / "docs" / f"{rcept_no}.zip"
        cache.parent.mkdir(parents=True, exist_ok=True)
        if cache.exists() and cache.stat().st_size > 100:
            return cache.read_bytes()
        q = urllib.parse.urlencode({"crtfc_key": self.api_key, "rcept_no": rcept_no})
        url = f"{BASE}/document.xml?{q}"
        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "contagion-opendart/1.0"})
                with urllib.request.urlopen(req, timeout=90) as resp:
                    blob = resp.read()
                # Error responses are small JSON/XML; real docs are zip
                if blob[:2] != b"PK" and len(blob) < 500:
                    try:
                        msg = json.loads(blob.decode("utf-8", errors="replace"))
                        raise OpenDartError(
                            f"document download failed: {msg.get('status')} {msg.get('message')}",
                            code=str(msg.get("status") or "doc_error"),
                        )
                    except json.JSONDecodeError:
                        raise OpenDartError("document download returned non-zip payload", code="doc_error")
                cache.write_bytes(blob)
                return blob
            except OpenDartError:
                raise
            except Exception as e:  # noqa: BLE001
                last_err = e
                if attempt + 1 < max_retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise OpenDartError(str(e), code="request_failed") from e
        raise OpenDartError(str(last_err or "download failed"), code="request_failed")

    def document_text(self, rcept_no: str, *, max_chars: int = 2_000_000) -> dict[str, Any]:
        """Unzip filing and concatenate XML/text for keyword search (server-side only)."""
        import io
        import re
        import zipfile

        blob = self.download_document_zip(rcept_no)
        parts: list[str] = []
        names: list[str] = []
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            for name in zf.namelist():
                lower = name.lower()
                if not (lower.endswith(".xml") or lower.endswith(".txt") or lower.endswith(".html") or lower.endswith(".htm")):
                    continue
                names.append(name)
                raw = zf.read(name)
                text = raw.decode("utf-8", errors="replace")
                # Strip tags lightly for HTML/XML
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text)
                parts.append(text)
                if sum(len(p) for p in parts) >= max_chars:
                    break
        joined = " ".join(parts)[:max_chars]
        return {
            "rcept_no": rcept_no,
            "files": names,
            "text_len": len(joined),
            "text": joined,
            "viewer_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}",
        }

    def sync_corp_codes(self) -> dict[str, Any]:
        """Download corpCode.xml.zip once and build a local name→code index (cached)."""
        if not self.api_key:
            raise OpenDartError("OPEN_DART_API_KEY is not configured", code="not_configured", configured=False)
        import io
        import zipfile
        import xml.etree.ElementTree as ET

        url = f"{BASE}/corpCode.xml?crtfc_key={urllib.parse.quote(self.api_key)}"
        req = urllib.request.Request(url, headers={"User-Agent": "contagion-opendart/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            blob = resp.read()
        # Response is a zip containing CORPCODE.xml
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            name = next(n for n in zf.namelist() if n.lower().endswith(".xml"))
            xml_bytes = zf.read(name)
        root = ET.fromstring(xml_bytes)
        rows = []
        for el in root.findall("list"):
            rows.append({
                "corp_code": (el.findtext("corp_code") or "").strip(),
                "corp_name": (el.findtext("corp_name") or "").strip(),
                "stock_code": (el.findtext("stock_code") or "").strip(),
                "modify_date": (el.findtext("modify_date") or "").strip(),
            })
        index = self.cache_dir / "corp_codes_index.json"
        index.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        return {"status": "ok", "count": len(rows), "cached_as": "corp_codes_index.json"}

    def verify_edge_rcept(self, rcept_no: str) -> dict[str, Any]:
        """Lightweight verification: confirm filing is addressable; do not invent relationship facts."""
        meta = self.document_meta(rcept_no)
        return {
            "rcept_no": rcept_no,
            "verified_reachable": True,
            "viewer_url": meta["viewer_url"],
            "interpretation": "Filing reference present. Relationship details must be read from the document notes; API absence ≠ no relationship.",
        }


_client: OpenDartClient | None = None


def get_client() -> OpenDartClient:
    global _client
    if _client is None:
        _client = OpenDartClient()
    return _client
