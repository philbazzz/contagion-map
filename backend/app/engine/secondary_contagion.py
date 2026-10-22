"""Secondary (counterparty) stress when CoreWeave enters modeled distress.

Mechanism B — separate from direct SOFR floating interest sensitivity.
Analytical scenario estimates — NOT confirmed default or bankruptcy.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .stress_model import stress_status

CW_LESSOR_EXPOSURES = [
    {
        "entity_id": "core_scientific",
        "name": "Core Scientific",
        "tier": "sole_segment",
        "contract_value_usd_m": 10200,
        "concentration_note": (
            "Disclosed CoreWeave leases ~590 MW / $10.2B landlord contract revenue (12y) "
            "— primary single-tenant AI colocation concentration."
        ),
        "source_ids": ["S_CORZ"],
        "edge_prefer": "facility",
    },
    {
        "entity_id": "applied_digital",
        "name": "Applied Digital",
        "tier": "material_backlog",
        "contract_value_usd_m": 7000,
        "concentration_note": (
            "IR: Ellendale ND ~250 MW AI lease to CoreWeave; "
            "~$7B expected landlord revenue over ~15 years (material contracted backlog)."
        ),
        "source_ids": ["S_APLD"],
        "edge_prefer": "facility",
    },
    {
        "entity_id": "galaxy_digital",
        "name": "Galaxy Digital",
        "tier": "named_campus_tenant",
        "contract_value_usd_m": None,
        "concentration_note": (
            "10-K / IR: Helios campus 15-year leases to CoreWeave for 526 MW critical IT load "
            "(Phases I–III); expected >$1B average annual revenue; Data Centers segment anchored by CW."
        ),
        "source_ids": ["S_GLXY_10K25", "S_GLXY_HELIOS"],
        "edge_prefer": "facility",
    },
]

LABEL_EN = {
    "moderate": "Modeled Counterparty Stress",
    "high": "Secondary High Financial Stress",
    "critical": "Secondary Critical Financial Distress",
}
LABEL_KO = {
    "moderate": "거래상대방 스트레스(시나리오)",
    "high": "2차 높은 재무 스트레스",
    "critical": "2차 심각 재무 압박 — 시나리오 추정",
}


def _map_tier(tier: str, origin: str, shock_bp: float) -> Optional[str]:
    if origin in ("normal", "insufficient", "not_applicable"):
        return None
    if tier == "sole_segment":
        if origin == "moderate":
            return "moderate"
        if origin == "high":
            return "high"
        if origin == "critical":
            return "critical"
    if tier in ("material_backlog", "named_campus_tenant"):
        if origin == "moderate":
            return None
        if origin == "high":
            return "moderate"
        if origin == "critical":
            return "critical" if shock_bp >= 500 else "high"
    return None


def _intensity(level: str) -> float:
    return {"moderate": 0.9, "high": 1.2, "critical": 1.55}.get(level, 0.45)


def compute_secondary_stress(
    origin_level: Optional[str],
    shock_bp: float,
    present_entity_ids: Set[str],
) -> List[Dict[str, Any]]:
    if not origin_level:
        return []
    out: List[Dict[str, Any]] = []
    for exp in CW_LESSOR_EXPOSURES:
        eid = exp["entity_id"]
        if eid not in present_entity_ids:
            continue
        level = _map_tier(exp["tier"], origin_level, shock_bp)
        if not level:
            continue
        out.append({
            "entity_id": eid,
            "level": level,
            "intensity": _intensity(level),
            "mechanism": "secondary_contagion",
            "label_en": LABEL_EN[level],
            "label_ko": LABEL_KO[level],
            "reason": (
                f"CoreWeave {origin_level} 시나리오 + {exp['concentration_note']} "
                "직접 SOFR 이자 민감도와 별개의 2차(임차료·가동) 경로. 확정 부도·파산이 아님."
            ),
            "source_ids": list(exp["source_ids"]),
            "origin_level": origin_level,
            "shock_bp": shock_bp,
        })
    return out


def secondary_node_status(level: str) -> str:
    return stress_status(level, True)
