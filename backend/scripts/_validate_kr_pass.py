from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.engine.relations import network_stats  # noqa: E402
from app.service import load_network  # noqa: E402

load_network.cache_clear()
n = load_network()
print("nodes", len(n["nodes"]), "edges", len(n["edges"]), "profiles", len(n.get("profiles") or {}))
for oid in [
    "arista", "vertiv", "hanmi_semi", "sk_telecom", "naver", "ls_electric",
    "sk_hynix", "tsmc", "samsung", "nvidia", "microsoft",
]:
    s = network_stats(n, oid)
    print(f"  {oid}: direct={s['direct']} profile={oid in (n.get('profiles') or {})}")

deg: dict[str, int] = defaultdict(int)
for e in n["edges"]:
    deg[e["source"]] += 1
    deg[e["target"]] += 1
lonely = [x["id"] for x in n["nodes"] if deg[x["id"]] == 0]
print("zero-degree", len(lonely), lonely)
print("rel_types", dict(Counter(e["relationship_type"] for e in n["edges"])))
kr = [x for x in n["nodes"] if (x.get("exchange") or "").upper() in ("KOSPI", "KOSDAQ") or (x.get("quote_currency") == "KRW" and x.get("listed"))]
print("korean_listed", len(kr), [x["id"] for x in kr])
