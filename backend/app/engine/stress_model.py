"""Evidence-based SOFR stress bands for CoreWeave (analytical — not covenants / default)."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

THRESHOLDS = {
    "moderate_delta_over_ocf": 0.02,
    "high_delta_over_ocf": 0.05,
    "critical_delta_over_ocf": 0.08,
    "critical_coverage": 2.5,
}


def _r(x: Optional[float], nd: int = 4) -> Optional[float]:
    if x is None:
        return None
    k = 10 ** nd
    return math.floor(float(x) * k + 0.5) / k


def _metric(fin: dict, mid: str) -> Optional[float]:
    for m in fin.get("metrics") or []:
        if m.get("id") == mid:
            return m.get("value_usd_m")
    return None


def compute_origin_stress(
    fin: dict,
    shock_bp: float,
    delta_interest_usd_m: Optional[float],
    floating_principal_usd_m: float,
    sofr_pct: float,
    has_computed: bool,
) -> Dict[str, Any]:
    source_ids = [fin.get("filing")] if fin.get("filing") else []
    base: Dict[str, Any] = {
        "entity": "coreweave",
        "level": "insufficient",
        "intensity": 0.35,
        "score_delta_over_ocf": None,
        "baseline_interest_ann_usd_m": None,
        "stressed_interest_ann_usd_m": None,
        "annualized_ocf_usd_m": None,
        "baseline_coverage": None,
        "stressed_coverage": None,
        "coverage_change": None,
        "delta_interest_usd_m": delta_interest_usd_m,
        "floating_principal_usd_m": floating_principal_usd_m or None,
        "cash_usd_m": _metric(fin, "cash"),
        "incremental_vs_cash_pct": None,
        "baseline_sofr_pct": sofr_pct,
        "stressed_sofr_pct": _r(sofr_pct + shock_bp / 100.0, 4),
        "shock_bp": shock_bp,
        "critical_sofr_pct": None,
        "critical_shock_bp": None,
        "bp_to_critical": None,
        "critical_trigger": None,
        "threshold_kind": "analytical",
        "assumptions": [
            "H1 interest/OCF ×2 annualized",
            "Only disclosed SOFR floating principal",
            "Analytical bands — not disclosed covenants",
        ],
        "limitations": [
            "No ICR covenant threshold in dataset",
            "Not a bankruptcy/default model",
        ],
        "source_ids": source_ids,
        "metric_trigger": None,
    }
    if not has_computed or floating_principal_usd_m <= 0 or delta_interest_usd_m is None:
        return base

    interest6 = _metric(fin, "interest_expense_6m")
    ocf6 = _metric(fin, "ocf_6m")
    cash = _metric(fin, "cash")
    if interest6 is None or ocf6 is None or ocf6 <= 0:
        base["limitations"].append("Missing H1 interest or OCF")
        return base

    baseline_ann = interest6 * 2
    ocf_ann = ocf6 * 2
    stressed_ann = baseline_ann + delta_interest_usd_m
    baseline_cov = ocf_ann / baseline_ann
    stressed_cov = ocf_ann / stressed_ann if stressed_ann > 0 else None
    score = abs(delta_interest_usd_m) / ocf_ann

    bp_ocf = (THRESHOLDS["critical_delta_over_ocf"] * ocf_ann / floating_principal_usd_m) * 10000
    interest_at_cov = ocf_ann / THRESHOLDS["critical_coverage"]
    bp_cov = ((interest_at_cov - baseline_ann) / floating_principal_usd_m) * 10000
    cands: List[Dict[str, Any]] = []
    if bp_ocf > 0:
        cands.append({"bp": bp_ocf, "trigger": f"ΔI/ann OCF ≥ {THRESHOLDS['critical_delta_over_ocf']*100:.0f}%", "sofr": sofr_pct + bp_ocf / 100})
    if bp_cov > 0:
        cands.append({"bp": bp_cov, "trigger": f"OCF/interest < {THRESHOLDS['critical_coverage']}x", "sofr": sofr_pct + bp_cov / 100})
    cands.sort(key=lambda c: c["bp"])
    crit = cands[0] if cands else None

    level = "normal"
    trigger = None
    if score >= THRESHOLDS["critical_delta_over_ocf"] or (stressed_cov is not None and stressed_cov < THRESHOLDS["critical_coverage"]):
        level = "critical"
        trigger = (
            f"coverage {stressed_cov:.2f}x < {THRESHOLDS['critical_coverage']}x"
            if stressed_cov is not None and stressed_cov < THRESHOLDS["critical_coverage"]
            else f"ΔI/OCF {score*100:.1f}% ≥ {THRESHOLDS['critical_delta_over_ocf']*100:.0f}%"
        )
    elif score >= THRESHOLDS["high_delta_over_ocf"]:
        level = "high"
        trigger = f"ΔI/OCF {score*100:.1f}% ≥ {THRESHOLDS['high_delta_over_ocf']*100:.0f}%"
    elif score >= THRESHOLDS["moderate_delta_over_ocf"]:
        level = "moderate"
        trigger = f"ΔI/OCF {score*100:.1f}% ≥ {THRESHOLDS['moderate_delta_over_ocf']*100:.0f}%"

    intensity = min(1.6, 0.55 + score * 12.5)
    base.update(
        {
            "level": level,
            "intensity": _r(intensity, 3),
            "score_delta_over_ocf": _r(score, 5),
            "baseline_interest_ann_usd_m": _r(baseline_ann, 1),
            "stressed_interest_ann_usd_m": _r(stressed_ann, 1),
            "annualized_ocf_usd_m": _r(ocf_ann, 1),
            "baseline_coverage": _r(baseline_cov, 3),
            "stressed_coverage": _r(stressed_cov, 3) if stressed_cov is not None else None,
            "coverage_change": _r(stressed_cov - baseline_cov, 3) if stressed_cov is not None else None,
            "cash_usd_m": cash,
            "incremental_vs_cash_pct": _r(abs(delta_interest_usd_m) / cash * 100, 2) if cash and cash > 0 else None,
            "critical_sofr_pct": _r(crit["sofr"], 3) if crit else None,
            "critical_shock_bp": _r(crit["bp"], 1) if crit else None,
            "bp_to_critical": _r(crit["bp"] - shock_bp, 1) if crit else None,
            "critical_trigger": crit["trigger"] if crit else None,
            "metric_trigger": trigger,
        }
    )
    return base


def stress_status(level: str, has_direct: bool) -> str:
    if not has_direct:
        return "insufficient"
    return {
        "critical": "stress_critical",
        "high": "stress_high",
        "moderate": "stress_moderate",
        "normal": "stress_normal",
        "insufficient": "insufficient",
    }.get(level, "potential")
