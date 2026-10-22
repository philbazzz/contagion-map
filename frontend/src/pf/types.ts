import type { MarketOverview, Network, RateShockResult, SourceStatus, StressLevel } from "../types";

export type EcosystemId = "semiconductor" | "datacenter_pf";

export type TransmissionClass = "direct_contract" | "sector_demand" | "funding_market" | "unverified";

export interface PfProject {
  id: string;
  name: string;
  name_ko?: string | null;
  name_en?: string | null;
  location: string;
  address?: string | null;
  country: string;
  developer: string | null;
  owner: string | null;
  operator?: string | null;
  spv: string | null;
  tenant: string | null;
  construction_company?: string | null;
  trust_company?: string | null;
  permit_date?: string | null;
  construction_start?: string | null;
  completion_date?: string | null;
  gfa_m2?: number | null;
  construction_stage: string;
  financing_disclosed?: boolean;
  shock_role?: string;
  note?: string;
  sources?: { title?: string; url?: string; filing_id?: string; date?: string }[];
  target_completion: string | null;
  critical_it_load_mw: number | null;
  capacity_note?: string;
  lease_structure?: string | null;
  capex_usd_m?: number | null;
  capex_native_krw_b?: number | null;
  capex_note?: string;
  equity_usd_m?: number | null;
  senior_debt_usd_m?: number | null;
  mezzanine_usd_m?: number | null;
  other_financing_note?: string;
  debt_interest_rate_pct?: number | null;
  debt_rate_type?: "fixed" | "floating" | "unknown";
  debt_rate_note?: string;
  debt_maturity?: string | null;
  amortization?: string | null;
  committed_construction_financing_usd_m?: number | null;
  drawn_usd_m?: number | null;
  covenants?: string | null;
  sponsor_guarantees?: string | null;
  collateral?: string | null;
  recourse?: boolean | null;
  revenue_assumptions?: string | null;
  operating_costs?: string | null;
  baseline_cfads_usd_m?: number | null;
  baseline_debt_service_usd_m?: number | null;
  baseline_dscr?: number | null;
  dscr_status?: SourceStatus | "UNKNOWN";
  gpu_rent_exposure?: string;
  gpu_rent_pass_through_pct?: number | null;
  gpu_rent_note?: string;
  hyperscaler_capex_exposure?: string;
  floating_debt_usd_m?: number | null;
  fixed_debt_usd_m?: number | null;
  floating_debt_note?: string;
  interest_hedge?: string;
  region?: string;
  korean_counterparties?: string[];
  korean_link_class?: TransmissionClass | string;
  source_ids: string[];
  verification_date?: string;
  missing?: string[];
}

export interface PfProjectsFile {
  as_of: string;
  disclaimer: string;
  projects: PfProject[];
}

export type CoreWeaveDistress = "normal" | "moderate" | "severe_liquidity" | "payment_default" | "insolvency";
export type PfExposureFilter = "all" | "confirmed_dc" | "general_pf" | "sector_only";

export interface PfShockForm {
  /** Primary shock A — CoreWeave financial distress ladder. */
  coreweaveDistress: CoreWeaveDistress;
  /** US / USD project financing rate shock (bp) — secondary. */
  rateBp: number;
  /** Separate Korean financing-rate shock (bp). Does not auto-equal US. */
  krRateBp: number;
  /** Linkage: fraction of US rate shock passed to KR — user explicit. */
  krRateLinkPct: number;
  /** GPU rental price change (%). Negative = decline — secondary. */
  gpuRentPct: number;
  /** Primary shock B — Hyperscaler AI CAPEX change (%). Negative = reduction. */
  hyperscalerCapexPct: number;
  /** When true, new project financing / discretionary starts are restricted. */
  restrictNewFinancing: boolean;
  horizonMonths: 12 | 24 | 36;
  /** ASSUMED pass-through of GPU rent shock into GPU-cloud operator EBITDA (0–1). */
  gpuOperatorMarginPassThrough: number;
  /** ASSUMED fraction of future DC demand tied to hyperscaler CAPEX. */
  capexDemandElasticity: number;
  /** Explicit ASSUMED fraction of CoreWeave distress transmitted to KR DC PF funding sentiment (0–1). */
  cwKrFundingPassThrough: number;
  showUsKoreaOnly: boolean;
  showKoreanPfOnly: boolean;
  /** When false (default), historical/repaid/arranger-only edges are hidden from the map. */
  includeHistoricalRelationships: boolean;
  exposureFilter: PfExposureFilter;
}

export interface PfProjectStress {
  project_id: string;
  name: string;
  region: string;
  level: StressLevel;
  intensity: number;
  baseline_dscr: number | null;
  stressed_dscr: number | null;
  dscr_delta: number | null;
  interest_delta_usd_m: number | null;
  debt_service_baseline_usd_m: number | null;
  debt_service_stressed_usd_m: number | null;
  liquidity_gap_usd_m: number | null;
  gpu_revenue_impact: "none" | "assumed_operator" | "lease_protected" | "insufficient";
  capex_demand_impact: "none" | "future_phases" | "construction_funding" | "qualitative";
  quantified: boolean;
  qualitative: boolean;
  reasons: string[];
  missing: string[];
  source_ids: string[];
}

/** Impact category for Korean PF shock results — not a default rating. */
export type PfImpactCategory =
  | "상환·차환 부담 증가"
  | "보증·추가 자금부담 가능"
  | "대출·투자금 손실 가능"
  | "매출·수주 영향"
  | "영향 규모 판단 불가";

export type PfDefaultAssessment =
  | "영향 확인 / 부도위험 판단 자료 부족"
  | "프로젝트 SPC 스트레스 (모회사 자동부도 아님)"
  | "조건부 의무 — 발동 조건 충족 시에만"
  | "정량 스트레스 계산 가능 (부도 판정 아님)"
  | "기준 대비 추가 충격 없음";

export interface PfAffectedCompany {
  company_id: string;
  company_name: string;
  role: string;
  impact_category: PfImpactCategory;
  directness: "direct" | "indirect";
  hop: number;
  projects: Array<{
    project_id: string;
    project_name: string;
    edge_id: string;
    relationship_type: string;
    exposure_label: string;
    amount_note: string;
    amount_krw_eok: number | null;
    amount_type: string | null;
    contingent: boolean;
    obligation_trigger: string;
    evidence_status: string;
    source_url: string | null;
    source_title: string | null;
  }>;
  transmission_path: string;
  baseline_vs_scenario: string;
  default_assessment: PfDefaultAssessment;
  explanation_ko: string;
  assumptions: string[];
  missing: string[];
  evidence_confidence: "VERIFIED" | "INFERRED" | "ASSUMED" | "UNKNOWN";
}

export type PfShockResult = RateShockResult & {
  mode: "RATE_SHOCK";
  pf: {
    rate_bp: number;
    kr_rate_bp: number;
    gpu_rent_pct: number;
    hyperscaler_capex_pct: number;
    restrict_new_financing: boolean;
    coreweave_distress?: string;
    projects: PfProjectStress[];
    measurable_projects: number;
    dscr_deterioration: number;
    liquidity_shortfalls: number;
    korean_verified_exposure: number;
    korean_sector_sensitivity: number;
    us_korea_paths: Array<{
      from: string; to: string; edge_id: string; transmission_class: string; explanation: string;
    }>;
    /** Companies with scenario impact vs unshocked baseline (+0bp / no extra shock). */
    affected_companies: PfAffectedCompany[];
    /** Edge ids carrying the scenario impact (for network highlight). */
    impact_edge_ids: string[];
    assumptions: string[];
    limitations: string[];
  };
};

export interface PfBundle {
  network: Network;
  projects: PfProjectsFile;
  market: MarketOverview | null;
  quotes: import("../types").QuotesOverview | null;
}
