/**
 * Secondary (counterparty) stress when CoreWeave enters modeled distress.
 *
 * Mechanism B — separate from direct SOFR floating interest sensitivity:
 * lessors with disclosed CoreWeave lease concentration may face modeled
 * lease-cash-flow / utilization stress if CW is severely stressed.
 *
 * Analytical scenario estimates — NOT confirmed default or bankruptcy.
 */
import type { StressLevel } from "./stressModel";
import { stressStatus } from "./stressModel";

export type ConcentrationTier = "sole_segment" | "material_backlog" | "named_campus_tenant";

export interface LessorExposure {
  entity_id: string;
  name: string;
  tier: ConcentrationTier;
  /** Disclosed contract / backlog value (USD M), landlord basis. */
  contract_value_usd_m: number | null;
  concentration_note: string;
  source_ids: string[];
  edge_prefer: "facility";
}

/** Counterparties with VERIFIED CoreWeave lease concentration in project data / 10-K. */
export const CW_LESSOR_EXPOSURES: LessorExposure[] = [
  {
    entity_id: "core_scientific",
    name: "Core Scientific",
    tier: "sole_segment",
    contract_value_usd_m: 10200,
    concentration_note:
      "Disclosed CoreWeave leases ~590 MW / $10.2B landlord contract revenue (12y) — primary single-tenant AI colocation concentration.",
    source_ids: ["S_CORZ"],
    edge_prefer: "facility",
  },
  {
    entity_id: "applied_digital",
    name: "Applied Digital",
    tier: "material_backlog",
    contract_value_usd_m: 7000,
    concentration_note:
      "IR: Ellendale ND ~250 MW AI lease to CoreWeave; ~$7B expected landlord revenue over ~15 years (material contracted backlog).",
    source_ids: ["S_APLD"],
    edge_prefer: "facility",
  },
  {
    entity_id: "galaxy_digital",
    name: "Galaxy Digital",
    tier: "named_campus_tenant",
    contract_value_usd_m: null,
    concentration_note:
      "10-K / IR: Helios campus 15-year leases to CoreWeave for 526 MW critical IT load (Phases I–III); expected >$1B average annual revenue; Data Centers segment anchored by CW.",
    source_ids: ["S_GLXY_10K25", "S_GLXY_HELIOS"],
    edge_prefer: "facility",
  },
];

export interface SecondaryStress {
  entity_id: string;
  level: StressLevel;
  intensity: number;
  mechanism: "secondary_contagion";
  label_en: string;
  label_ko: string;
  reason: string;
  source_ids: string[];
  origin_level: StressLevel;
  shock_bp: number;
}

const LABEL_EN: Record<string, string> = {
  moderate: "Modeled Counterparty Stress",
  high: "Secondary High Financial Stress",
  critical: "Secondary Critical Financial Distress",
};

const LABEL_KO: Record<string, string> = {
  moderate: "거래상대방 스트레스(시나리오)",
  high: "2차 높은 재무 스트레스",
  critical: "2차 심각 재무 압박 — 시나리오 추정",
};

function mapTier(
  tier: ConcentrationTier,
  origin: StressLevel,
  shockBp: number,
): StressLevel | null {
  if (origin === "normal" || origin === "insufficient" || origin === "not_applicable") return null;

  if (tier === "sole_segment") {
    if (origin === "moderate") return "moderate";
    if (origin === "high") return "high";
    if (origin === "critical") return "critical";
  }

  if (tier === "material_backlog" || tier === "named_campus_tenant") {
    if (origin === "moderate") return null; // watch only — not enough for planet stress
    if (origin === "high") return "moderate";
    if (origin === "critical") {
      // Combined: CW critical + extreme rate shock escalates campus tenants
      return shockBp >= 500 ? "critical" : "high";
    }
  }
  return null;
}

function intensityFor(level: StressLevel): number {
  switch (level) {
    case "moderate": return 0.9;
    case "high": return 1.2;
    case "critical": return 1.55;
    default: return 0.45;
  }
}

export function computeSecondaryStress(
  originLevel: StressLevel | null | undefined,
  shockBp: number,
  presentEntityIds: Set<string>,
): SecondaryStress[] {
  if (!originLevel) return [];
  const out: SecondaryStress[] = [];
  for (const exp of CW_LESSOR_EXPOSURES) {
    if (!presentEntityIds.has(exp.entity_id)) continue;
    const level = mapTier(exp.tier, originLevel, shockBp);
    if (!level) continue;
    out.push({
      entity_id: exp.entity_id,
      level,
      intensity: intensityFor(level),
      mechanism: "secondary_contagion",
      label_en: LABEL_EN[level] || "Modeled Counterparty Stress",
      label_ko: LABEL_KO[level] || "거래상대방 스트레스",
      reason:
        `CoreWeave ${originLevel} 시나리오 + ${exp.concentration_note} ` +
        `직접 SOFR 이자 민감도와 별개의 2차(임차료·가동) 경로. 확정 부도·파산이 아님.`,
      source_ids: exp.source_ids,
      origin_level: originLevel,
      shock_bp: shockBp,
    });
  }
  return out;
}

export function secondaryNodeStatus(level: StressLevel): string {
  return stressStatus(level, true);
}
