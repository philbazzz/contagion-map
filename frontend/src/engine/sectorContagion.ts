/**
 * Sector-wide financing contagion + CoreWeave default effects on SPVs / lessors.
 *
 * Mechanism B (counterparty) remains in secondaryContagion.ts.
 * This module adds:
 *   - Scenario A helpers for CW default → SPV critical without parent auto-default
 *   - Scenario B sector financing stress from disclosed leverage / funding dependence
 *   - Scenario C combines both without double-counting the same entity's worst band
 *
 * Analytical estimates — NOT confirmed default or bankruptcy.
 */
import type { StressLevel } from "./stressModel";
import { stressStatus } from "./stressModel";

export type CrisisMode = "rate_only" | "cw_default" | "financing" | "combined";
export type FundingAvail = "normal" | "restricted" | "unavailable";

export interface SectorEntityInput {
  cash_usd_m: number | null;
  total_debt_usd_m: number | null;
  floating_debt_usd_m: number | null;
  near_term_debt_usd_m: number | null;
  annual_capex_need_usd_m: number | null;
  funding_dependence: string;
  cw_direct: boolean;
  resilience: string;
  data_quality: string;
  parent_id?: string;
  source_ids: string[];
  notes?: string;
}

export interface SectorStressDataset {
  meta: { as_of: string; note: string; disclaimer: string };
  entities: Record<string, SectorEntityInput>;
}

export interface SectorStressResult {
  entity_id: string;
  level: StressLevel;
  intensity: number;
  mechanism: "cw_default_spv" | "sector_financing" | "combined";
  label_en: string;
  label_ko: string;
  reason: string;
  source_ids: string[];
  parent_id?: string;
  /** Parent is NOT auto-failed when SPV is critical. */
  parent_auto_default: false;
  score_detail: string;
}

const LABEL_EN: Record<string, string> = {
  moderate: "Modeled Sector Funding Stress",
  high: "High Modeled Funding / Liquidity Stress",
  critical: "Critical Modeled Financial Distress",
  insufficient: "Insufficient financial data",
  normal: "Resilient under scenario",
};

const LABEL_KO: Record<string, string> = {
  moderate: "섹터 자금조달 스트레스(시나리오)",
  high: "높은 자금·유동성 스트레스",
  critical: "심각 재무 압박 — 시나리오 추정",
  insufficient: "재무 데이터 부족",
  normal: "시나리오 하 회복력 유지",
};

function intensityFor(level: StressLevel): number {
  switch (level) {
    case "moderate": return 0.85;
    case "high": return 1.15;
    case "critical": return 1.55;
    case "insufficient": return 0.35;
    default: return 0.4;
  }
}

function worse(a: StressLevel, b: StressLevel): StressLevel {
  const rank: Record<string, number> = {
    normal: 0, insufficient: 0.5, moderate: 1, high: 2, critical: 3, not_applicable: -1,
  };
  return (rank[a] || 0) >= (rank[b] || 0) ? a : b;
}

/** SPV / single-tenant vehicles under CoreWeave default assumption. */
export function computeCwDefaultSpvStress(
  dataset: SectorStressDataset,
  present: Set<string>,
  cwDefaultActive: boolean,
): SectorStressResult[] {
  if (!cwDefaultActive) return [];
  const out: SectorStressResult[] = [];
  for (const [id, inp] of Object.entries(dataset.entities)) {
    if (!present.has(id)) continue;
    if (!inp.cw_direct || inp.resilience !== "spv_single_tenant") continue;
    const inferred = inp.data_quality === "inferred";
    out.push({
      entity_id: id,
      level: "critical",
      intensity: intensityFor("critical"),
      mechanism: "cw_default_spv",
      label_en: inferred
        ? "Secondary Critical Financial Distress (SPV · inferred structure)"
        : "Secondary Critical Financial Distress (Project SPV)",
      label_ko: "2차 심각 재무 압박 — 프로젝트 SPV (시나리오)",
      reason:
        "CoreWeave 계약 불이행 가정 시 단일 임차 현금흐름이 프로젝트 부채 상환 원천인 SPV. " +
        "모회사 notes 미보증이므로 모회사 자동 파산으로 보지 않음. 확정 부도 판정 아님.",
      source_ids: inp.source_ids,
      parent_id: inp.parent_id,
      parent_auto_default: false,
      score_detail: "CW default → SPV debt service cash-flow interruption (scenario)",
    });
  }
  return out;
}

/**
 * Sector financing stress from leverage, cash runway vs capex, near-term debt,
 * and optional floating-rate cost increase. Does not invent floating share —
 * uses disclosed floating_debt_usd_m only (often 0).
 */
export function computeSectorFinancingStress(
  dataset: SectorStressDataset,
  present: Set<string>,
  params: {
    shockBp: number;
    refi: FundingAvail;
    projectFinancing: FundingAvail;
    horizonMonths: 12 | 24;
  },
): SectorStressResult[] {
  const out: SectorStressResult[] = [];
  const years = params.horizonMonths / 12;

  for (const [id, inp] of Object.entries(dataset.entities)) {
    if (!present.has(id)) continue;
    if (inp.resilience === "spv_single_tenant") continue; // handled by CW default path
    if (inp.data_quality === "insufficient" || inp.cash_usd_m == null || inp.total_debt_usd_m == null) {
      out.push({
        entity_id: id,
        level: "insufficient",
        intensity: intensityFor("insufficient"),
        mechanism: "sector_financing",
        label_en: LABEL_EN.insufficient,
        label_ko: LABEL_KO.insufficient,
        reason: "공개 연결 재무로 유동성·부채 서비스 스트레스를 산정할 수 없음 (비상장·미공시).",
        source_ids: inp.source_ids,
        parent_auto_default: false,
        score_detail: "insufficient_data",
      });
      continue;
    }

    const cash = inp.cash_usd_m;
    const debt = inp.total_debt_usd_m;
    const floating = inp.floating_debt_usd_m || 0;
    const near = inp.near_term_debt_usd_m || 0;
    const capex = inp.annual_capex_need_usd_m || 0;

    const deltaInterest = floating > 0 && params.shockBp !== 0
      ? floating * params.shockBp / 10000
      : 0;

    // Funding gap if new project financing is restricted/unavailable
    let fundingGap = 0;
    if (params.projectFinancing === "unavailable") {
      fundingGap = Math.max(0, capex * years - cash * 0.35);
    } else if (params.projectFinancing === "restricted") {
      fundingGap = Math.max(0, capex * years * 0.5 - cash * 0.5);
    }

    let refiPressure = 0;
    if (params.refi === "unavailable" && near > 0) {
      refiPressure = near;
    } else if (params.refi === "restricted" && near > 0) {
      refiPressure = near * 0.5;
    }

    // Incremental cost of refinancing at higher spreads when refi is needed
    const refiCostBump = (params.refi !== "normal" && near > 0 && params.shockBp > 0)
      ? near * params.shockBp / 10000
      : 0;

    const outflow = deltaInterest * years + fundingGap + refiPressure + refiCostBump * years;
    const leverage = debt / Math.max(cash, 1);
    const coverage = cash > 0 ? (cash - outflow) / cash : -1;

    let level: StressLevel = "normal";
    let detail = `lev=${leverage.toFixed(2)} outflow=${outflow.toFixed(0)} coverage=${coverage.toFixed(2)}`;

    // Resilient profiles need stronger shocks to move
    const resilient = inp.resilience === "low_leverage" || inp.resilience === "ig_project_google_backstop";

    if (coverage < 0 || (params.refi === "unavailable" && near > cash)) {
      level = resilient && coverage > -0.15 ? "high" : "critical";
      detail += " · modeled liquidity shortfall";
    } else if (coverage < 0.25 || (params.projectFinancing === "unavailable" && inp.funding_dependence === "high" && params.shockBp >= 500)) {
      level = resilient ? "moderate" : "high";
      detail += " · thin liquidity / funding dependence";
    } else if (
      (params.shockBp >= 300 && inp.funding_dependence === "high") ||
      (params.projectFinancing !== "normal" && leverage > 3) ||
      (params.refi !== "normal" && near > cash * 0.3)
    ) {
      level = resilient ? "normal" : "moderate";
      detail += " · elevated funding / refi pressure";
    } else if (params.shockBp >= 500 && leverage > 4 && !resilient) {
      level = "moderate";
    }

    // Hut 8 / Soluna stay normal or mild unless financing truly unavailable for near-term
    if (inp.resilience === "ig_project_google_backstop" && params.projectFinancing !== "unavailable") {
      if (level === "critical") level = "high";
      if (level === "high" && params.shockBp < 500) level = "moderate";
    }
    if (inp.resilience === "low_leverage" && level !== "insufficient") {
      if (params.projectFinancing === "normal" && params.refi === "normal") level = "normal";
      else if (level === "critical") level = "moderate";
    }

    if (level === "normal") continue; // don't clutter map with green noise

    out.push({
      entity_id: id,
      level,
      intensity: intensityFor(level),
      mechanism: "sector_financing",
      label_en: LABEL_EN[level] || "Modeled Sector Funding Stress",
      label_ko: LABEL_KO[level] || "섹터 자금조달 스트레스",
      reason:
        `섹터 자금조달 시나리오(+${params.shockBp}bp · refi=${params.refi} · project=${params.projectFinancing} · ${params.horizonMonths}m). ` +
        `현금 $${cash.toFixed(0)}M · 부채 $${debt.toFixed(0)}M. ${detail}. 확정 부도 아님.`,
      source_ids: inp.source_ids,
      parent_auto_default: false,
      score_detail: detail,
    });
  }
  return out;
}

export function mergeStressByEntity(
  ...lists: SectorStressResult[][]
): SectorStressResult[] {
  const map = new Map<string, SectorStressResult>();
  for (const list of lists) {
    for (const s of list) {
      const prev = map.get(s.entity_id);
      if (!prev) {
        map.set(s.entity_id, s);
        continue;
      }
      const level = worse(prev.level, s.level);
      map.set(s.entity_id, {
        ...s,
        level,
        intensity: intensityFor(level),
        mechanism: "combined",
        label_en: level === "critical"
          ? "Critical Modeled Financial Distress (Combined)"
          : LABEL_EN[level] || s.label_en,
        label_ko: level === "critical"
          ? "심각 재무 압박 — 복합 시나리오"
          : LABEL_KO[level] || s.label_ko,
        reason: `${prev.reason} | ${s.reason}`,
        score_detail: `${prev.score_detail} + ${s.score_detail}`,
      });
    }
  }
  return [...map.values()];
}

export function sectorNodeStatus(level: StressLevel): string {
  if (level === "insufficient") return "insufficient";
  if (level === "normal") return "stress_normal";
  return stressStatus(level, true);
}

/** Empty dataset fallback when sector_stress.json not loaded into Network. */
export const EMPTY_SECTOR: SectorStressDataset = {
  meta: { as_of: "", note: "", disclaimer: "" },
  entities: {},
};
