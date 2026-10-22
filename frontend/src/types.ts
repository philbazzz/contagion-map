export type SourceStatus = "VERIFIED" | "INFERRED" | "ASSUMED" | "UNKNOWN";
export type Channel = "financial" | "equity" | "supply_chain" | "customer" | "facility" | "contract";

export interface NetNode {
  id: string;
  name: string;
  name_ko?: string | null;
  /** English alias when `name` / `name_ko` is Hangul (KR entities). */
  name_en?: string | null;
  region?: string | null;
  country?: string | null;
  group: string;
  sector: string;
  entity_type: string;
  role: string;
  description: string;
  listed: boolean;
  ticker: string | null;
  exchange: string | null;
  quote_currency: string | null;
  listing_note: string | null;
  display_size: number;
  source_status: SourceStatus;
  source_ids: string[];
  key_drivers: string[];
  /** v0.3 field kept for the renderer's DEMO ring; always false since v0.4 */
  is_demo?: boolean;
}

export interface NetEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  impact_channel: Channel;
  label: string;
  impact_label: string;
  source_status: SourceStatus;
  source_ids: string[];
  contract_ids: string[];
  commercial_ids: string[];
  amount_usd_m: number | null;
  amount_note: string;
  roles: string[];
  explanation: string;
}

export interface Participant { entity: string; roles: string[]; status: SourceStatus }

export interface Instrument {
  id: string;
  name: string;
  kind: "term_loan" | "revolver" | "senior_notes" | "convertible" | "vendor_financing" | "other_loan";
  currency: string;
  principal_usd_m: number | null;
  principal_as_of: string;
  principal_note: string;
  commitment_usd_m: number | null;
  effective_rate_pct: number | null;
  effective_rate_status: SourceStatus;
  rate_type: "fixed" | "floating" | "unknown";
  coupon_pct: number | null;
  spread_pct: number | null;
  base_rate: string | null;
  floor_pct: number | null;
  rate_status: SourceStatus;
  rate_note: string;
  maturity: string | null;
  maturity_status: SourceStatus;
  borrower: string | null;
  borrower_status: SourceStatus;
  recourse: boolean | null;
  amortization: string;
  collateral: string;
  customer: string | null;
  signed: string | null;
  participants: Participant[];
  source_ids: string[];
}

export interface CommercialContract {
  id: string; counterparty: string; kind: "customer" | "backstop" | "lease" | "supply"; title: string;
  signed: string | null; value_usd_m: number | null; value_basis: string; term_end: string | null; term_note: string;
  history: string[]; detail: string; remaining_note: string; status: SourceStatus; source_ids: string[];
}

export interface Commercial {
  rpo_usd_m: number; rpo_as_of: string; rpo_buckets: { label: string; pct: number }[]; rpo_source_id: string;
  post_q2_commitments_usd_m: number; post_q2_note: string; post_q2_source_id: string;
  contracted_power_gw: number; active_power_gw: number; power_note: string; power_source_ids: string[];
  concentration: { customer: string; q2_3m_pct: number; h1_6m_pct: number | null }[]; concentration_note: string; concentration_source_id: string;
  lease_operating_undiscounted_usd_m: number; lease_finance_undiscounted_usd_m: number; lease_not_commenced_usd_m: number; lease_note: string; lease_source_id: string;
}

export interface Financials {
  company: string;
  as_of: string;
  filing: string;
  currency_unit: string;
  notes: string[];
  totals: { principal_usd_m: number; recourse_net_usd_m: number; nonrecourse_net_usd_m: number; source_ids: string[] };
  maturities: { period: string; usd_m: number }[];
  metrics: { id: string; label: string; value_usd_m: number; period: string; source_ids: string[] }[];
  instruments: Instrument[];
  market_inputs: { sofr_pct: number; sofr_date: string; sofr_source_id: string };
  reference: { nvidia_revenue_fy2026_usd_m: number; nvidia_dc_revenue_fy2026_usd_m: number; nvidia_period: string; nvidia_source_id: string };
  commercial: Commercial;
}

export interface Source { id: string; title: string; publisher: string; date: string; url: string; used_for: string; kind: string }

export interface ProfileMetric {
  id: string; label: string; value_usd_m?: number | null; value_native?: number | null;
  /** Reporting currency for this metric (USD / KRW / TWD). */
  currency?: string; display?: string; period?: string;
  status: SourceStatus; source_ids: string[]; note?: string;
}

export interface CompanyProfile {
  as_of?: string; period_label?: string; currency?: string; unit?: string;
  /** Primary financial reporting currency (distinct from quote/ADR trading currency). */
  reporting_currency?: string;
  listing_currency?: string;
  overview?: string;
  metrics?: ProfileMetric[]; financing_notes?: string[]; risk_factors?: string[];
  missing?: string[]; source_ids?: string[];
}

export interface Network {
  meta: { name: string; as_of: string; currency_unit: string; disclaimer: string; status_legend: Record<string, string>; next_maturity_id?: string | null };
  sources: Source[];
  nodes: NetNode[];
  edges: NetEdge[];
  financials: Financials;
  contracts: CommercialContract[];
  profiles?: Record<string, CompanyProfile>;
}

export type StressLevel = "normal" | "moderate" | "high" | "critical" | "insufficient" | "not_applicable";

export interface NodeVisual {
  status: string;
  intensity?: number;
  label?: string;
  /** Evidence-based financial stress band (Shock tab). */
  stress?: StressLevel;
  /** Increments on replay / new shock so shatter FX can re-trigger. */
  fx_gen?: number;
}

export interface PathResult { nodes: string[]; edges: string[]; hops: number; statuses: string[] }
export interface RelationSummary { kind: "origin" | "direct" | "indirect" | "unconfirmed"; path: PathResult | null; direct_edges: string[] }

export interface NetworkStats {
  origin: string; entities: number; direct: number; indirect: number; unconnected: number;
  financing_contracts: number; industrial_relationships: number; financial_relationships: number; note: string;
}

export type Category = "computed" | "assumed" | "relationship_only" | "unconfirmed";

export interface NodeState {
  status: string;
  label: string;
  category: Category | string;
  intensity?: number;
  stress?: StressLevel;
}

export interface RefiRound {
  round: number; stage: number; title: string; title_ko: string; lines: string[]; active_edges: string[];
  node_states: Record<string, NodeState>;
}

export interface RefiCore {
  new_rate_pct: number; existing_rate_pct: number; rate_change_bp: number; amount_usd_m: number; refinanced_usd_m: number;
  not_refinanced_usd_m: number; annual_interest_existing_usd_m: number; annual_interest_new_usd_m: number;
  annual_interest_delta_usd_m: number; one_off_fee_usd_m: number; funding_need_usd_m: number; delta_6m_usd_m: number;
  delta_6m_vs_ocf_6m_pct: number | null; delta_6m_vs_interest_6m_pct: number | null;
}

export interface ScheduleRow {
  year: number; months: number; interest_existing_usd_m: number; interest_new_usd_m: number; interest_delta_usd_m: number;
  fee_usd_m: number; principal_usd_m: number; debt_service_new_usd_m: number;
}

export interface AssessValue { label: string; usd_m?: number; pct?: number | null; status: string; round: number }
export interface Assessment { category: Category; relation: RelationSummary; values: AssessValue[]; reason: string; needed: string | null }

export interface RefiParams {
  instrument_id: string; new_rate_pct: number; amount_usd_m?: number | null; basis?: "stated" | "effective";
  refi_date?: string | null; success_ratio?: number; fee_pct?: number; new_tenor_years?: number; sofr_pct?: number | null;
  capex_absorption_pct?: number | null; gpu_share_pct?: number | null; compare_rates?: number[] | null;
}

export interface RefiResult {
  mode: "REFINANCING";
  origin: string;
  instrument: Pick<Instrument, "id" | "name" | "kind" | "principal_usd_m" | "principal_as_of" | "maturity" | "rate_type" | "coupon_pct" |
    "spread_pct" | "effective_rate_pct" | "rate_status" | "rate_note" | "borrower" | "recourse" | "source_ids">;
  params: Required<Omit<RefiParams, "compare_rates">> & { amount_usd_m: number };
  existing_rate: { rate_pct: number; basis: string; status: string; formula: string; fallback: boolean };
  result: RefiCore;
  schedule: ScheduleRow[];
  comparison: (RefiCore & { label: string })[];
  reference: {
    ocf_6m_usd_m: number | null; contractual_interest_6m_usd_m: number | null; cash_usd_m: number | null; capex_6m_usd_m: number | null;
    as_of: string; source_ids: string[]; nvidia_revenue_fy2026_usd_m: number; nvidia_source_id: string;
  };
  assumption_chain: {
    capex_absorption_pct: number | null; capex_cut_usd_m: number | null; gpu_share_pct: number | null;
    gpu_purchase_cut_usd_m: number | null; gpu_cut_vs_nvidia_revenue_pct: number | null;
  };
  rounds: RefiRound[];
  assessments: Record<string, Assessment>;
  warnings: string[];
  notes: string[];
}

export interface EntityDetail {
  entity: NetNode;
  links: (NetEdge & { counterpart: string })[];
  contracts: string[];
  relation: RelationSummary;
}

export interface SourcesResponse { sources: Source[]; status_counts: Record<string, number>; meta: Network["meta"] }

export interface TrendItem { status: "ok" | "insufficient"; label?: string; ref_date?: string; ref_value?: number; change?: number; change_pct?: number | null; }
export interface MarketIndicator {
  id: "hy_oas" | "ust_10y" | "ust_2y" | "gpu_rent" | string; name: string; plain: string; unit: string; unit_note?: string;
  source: { name: string; url: string }; freshness_label?: string; caution: string; license?: string;
  status: string; status_ko: string; detail?: string | null;
  last_attempt_at?: string | null; last_success_at?: string | null;
  last_error?: { code: string; label: string; detail: string } | null;
  latest: null | { value?: number; obs_date?: string; snap_date?: string; median?: number; p25?: number; p75?: number;
    min?: number; max?: number; offer_count?: number; median_dph_base?: number | null; collected_at?: string };
  previous?: MarketIndicator["latest"];
  change_vs_previous?: number | null;
  trend?: { d7: TrendItem; d30: TrendItem };
  history?: { stored_from?: string; stored_to?: string; stored_count?: number; provider_note?: string };
  condition?: Record<string, unknown>; condition_text?: string; fee_note?: string;
}
export interface MarketOverview {
  generated_at?: string; snapshot_at?: string; auto_update?: boolean;
  scheduler?: { enabled: boolean; note: string };
  indicators: MarketIndicator[]; usage_note: string;
}

export interface QuoteItem {
  entity: string; listed: boolean; ticker: string | null; exchange: string | null; listing_note?: string | null;
  provider: "finnhub" | "krx" | "fdr" | "yfinance" | null; symbol: string | null; status: string; status_ko: string; error?: string | null;
  delay_kind?: "realtime" | "close"; delay_label?: string; source?: { name: string; url: string };
  price?: number | null; currency?: string; change?: number | null; change_pct?: number | null; prev_close?: number | null;
  day_high?: number | null; day_low?: number | null; market_cap?: number | null; market_cap_currency?: string | null; market_cap_unit?: string;
  price_time?: string | null; collected_at?: string; basis?: string;
  krw?: { value: number | null; native?: boolean; fx_rate?: number; fx_date?: string; fx_currency?: string; fx_source?: string; note?: string };
}
export interface QuotesOverview {
  generated_at?: string; items: QuoteItem[];
  fx: { source: string; rates: Record<string, { obs_date: string; krw_per_unit: number }> };
  providers: Record<string, { last_success_at: string | null; last_attempt_at: string | null; last_status: string | null; last_status_ko: string | null; detail: string | null }>;
  keys: Record<string, boolean>; note: string; demo?: boolean; static?: boolean;
  /** When set, quotes belong to the PF ecosystem network (not semiconductor). */
  ecosystem?: "semiconductor" | "datacenter_pf" | string;
  /** Client/server clock when this payload was returned (≠ quote market timestamp). */
  retrieved_at?: string;
  refresh_status?: "ok" | "partial" | "throttled" | "error" | "stale_retained" | string;
  refresh_detail?: string;
  refresh_results?: Record<string, { status?: string; detail?: string }>;
}
export interface QuoteHistory {
  entity: string; period: string; symbol?: string; provider?: string; currency?: string | null;
  points: { date: string; close: number; krw: number | null; fx: number | null }[]; status: string; note: string;
}

export interface RunRecord {
  id?: string; created_at?: string; event: string; origin: string; interest: string;
  params: Record<string, number | boolean | string | null>;
  market: Record<string, unknown> | null;
  summary: Record<string, number | string | null>;
}

export interface RateShockParams {
  shock_bp: number;
  benchmark: "sofr" | "ust_2y" | "ust_10y";
  sofr_pct?: number | null;
  crisis_mode?: string;
  refi_availability?: string;
  project_financing?: string;
  horizon_months?: number;
}

/** Rate-shock payload shares round/assessment shape with refinancing for the map UI. */
export interface RateShockResult {
  mode: "RATE_SHOCK";
  origin: string;
  benchmark: { id: string; label: string; label_en: string; plain: string; applies_to: string };
  params: { shock_bp: number; benchmark: string; sofr_pct: number };
  origin_stress?: {
    level: StressLevel;
    intensity: number;
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
    baseline_sofr_pct: number;
    stressed_sofr_pct: number;
    shock_bp: number;
    critical_sofr_pct: number | null;
    critical_shock_bp: number | null;
    bp_to_critical: number | null;
    critical_trigger: string | null;
    metric_trigger: string | null;
    threshold_kind: string;
    assumptions: string[];
    limitations: string[];
    source_ids: string[];
  } | null;
  summary: {
    network_companies: number; direct_measurable: number; potential_indirect: number;
    transmission_channels: number; insufficient_data: number; no_identified_exposure: number;
    total_incremental_interest_usd_m: number | null; floating_sofr_principal_usd_m: number | null;
    fixed_principal_usd_m: number | null; shock_bp: number; benchmark: string;
    stress_level?: StressLevel | null;
    companies_at_or_above_high?: number;
    companies_critical?: number;
    secondary_stressed?: number;
    secondary_critical?: number;
    sector_stressed?: number;
    sector_critical?: number;
    spv_critical?: number;
    order1?: number;
    order2?: number;
    order3_plus?: number;
    quantified_contagion?: number;
    qualitative_contagion?: number;
    pathway_only?: number;
    max_contagion_order?: number;
    crisis_mode?: string;
    baseline_sofr_pct?: number;
    stressed_sofr_pct?: number;
  };
  contagion?: {
    max_order_reached: number;
    counts: Record<string, number>;
    stopped_reason: string;
    events: Array<{
      entity_id: string; order: number; level: StressLevel | null;
      impact_kind: string; from_entity: string; mechanism: string; reason: string;
    }>;
  };
  secondary_stress?: Array<{
    entity_id: string; level: StressLevel; intensity: number; mechanism: string;
    label_en: string; label_ko: string; reason: string; source_ids: string[];
    origin_level: StressLevel; shock_bp: number;
  }>;
  instruments: Array<{
    id: string; name: string; rate_type: string; principal_usd_m: number | null;
    exposure_class: string; annual_interest_delta_usd_m: number | null; reason: string; formula: string | null;
  }>;
  rounds: RefiRound[];
  assessments: Record<string, Assessment & { exposure_class?: string; channels?: string[]; mechanism?: string }>;
  formulas: string[];
  warnings: string[];
  notes: string[];
  /** Partial RefiCore shape — rate-shock fills interest delta / shock fields; rate % may be null. */
  result: {
    annual_interest_delta_usd_m: number;
    shock_bp: number;
    rate_change_bp: number;
    amount_usd_m: number | null;
    new_rate_pct?: number | null;
    existing_rate_pct?: number | null;
    refinanced_usd_m?: number | null;
    not_refinanced_usd_m?: number | null;
    annual_interest_existing_usd_m?: number | null;
    annual_interest_new_usd_m?: number | null;
    one_off_fee_usd_m?: number | null;
    funding_need_usd_m?: number | null;
    delta_6m_usd_m?: number | null;
    delta_6m_vs_ocf_6m_pct?: number | null;
    delta_6m_vs_interest_6m_pct?: number | null;
  };
  instrument: { id: string; name: string } & Record<string, unknown>;
  existing_rate: { rate_pct: number | null; basis: string; status: string; formula: string; fallback: boolean };
  comparison: [];
  schedule: [];
  reference: Record<string, unknown>;
  assumption_chain: Record<string, unknown>;
}

export type SimResult = RefiResult | RateShockResult;

export interface Api {
  /** http = FastAPI; static = GitHub Pages / vite preview; local = embedded demo bundle */
  kind: "http" | "static" | "local";
  /** static build connected to a live quote server (VITE_LIVE_API) */
  live?: boolean;
  health(): Promise<{ status: string; nodes: number; edges: number; as_of: string }>;
  network(): Promise<Network>;
  stats(origin: string): Promise<NetworkStats>;
  path(a: string, b: string): Promise<{ from: string; to: string; path: PathResult | null }>;
  entity(id: string, origin: string): Promise<EntityDetail>;
  simulateRefinancing(p: RefiParams): Promise<RefiResult>;
  simulateRateShock(p: RateShockParams): Promise<RateShockResult>;
  sources(): Promise<SourcesResponse>;
  market(): Promise<MarketOverview | null>;
  refreshMarket(): Promise<MarketOverview | null>;
  quotes(): Promise<QuotesOverview>;
  quoteHistory(id: string, period: string): Promise<QuoteHistory>;
  /** Fresh backend collect. Pass ecosystem=datacenter_pf for the AI DC network. */
  refreshQuotes(opts?: { ecosystem?: "semiconductor" | "datacenter_pf" }): Promise<QuotesOverview>;
  saveRun(r: RunRecord): Promise<RunRecord>;
  listRuns(): Promise<RunRecord[]>;
}
