/**
 * Evidence-based interest-rate financial stress model for Contagion Shock tab.
 *
 * Scope: CoreWeave instruments + 10-Q metrics in network.financials only.
 * Thresholds are ANALYTICAL scenario estimates, not disclosed financial covenants
 * and not predictions of bankruptcy or default.
 *
 * Primary continuous stress score (drives glow intensity):
 *   score = Δ annual interest / annualized OCF   (0 → unbounded)
 *
 * Discrete bands (documented cutoffs on that score + coverage floor):
 *   normal    : score < 0.02
 *   moderate  : score ≥ 0.02
 *   high      : score ≥ 0.05
 *   critical  : score ≥ 0.08  OR  stressed OCF/interest < 2.5x
 *
 * Critical SOFR = baseline SOFR + bp needed to hit the nearer of:
 *   (A) ΔI / ann_OCF = 8%
 *   (B) ann_OCF / stressed_interest = 2.5
 */
import type { Financials } from "../types";

export type StressLevel = "normal" | "moderate" | "high" | "critical" | "insufficient" | "not_applicable";

export const STRESS_LABEL: Record<StressLevel, string> = {
  normal: "Normal",
  moderate: "Moderate Financial Stress",
  high: "High Financial Stress",
  critical: "Critical Financial Distress — Scenario Estimate",
  insufficient: "Insufficient financial data",
  not_applicable: "Not applicable to this benchmark",
};

export const STRESS_LABEL_KO: Record<StressLevel, string> = {
  normal: "정상",
  moderate: "중간 재무 스트레스",
  high: "높은 재무 스트레스",
  critical: "심각 재무 압박 — 시나리오 추정",
  insufficient: "재무 데이터 부족",
  not_applicable: "이 벤치마크에 해당 없음",
};

/** Analytical cutoffs — not contractual covenants. */
export const THRESHOLDS = {
  moderate_delta_over_ocf: 0.02,
  high_delta_over_ocf: 0.05,
  critical_delta_over_ocf: 0.08,
  critical_coverage: 2.5,
  horizon: "12 months (annualized from H1 10-Q metrics)",
  definition: "Analytical stress bands using disclosed SOFR floating principal and H1 OCF/interest; not a bankruptcy forecast.",
} as const;

export interface OriginStress {
  entity: string;
  level: StressLevel;
  /** Continuous 0–1+ visual intensity (clamped display 0–1.6). */
  intensity: number;
  /** Δ annual interest / annualized OCF */
  score_delta_over_ocf: number | null;
  baseline_interest_ann_usd_m: number | null;
  stressed_interest_ann_usd_m: number | null;
  annualized_ocf_usd_m: number | null;
  baseline_coverage: number | null;
  stressed_coverage: number | null;
  coverage_change: number | null;
  delta_interest_usd_m: number | null;
  floating_principal_usd_m: number | null;
  cash_usd_m: number | null;
  incremental_vs_cash_pct: number | null;
  baseline_sofr_pct: number;
  stressed_sofr_pct: number;
  shock_bp: number;
  critical_sofr_pct: number | null;
  critical_shock_bp: number | null;
  bp_to_critical: number | null;
  critical_trigger: string | null;
  threshold_kind: "analytical";
  assumptions: string[];
  limitations: string[];
  source_ids: string[];
  metric_trigger: string | null;
}

function metric(fin: Financials, id: string): number | null {
  const m = fin.metrics.find((x) => x.id === id);
  return m?.value_usd_m ?? null;
}

function r(x: number, nd = 4): number {
  const k = 10 ** nd;
  return Math.floor(x * k + 0.5) / k;
}

export function computeOriginStress(
  fin: Financials,
  shockBp: number,
  deltaInterestUsdM: number | null,
  floatingPrincipalUsdM: number,
  sofrPct: number,
  hasComputed: boolean,
): OriginStress {
  const sourceIds = [fin.filing, ...(fin.metrics[0]?.source_ids || [])].filter(Boolean) as string[];
  const assumptions = [
    "H1 (6개월) 이자·OCF를 ×2 하여 연환산 (계절성·비반복 항목 미조정)",
    "이자 민감도는 공시된 SOFR 연동 변동금리 잔액에만 적용",
    "고정금리·헤지·미공시 잔액은 제외",
    "임계값은 분석용 시나리오 밴드이며 공시 재무약정이 아님",
  ];
  const limitations = [
    "이자보상배율 약정(covenant) 임계값은 본 데이터셋에 없음",
    "부도·파산 예측 모델이 아님",
    "간접 거래처 손실은 산정하지 않음",
  ];

  const base: OriginStress = {
    entity: "coreweave",
    level: "insufficient",
    intensity: 0.35,
    score_delta_over_ocf: null,
    baseline_interest_ann_usd_m: null,
    stressed_interest_ann_usd_m: null,
    annualized_ocf_usd_m: null,
    baseline_coverage: null,
    stressed_coverage: null,
    coverage_change: null,
    delta_interest_usd_m: deltaInterestUsdM,
    floating_principal_usd_m: floatingPrincipalUsdM || null,
    cash_usd_m: metric(fin, "cash"),
    incremental_vs_cash_pct: null,
    baseline_sofr_pct: sofrPct,
    stressed_sofr_pct: r(sofrPct + shockBp / 100, 4),
    shock_bp: shockBp,
    critical_sofr_pct: null,
    critical_shock_bp: null,
    bp_to_critical: null,
    critical_trigger: null,
    threshold_kind: "analytical",
    assumptions,
    limitations,
    source_ids: sourceIds,
    metric_trigger: null,
  };

  if (!hasComputed || floatingPrincipalUsdM <= 0 || deltaInterestUsdM === null) {
    return { ...base, level: "insufficient", intensity: 0.35 };
  }

  const interest6 = metric(fin, "interest_expense_6m");
  const ocf6 = metric(fin, "ocf_6m");
  const cash = metric(fin, "cash");

  if (interest6 === null || ocf6 === null || ocf6 <= 0) {
    return { ...base, level: "insufficient", intensity: 0.4, limitations: [...limitations, "H1 이자 또는 OCF 공시 부족"] };
  }

  const baselineAnn = interest6 * 2;
  const ocfAnn = ocf6 * 2;
  const stressedAnn = baselineAnn + deltaInterestUsdM;
  const baselineCov = ocfAnn / baselineAnn;
  const stressedCov = stressedAnn > 0 ? ocfAnn / stressedAnn : null;
  const score = Math.abs(deltaInterestUsdM) / ocfAnn;
  const vsCash = cash && cash > 0 ? (Math.abs(deltaInterestUsdM) / cash) * 100 : null;

  // Critical bp candidates (positive shock direction)
  const bpForOcfBand = (THRESHOLDS.critical_delta_over_ocf * ocfAnn / floatingPrincipalUsdM) * 10000;
  const interestAtCov = ocfAnn / THRESHOLDS.critical_coverage;
  const bpForCoverage = ((interestAtCov - baselineAnn) / floatingPrincipalUsdM) * 10000;
  const criticalCandidates = [
    { bp: bpForOcfBand, trigger: `Δ이자 / 연환산 OCF ≥ ${(THRESHOLDS.critical_delta_over_ocf * 100).toFixed(0)}%`, sofr: sofrPct + bpForOcfBand / 100 },
    { bp: bpForCoverage, trigger: `연환산 OCF / 스트레스 이자 < ${THRESHOLDS.critical_coverage}x`, sofr: sofrPct + bpForCoverage / 100 },
  ].filter((c) => c.bp > 0);
  criticalCandidates.sort((a, b) => a.bp - b.bp);
  const crit = criticalCandidates[0] || null;

  let level: StressLevel = "normal";
  let trigger: string | null = null;
  if (score >= THRESHOLDS.critical_delta_over_ocf || (stressedCov !== null && stressedCov < THRESHOLDS.critical_coverage)) {
    level = "critical";
    trigger = stressedCov !== null && stressedCov < THRESHOLDS.critical_coverage
      ? `커버리지 ${r(stressedCov, 2)}x < ${THRESHOLDS.critical_coverage}x`
      : `Δ이자/OCF ${(score * 100).toFixed(1)}% ≥ ${(THRESHOLDS.critical_delta_over_ocf * 100).toFixed(0)}%`;
  } else if (score >= THRESHOLDS.high_delta_over_ocf) {
    level = "high";
    trigger = `Δ이자/OCF ${(score * 100).toFixed(1)}% ≥ ${(THRESHOLDS.high_delta_over_ocf * 100).toFixed(0)}%`;
  } else if (score >= THRESHOLDS.moderate_delta_over_ocf) {
    level = "moderate";
    trigger = `Δ이자/OCF ${(score * 100).toFixed(1)}% ≥ ${(THRESHOLDS.moderate_delta_over_ocf * 100).toFixed(0)}%`;
  }

  // Intensity scales continuously with score so +100bp ≠ +300bp visually inside a band.
  // Map score 0→0.55, 0.02→0.85, 0.05→1.15, 0.08→1.45, beyond → up to 1.6
  const intensity = Math.min(1.6, 0.55 + score * 12.5);

  return {
    ...base,
    level,
    intensity: r(intensity, 3),
    score_delta_over_ocf: r(score, 5),
    baseline_interest_ann_usd_m: r(baselineAnn, 1),
    stressed_interest_ann_usd_m: r(stressedAnn, 1),
    annualized_ocf_usd_m: r(ocfAnn, 1),
    baseline_coverage: r(baselineCov, 3),
    stressed_coverage: stressedCov !== null ? r(stressedCov, 3) : null,
    coverage_change: stressedCov !== null ? r(stressedCov - baselineCov, 3) : null,
    cash_usd_m: cash,
    incremental_vs_cash_pct: vsCash !== null ? r(vsCash, 2) : null,
    critical_sofr_pct: crit ? r(crit.sofr, 3) : null,
    critical_shock_bp: crit ? r(crit.bp, 1) : null,
    bp_to_critical: crit ? r(crit.bp - shockBp, 1) : null,
    critical_trigger: crit?.trigger ?? null,
    metric_trigger: trigger,
  };
}

/** Map stress level → NodeVisual status token used by Universe. */
export function stressStatus(level: StressLevel, hasDirect: boolean): string {
  if (!hasDirect) return "insufficient";
  switch (level) {
    case "critical": return "stress_critical";
    case "high": return "stress_high";
    case "moderate": return "stress_moderate";
    case "normal": return "stress_normal";
    case "insufficient": return "insufficient";
    default: return "potential";
  }
}

export function compareStress(a: OriginStress | null, b: OriginStress | null): {
  delta_interest_usd_m: number | null;
  level_from: StressLevel | null;
  level_to: StressLevel | null;
  crossed_critical: boolean;
  summary_ko: string;
} {
  if (!a || !b) {
    return { delta_interest_usd_m: null, level_from: null, level_to: null, crossed_critical: false, summary_ko: "비교할 시나리오 결과가 없습니다." };
  }
  const dInt = (b.delta_interest_usd_m ?? 0) - (a.delta_interest_usd_m ?? 0);
  const crossed = a.level !== "critical" && b.level === "critical";
  const fmt = (x: number) => {
    const a = Math.abs(x);
    const s = x < 0 ? "−" : x > 0 ? "+" : "";
    return s + (a >= 1000 ? `$${(a / 1000).toFixed(2)}B` : `$${a.toFixed(0)}M`);
  };
  const summary_ko = a.shock_bp === 0
    ? `현재 기준(+0bp) 대비 선택 시나리오(${b.shock_bp >= 0 ? "+" : ""}${b.shock_bp}bp)는 추가 이자 ${fmt(dInt)}/년, 스트레스 ${STRESS_LABEL_KO[a.level]} → ${STRESS_LABEL_KO[b.level]}${crossed ? " (심각 임계 교차)" : ""}입니다.`
    : `${a.shock_bp >= 0 ? "+" : ""}${a.shock_bp}bp 대비 ${b.shock_bp >= 0 ? "+" : ""}${b.shock_bp}bp 시나리오는 추가 이자 ${fmt(dInt)}/년, 스트레스 ${STRESS_LABEL_KO[a.level]} → ${STRESS_LABEL_KO[b.level]}${crossed ? " (심각 임계 교차)" : ""}입니다.`;
  return {
    delta_interest_usd_m: r(dInt, 2),
    level_from: a.level,
    level_to: b.level,
    crossed_critical: crossed,
    summary_ko,
  };
}
