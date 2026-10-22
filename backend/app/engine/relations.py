"""Relationship graph: the SAME edge list the 3D map draws.

Relationship paths (type A) are found on an undirected graph of every VERIFIED or INFERRED
relationship, so any entity the map connects to CoreWeave also has a path here. Whether an
impact on that entity can be *quantified* is a separate question answered by the refinancing
engine (types B-E); a missing number never hides an existing relationship.
"""
from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional

PATH_STATUSES = ("VERIFIED", "INFERRED")
FINANCING_KINDS = ("term_loan", "revolver", "senior_notes", "convertible", "other_loan")
INDUSTRIAL_CHANNELS = ("supply_chain", "customer", "facility", "contract")
# when two entities share several relationships, a path is labelled by the most direct business channel
CHANNEL_RANK = {"supply_chain": 0, "financial": 1, "equity": 2, "customer": 3, "facility": 4, "contract": 5}


def adjacency(net: dict) -> Dict[str, List[dict]]:
    adj: Dict[str, List[dict]] = {}
    for e in net["edges"]:
        if e["source_status"] not in PATH_STATUSES:
            continue
        adj.setdefault(e["source"], []).append({"edge": e, "to": e["target"]})
        adj.setdefault(e["target"], []).append({"edge": e, "to": e["source"]})
    # deterministic order: verified first, then the most direct business channel, then edge id
    for k in adj:
        adj[k].sort(key=lambda x: (x["edge"]["source_status"] != "VERIFIED",
                                   CHANNEL_RANK.get(x["edge"]["impact_channel"], 9), x["edge"]["id"]))
    return adj


def shortest_path(net: dict, a: str, b: str) -> Optional[dict]:
    """Fewest-hop relationship path between two entities (direction ignored), or None."""
    ids = {n["id"] for n in net["nodes"]}
    if a not in ids or b not in ids:
        return None
    if a == b:
        return {"nodes": [a], "edges": [], "hops": 0, "statuses": []}
    adj = adjacency(net)
    prev: Dict[str, tuple] = {a: (None, None)}
    q = deque([a])
    while q:
        cur = q.popleft()
        for step in adj.get(cur, []):
            nxt = step["to"]
            if nxt in prev:
                continue
            prev[nxt] = (cur, step["edge"])
            if nxt == b:
                q.clear()
                break
            q.append(nxt)
    if b not in prev:
        return None
    nodes, edges = [b], []
    cur = b
    while prev[cur][0] is not None:
        p, e = prev[cur]
        edges.append(e)
        nodes.append(p)
        cur = p
    nodes.reverse()
    edges.reverse()
    return {"nodes": nodes, "edges": [e["id"] for e in edges], "hops": len(edges),
            "statuses": [e["source_status"] for e in edges]}


def hop_distances(net: dict, origin: str) -> Dict[str, int]:
    adj = adjacency(net)
    dist = {origin: 0}
    q = deque([origin])
    while q:
        cur = q.popleft()
        for step in adj.get(cur, []):
            if step["to"] not in dist:
                dist[step["to"]] = dist[cur] + 1
                q.append(step["to"])
    return dist


def network_stats(net: dict, origin: str) -> dict:
    """Header counts, computed from the dataset (never typed in)."""
    dist = hop_distances(net, origin)
    others = [n["id"] for n in net["nodes"] if n["id"] != origin]
    instruments = net.get("financials", {}).get("instruments", [])
    return {
        "origin": origin,
        "entities": len(net["nodes"]),
        "direct": sum(1 for i in others if dist.get(i) == 1),
        "indirect": sum(1 for i in others if dist.get(i, 0) >= 2),
        "unconnected": sum(1 for i in others if i not in dist),
        "financing_contracts": sum(1 for x in instruments if x["kind"] in FINANCING_KINDS),
        "industrial_relationships": sum(1 for e in net["edges"] if e["impact_channel"] in INDUSTRIAL_CHANNELS),
        "financial_relationships": sum(1 for e in net["edges"] if e["impact_channel"] in ("financial", "equity")),
        "note": "공개자료로 확인된 기업·기관만 집계한 값이며, CoreWeave 생태계 전체 규모가 아닙니다.",
    }


def relationship_summary(net: dict, origin: str, entity_id: str) -> dict:
    """Relationship (type A) view of one entity: path, distance and the direct links between them."""
    path = shortest_path(net, origin, entity_id)
    direct = [e for e in net["edges"]
              if {e["source"], e["target"]} == {origin, entity_id}]
    if entity_id == origin:
        kind = "origin"
    elif path is None:
        kind = "unconfirmed"
    elif path["hops"] == 1:
        kind = "direct"
    else:
        kind = "indirect"
    return {"kind": kind, "path": path, "direct_edges": [e["id"] for e in direct]}
