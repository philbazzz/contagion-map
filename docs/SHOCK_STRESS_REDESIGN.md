# Shock Tab Stress Redesign (2026-10-20)

## Root cause (why +100bp ≈ +300bp visually)

Planet glow/color keyed only on discrete status `shock_origin`. Interest dollars scaled with bp, but `NodeVisual.intensity` was never passed from App → Universe. Fixed by continuous intensity + stress bands.

## HY OAS removed

Removed from Shock benchmarks, Market strip/overview/API refresh allowlist, static `market.json` placeholder, and docs-facing collectors path. Optional `collect_hy_oas` may remain in collectors for historical tests/utilities but is not wired into the app.

## Financial stress model (CoreWeave / SOFR floating)

Score = Δ annual interest / annualized OCF (H1 × 2).

| Band | Rule (analytical — not a covenant) |
|------|-------------------------------------|
| normal | score < 2% |
| moderate | score ≥ 2% |
| high | score ≥ 5% |
| critical | score ≥ 8% **or** stressed OCF/interest < 2.5x |

Critical SOFR = nearer of (score=8% bp, coverage=2.5x bp) + baseline SOFR.

**Not** a bankruptcy or PD model. UI labels critical as “Critical Financial Distress — Scenario Estimate”.

## Visual states

| Status | Look |
|--------|------|
| `stress_normal` | Intact, mild orange |
| `stress_moderate` | Color shift, faint cracks |
| `stress_high` | Visible cracks, vibration, sparks |
| `stress_critical` | Major cracks + one-shot shatter fragments (reversible) |
| `insufficient` | Neutral intact |

Intensity scales continuously with score so +100bp and +300bp differ even inside one band.

## Observed CoreWeave bands (SOFR ≈ 3.88%, floating ~$13.6B)

Run `simulate_rate_shock` locally for exact numbers; typically +100bp stays below high, +300bp enters high, critical near ~+430bp (8% of ann. OCF).

## Multi-hop contagion (orders 1…N)

Prior limitation: contagion was a **hardcoded CW-lessor list + SPV list** (effectively depth ≤ 2), not a graph walk. Replay stages were thematic, not hop-ordered.

Now `multiHopContagion.ts` runs a deterministic BFS with transmission rules:

| Rule | Edge | Effect |
|------|------|--------|
| Lease cashflow | LESSOR / facility (tenant→landlord) | Quantified stress via concentration tier |
| Parent→SPV | PARENT_SPV | Quantified SPV stress (parent not auto-default) |
| Project equity | INVESTOR | Qualitative moderate max (diversified AM) |
| Initial purchaser | INITIAL_PURCHASER / ARRANGER | Pathway only — arranger ≠ loss |
| Generic lender/customer | — | **No** hop event (reachability ≠ loss) |

Replay stages: Direct → 1st-order → 2nd-order → 3rd-order+ → Sector funding → Summary.

Verified order-3 example: CW → CORZ → Finance I → MS/JPM (pathway).

## Crisis modes (Shock tab)

| Mode | Meaning |
|------|---------|
| `rate_only` | CoreWeave SOFR floating interest + secondary lessors if CW stressed |
| `cw_default` (A) | Assume CW contractual default → lessors + single-tenant SPVs (parent ≠ auto-default) |
| `financing` (B) | Sector funding stress only (refi / project financing / +bp) — no lessor mapping from CW |
| `combined` (C) | A + B together |

Controls: refinancing availability, new project financing, 12/24-month horizon. No HY OAS.

## Secondary contagion (Mechanism B)

Separate from direct SOFR interest (Mechanism A). When CoreWeave enters **moderate+** modeled stress, disclosed CW lessors may receive secondary stress based on concentration tier:

| Entity | Tier | Evidence |
|--------|------|----------|
| Core Scientific (CORZ) | `sole_segment` | ~590 MW / $10.2B landlord contract |
| Applied Digital (APLD) | `material_backlog` | ~250 MW / ~$7B expected landlord revenue |
| Galaxy Digital (GLXY) | `named_campus_tenant` | Helios 526 MW critical IT; >$1B avg annual revenue expected |

Mapping (not mechanical default of every neighbor):
- sole: tracks CW band (moderate→critical)
- material/campus: CW high → moderate; CW critical → high; CW critical **and** shock ≥ +500bp → secondary critical

Labels: “Modeled Counterparty Stress” / “Secondary Critical Financial Distress” — **not** confirmed default.

## Replay

Play advances **all** Shock rounds (rate_shock was previously skipped). Replay from last stage resets `fx_gen`, stage→0, and re-runs propagation so shatter can re-fire.

## Files

- `frontend/src/engine/stressModel.ts`, `rateShock.ts`, `secondaryContagion.ts`
- `frontend/src/universe/Universe.ts` (cracks/shatter + fx_gen)
- `frontend/src/App.tsx` (rate_shock playback)
- `frontend/src/components/ScenarioBuilder.tsx` (compare / What Changed)
- `backend/app/engine/stress_model.py`, `rate_shock.py`, `secondary_contagion.py`
- Market HY removal: `overview.py`, `Market.tsx`, `prepare-static.mjs`, tests
