#!/usr/bin/env python3
"""Fetch dc.namepf.com page and discover JSON data endpoints."""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "data" / "pf"
UA = {"User-Agent": "Mozilla/5.0 (compatible; ContagionResearch/1.0)"}


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def main() -> None:
    html = get("https://dc.namepf.com/").decode("utf-8", "replace")
    (ROOT / "tmp_dc.html").write_text(html, encoding="utf-8")
    print("html_len", len(html))

    refs = sorted(set(re.findall(r"""["']([^"']*(?:api|/data/|\.json|permits|assets)[^"']*)["']""", html, re.I)))
    for m in refs[:50]:
        print("ref", m[:160])

    srcs = re.findall(r"""src=["']([^"']+)["']""", html)
    for m in srcs[:30]:
        print("src", m)

    # Try common Next/Vite/static data paths
    candidates = [
        "https://dc.namepf.com/data/permits.json",
        "https://dc.namepf.com/data/projects.json",
        "https://dc.namepf.com/api/permits",
        "https://dc.namepf.com/api/projects",
        "https://dc.namepf.com/permits.json",
    ]
    # Also pull from script chunks that might embed __NEXT_DATA__
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if m:
        data = json.loads(m.group(1))
        (OUT / "dc_namepf_next_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("saved __NEXT_DATA__ keys", list(data.keys())[:20])
    else:
        print("no __NEXT_DATA__")

    for url in candidates:
        try:
            body = get(url)
            print("OK", url, len(body), body[:80])
            name = url.rstrip("/").split("/")[-1] or "index"
            if not name.endswith(".json"):
                name += ".json"
            (OUT / f"dc_namepf_{name}").write_bytes(body)
        except Exception as e:
            print("FAIL", url, type(e).__name__, e)


if __name__ == "__main__":
    main()
