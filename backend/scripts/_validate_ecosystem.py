"""One-shot validation for multi-center ecosystem expansion."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.engine.relations import network_stats, shortest_path  # noqa: E402
from app.service import load_network  # noqa: E402

load_network.cache_clear()
n = load_network()
profiles = n.get("profiles") or {}

print("=== ENTITY / RELATIONSHIP COUNTS ===")
print(f"entities: {len(n['nodes'])}")
print(f"relationships: {len(n['edges'])}")
print(f"detailed_profiles: {len(profiles)}")
print(f"instruments: {len(n['financials']['instruments'])}")
print(f"contracts: {len(n['contracts'])}")

print("\n=== BY INDUSTRY / GROUP ===")
for g, c in sorted(Counter(e["group"] for e in n["nodes"]).items(), key=lambda x: -x[1]):
    print(f"  {g}: {c}")

print("\n=== BY RELATIONSHIP TYPE ===")
for t, c in sorted(Counter(e["relationship_type"] for e in n["edges"]).items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

print("\n=== BY IMPACT CHANNEL ===")
for t, c in sorted(Counter(e["impact_channel"] for e in n["edges"]).items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

cw = sum(1 for e in n["edges"] if e["source"] == "coreweave" or e["target"] == "coreweave")
print(f"\nCW-touching edges: {cw}")
print(f"non-CW edges: {len(n['edges']) - cw}")

print("\n=== FOCAL COMPANY NETWORK STATS ===")
for oid in [
    "coreweave",
    "nvidia",
    "microsoft",
    "oracle",
    "tsmc",
    "sk_hynix",
    "samsung",
    "amazon",
    "meta",
    "openai",
]:
    if not any(x["id"] == oid for x in n["nodes"]):
        print(f"  MISSING node: {oid}")
        continue
    s = network_stats(n, oid)
    has_prof = oid in profiles
    print(
        f"  {oid}: direct={s['direct']} indirect={s['indirect']} "
        f"unconnected={s['unconnected']} profile={has_prof}"
    )

print("\n=== SAMPLE SHORTEST PATHS ===")
for a, b in [
    ("microsoft", "nvidia"),
    ("amazon", "tsmc"),
    ("nvidia", "asml"),
    ("openai", "microsoft"),
    ("oracle", "nvidia"),
    ("samsung", "nvidia"),
    ("coreweave", "microsoft"),
]:
    p = shortest_path(n, a, b)
    if p:
        print(f"  {a} -> {b}: hops={p['hops']} path={p['nodes']}")
    else:
        print(f"  {a} -> {b}: NO PATH")

print("\n=== PROFILES LIST ===")
for pid in sorted(profiles):
    p = profiles[pid]
    metrics = p.get("metrics") or []
    verified = sum(1 for x in metrics if x.get("status") == "VERIFIED" and (x.get("value_usd_m") is not None or x.get("display")))
    print(f"  {pid}: metrics={len(metrics)} verified_display={verified} period={p.get('period_label')}")

print("\n=== COMPANIES WITHOUT DETAILED PROFILE (sample majors) ===")
majors = [
    "amazon",
    "meta",
    "google",
    "amd",
    "broadcom",
    "equinix",
    "digital_realty",
    "supermicro",
    "dell",
    "hpe",
    "arista",
    "vertiv",
    "eaton",
    "schneider",
]
for m in majors:
    if any(x["id"] == m for x in n["nodes"]):
        print(f"  {m}: profile={'yes' if m in profiles else 'NO (overview only)'}")
