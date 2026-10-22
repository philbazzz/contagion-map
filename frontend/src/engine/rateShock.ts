/**
 * Port of backend/app/engine/rate_shock.py — keep in step with the Python engine.
 */
import type { Assessment, Instrument, Network, NodeState, RefiRound } from "../types";
import { relationshipSummary } from "./relations";
import {
  computeOriginStress, stressStatus, STRESS_LABEL_KO, THRESHOLDS, type OriginStress, type StressLevel,
} from "./stressModel";
import {
  contagionNodeStatus, propagateContagion, type ContagionEvent, type ContagionPropagationResult,
} from "./multiHopContagion";
import {
  computeSectorFinancingStress, sectorNodeStatus, type CrisisMode, type FundingAvail, type SectorStressResult,
} from "./sectorContagion";
import { SECTOR_STRESS_DATA } from "../data/sectorStress";

export const ORIGIN = "coreweave";

export const SHOCK_STAGES = [
  "Direct Stress",
  "1st-Order Counterparties",
  "2nd-Order Contagion",
  "3rd-Order Contagion",
  "Sector Funding",
  "Ecosystem Summary",
];
export const SHOCK_STAGES_KO = [
  "직접 스트레스",
  "1차 거래상대방",
  "2차 전염",
  "3차 전염",
  "섹터 자금조달",
  "생태계 종합",
];

export type RateBenchmark = "sofr" | "ust_2y" | "ust_10y";

export interface RateShockParams {
  shock_bp: number;
  benchmark: RateBenchmark;
  sofr_pct?: number | null;
  crisis_mode?: CrisisMode;
  refi_availability?: FundingAvail;
  project_financing?: FundingAvail;
  horizon_months?: 12 | 24;
}

export const BENCHMARKS: Record<RateBenchmark, {
  id: RateBenchmark; label: string; label_en: string; plain: string; applies_to: string;
}> = {
  sofr: { id: "sofr", label: "SOFR (단기 기준금리)", label_en: "SOFR", plain: "변동금리 차입금이 대부분 따르는 단기 기준금리", applies_to: "sofr_floating" },
  ust_2y: { id: "ust_2y", label: "미국 2년물 국채 금리", label_en: "US 2Y Treasury", plain: "단기·중기 시장금리의 벤치마크. SOFR 연동 차입과 자동으로 같지 않음", applies_to: "treasury" },
  ust_10y: { id: "ust_10y", label: "미국 10년물 국채 금리", label_en: "US 10Y Treasury", plain: "장기 시장금리의 벤치마크. 고정금리 채권 재발행 환경에 참고", applies_to: "treasury" },
};

export const SHOCK_PRESETS = [-200, -100, -50, 0, 50, 100, 150, 200, 300, 450, 500, 700];

export type { OriginStress, StressLevel };
export { STRESS_LABEL_KO, THRESHOLDS };

export interface InstrumentExposure {
  id: string; name: string; kind: string; rate_type: string; base_rate: string | null;
  principal_usd_m: number | null; maturity: string | null; channel: string | null;
  exposure_class: string; annual_interest_delta_usd_m: number | null; reason: string;
  formula: string | null; evidence_status: string; effective_shock_bp?: number;
}

export interface ShockSummary {
  network_companies: number;
  direct_measurable: number;
  potential_indirect: number;
  transmission_channels: number;
  insufficient_data: number;
  no_identified_exposure: number;
  total_incremental_interest_usd_m: number | null;
  floating_sofr_principal_usd_m: number | null;
  fixed_principal_usd_m: number | null;
  shock_bp: number;
  benchmark: RateBenchmark;
  stress_level: StressLevel | null;
  companies_at_or_above_high: number;
  companies_critical: number;
  secondary_stressed: number;
  secondary_critical: number;
  sector_stressed: number;
  sector_critical: number;
  spv_critical: number;
  order1: number;
  order2: number;
  order3_plus: number;
  quantified_contagion: number;
  qualitative_contagion: number;
  pathway_only: number;
  max_contagion_order: number;
  crisis_mode: CrisisMode;
  baseline_sofr_pct: number;
  stressed_sofr_pct: number;
}

export interface RateShockResult {
  mode: "RATE_SHOCK";
  origin: string;
  benchmark: (typeof BENCHMARKS)[RateBenchmark];
  params: { shock_bp: number; benchmark: RateBenchmark; sofr_pct: number };
  summary: ShockSummary;
  origin_stress: OriginStress | null;
  /** @deprecated kept for UI compat — prefer contagion.events */
  secondary_stress: ContagionEvent[];
  contagion: ContagionPropagationResult;
  sector_stress: SectorStressResult[];
  instruments: InstrumentExposure[];
  rounds: RefiRound[];
  assessments: Record<string, Assessment & { exposure_class?: string; channels?: string[]; mechanism?: string }>;
  formulas: string[];
  warnings: string[];
  notes: string[];
  result: {
    annual_interest_delta_usd_m: number;
    shock_bp: number;
    rate_change_bp: number;
    amount_usd_m: number | null;
    [k: string]: number | null | undefined;
  };
  instrument: { id: string; name: string; [k: string]: unknown };
  existing_rate: { rate_pct: number | null; basis: string; status: string; formula: string; fallback: boolean };
  comparison: [];
  schedule: [];
  reference: Record<string, unknown>;
  assumption_chain: Record<string, null>;
}

export class ShockError extends Error {}

function r(x: number, nd = 4): number {
  const k = 10 ** nd;
  return Math.floor(x * k + 0.5) / k;
}
function g(x: number): string {
  const s = r(x, 6).toFixed(6).replace(/0+$/, "").replace(/\.$/, "");
  return s === "-0" || s === "" ? "0" : s;
}
function m(x: number): string {
  const a = Math.abs(x);
  const sign = x < 0 ? "−" : x > 0 ? "+" : "";
  const body = a >= 1000 ? `$${(a / 1000).toFixed(2)}B` : a >= 10 ? `$${a.toFixed(0)}M` : `$${a.toFixed(1)}M`;
  return sign + body;
}
const u = (x: number) => m(Math.abs(x)).replace(/^[+−]+/, "");

function edgeTo(net: Network, a: string, b: string, prefer?: string): string | null {
  const c = net.edges.filter((e) => e.source === a && e.target === b);
  if (prefer) for (const e of c) if (e.impact_channel === prefer) return e.id;
  return c.length ? c[0].id : null;
}

function floatingSens(principal: number, shockBp: number, sofr: number, floor: number | null) {
  let effBp = shockBp;
  let note = `원금 ${u(principal)} × ${shockBp >= 0 ? "+" : ""}${shockBp}bp / 10,000`;
  let formula = "principal_usd_m × shock_bp / 10_000";
  if (floor !== null) {
    const base = Math.max(sofr, floor);
    const shocked = Math.max(sofr + shockBp / 100, floor);
    effBp = (shocked - base) * 100;
    note = `SOFR ${g(sofr)}% (하한 ${g(floor)}%) → 충격 후 ${g(shocked)}% · 유효 ${g(effBp)}bp × 원금 ${u(principal)}`;
    formula = "max(SOFR+shock, floor) − max(SOFR, floor), then × principal";
  }
  return { annual_interest_delta_usd_m: r(principal * effBp / 10000), effective_shock_bp: r(effBp, 2), formula, note };
}

export function simulateRateShock(net: Network, p: RateShockParams): RateShockResult {
  const benchmark = p.benchmark;
  if (!BENCHMARKS[benchmark]) throw new ShockError(`알 수 없는 벤치마크: ${benchmark}`);
  if (!(p.shock_bp >= -700 && p.shock_bp <= 700)) throw new ShockError("금리 충격은 −700bp ~ +700bp 범위");
  const crisisMode: CrisisMode = p.crisis_mode || "rate_only";
  const refiAvail: FundingAvail = p.refi_availability || "normal";
  const projectFin: FundingAvail = p.project_financing || "normal";
  const horizon: 12 | 24 = p.horizon_months === 24 ? 24 : 12;
  const cwDefaultOn = crisisMode === "cw_default" || crisisMode === "combined";
  const financingOn = crisisMode === "financing" || crisisMode === "combined";
  const fin = net.financials;
  const sofr = p.sofr_pct == null ? fin.market_inputs.sofr_pct : p.sofr_pct;
  if (!(sofr >= 0 && sofr <= 20)) throw new ShockError("SOFR는 0~20%");
  const bm = BENCHMARKS[benchmark];
  const applies = bm.applies_to;
  const warnings: string[] = [];
  const instrumentRows: InstrumentExposure[] = [];

  let floatingKnown = 0, fixedKnown = 0, floatingUnknown = 0, computedDelta = 0;
  let hasComputed = false;

  for (const inst of fin.instruments) {
    const principal = inst.principal_usd_m;
    const row: InstrumentExposure = {
      id: inst.id, name: inst.name, kind: inst.kind, rate_type: inst.rate_type, base_rate: inst.base_rate,
      principal_usd_m: principal, maturity: inst.maturity, channel: null, exposure_class: "not_applicable",
      annual_interest_delta_usd_m: null, reason: "", formula: null, evidence_status: inst.rate_status || "UNKNOWN",
    };

    if (inst.rate_type === "floating" && (inst.base_rate || "").toUpperCase() === "SOFR") {
      if (principal && principal > 0) floatingKnown += principal;
      else if (principal === null) floatingUnknown += 1;

      if (applies === "sofr_floating") {
        if (principal === null) {
          Object.assign(row, { channel: "floating_rate_interest", exposure_class: "insufficient_data",
            reason: "SOFR 연동 변동금리이나 잔액이 공시되지 않아 이자 민감도를 계산할 수 없음" });
        } else if (principal <= 0) {
          Object.assign(row, { channel: "floating_rate_interest", exposure_class: "not_applicable",
            reason: "약정은 있으나 인출 잔액 0 — 이자 민감도 없음" });
        } else {
          const sens = floatingSens(principal, p.shock_bp, sofr, inst.floor_pct);
          Object.assign(row, {
            channel: "floating_rate_interest", exposure_class: "direct_computed",
            annual_interest_delta_usd_m: sens.annual_interest_delta_usd_m, reason: sens.note,
            formula: sens.formula, effective_shock_bp: sens.effective_shock_bp,
          });
          computedDelta += sens.annual_interest_delta_usd_m;
          hasComputed = true;
        }
      } else {
        Object.assign(row, {
          channel: "floating_rate_interest", exposure_class: "benchmark_mismatch",
          reason: `이 차입금은 SOFR에 연동됩니다. 선택한 벤치마크(${bm.label})와 자동으로 같지 않아 이자비용을 계산하지 않습니다.`,
        });
        warnings.push(`${inst.name}: SOFR 연동 — ${bm.label} 충격은 자동 적용하지 않음`);
      }
    } else if (inst.rate_type === "fixed") {
      if (principal && principal > 0) fixedKnown += principal;
      if (applies === "treasury") {
        Object.assign(row, {
          channel: "fixed_rate_refinancing", exposure_class: "qualitative_refi",
          reason: `고정금리 ${inst.coupon_pct === null || inst.coupon_pct === undefined ? "null" : (Number.isInteger(inst.coupon_pct) ? `${inst.coupon_pct}.0` : String(inst.coupon_pct))}% · 만기 ${inst.maturity || "미공시"}. 만기 전 이자비용은 변하지 않음. 만기 재발행 시 시장금리가 반영될 수 있으나 재발행 금리·잔액 가정이 없어 금액을 만들지 않음.`,
        });
      } else {
        Object.assign(row, {
          channel: "fixed_rate_refinancing", exposure_class: "not_applicable",
          reason: "고정금리 — SOFR 충격이 만기 전 이자비용에 직접 적용되지 않음",
        });
      }
    } else if (inst.rate_type === "unknown") {
      Object.assign(row, {
        channel: "unknown_rate", exposure_class: "insufficient_data",
        reason: "금리 유형(고정/변동)이 공시되지 않아 민감도를 계산할 수 없음",
      });
    } else {
      row.reason = "이 시나리오와 직접 관련 없음";
    }
    instrumentRows.push(row);
  }

  const lenderIds = new Set<string>();
  for (const inst of fin.instruments) for (const pp of inst.participants || []) lenderIds.add(pp.entity);
  const supplyIndirect = new Set(["nvidia", "dell", "sk_hynix", "tsmc", "samsung"]);
  const customerIds = new Set(net.edges.filter((e) => e.impact_channel === "customer" && e.source === ORIGIN).map((e) => e.target));
  const facilityIds = new Set(net.edges.filter((e) => e.impact_channel === "facility").map((e) => e.target));

  const assessments: RateShockResult["assessments"] = {};
  const originValues = hasComputed && applies === "sofr_floating"
    ? [{ label: "추가 연간 이자비용 (SOFR 연동·잔액 공시분)", usd_m: r(computedDelta), status: "computed", round: 0 }]
    : [];

  for (const n of net.nodes) {
    const nid = n.id;
    const rel = relationshipSummary(net, ORIGIN, nid);
    if (nid === ORIGIN) {
      if (applies === "sofr_floating" && hasComputed) {
        assessments[nid] = {
          category: "computed", exposure_class: "direct_computed", relation: rel, values: originValues,
          reason: `SOFR 연동 변동금리 잔액(공시분) ${u(floatingKnown)}에 ${p.shock_bp >= 0 ? "+" : ""}${p.shock_bp}bp를 적용. 공식: 원금 × bp / 10,000. 고정금리·미공시 잔액은 제외.`,
          needed: floatingUnknown === 0 ? null : "잔액 미공시 변동금리 차입금의 인출 잔액",
          channels: ["floating_rate_interest"],
        };
      } else if (applies === "sofr_floating") {
        assessments[nid] = {
          category: "relationship_only", exposure_class: "insufficient_data", relation: rel, values: [],
          reason: "SOFR 연동 차입금이 있으나 계산 가능한 잔액이 없음", needed: "변동금리 차입금 잔액",
          channels: ["floating_rate_interest"],
        };
      } else {
        assessments[nid] = {
          category: "relationship_only", exposure_class: "qualitative_refi", relation: rel, values: [],
          reason: `${bm.label} 충격은 CoreWeave의 SOFR 연동 이자에 자동 적용하지 않습니다. 고정금리 공시 잔액 ${u(fixedKnown)}은 만기 재발행 시에만 시장금리가 반영될 수 있으며, 재발행 가정을 넣지 않아 금액을 만들지 않습니다.`,
          needed: "만기별 재발행 금리·금액 가정 (사용자 입력 시 별도 차환 도구 사용)",
          channels: ["fixed_rate_refinancing"],
        };
      }
      continue;
    }
    if (rel.kind === "unconfirmed") {
      assessments[nid] = {
        category: "unconfirmed", exposure_class: "no_identified_exposure", relation: rel, values: [],
        reason: "공개자료에서 확인된 관계 경로 없음", needed: "관계를 입증할 공시·계약 자료", channels: [],
      };
      continue;
    }
    if (lenderIds.has(nid)) {
      assessments[nid] = {
        category: "relationship_only", exposure_class: "transmission_channel", relation: rel, values: [],
        reason: "대주·주선 기관. 금리 상승은 대주에게 자동 손실이 아니라 이자수익·자산가치 변화일 수 있음. 기관별 보유액 미공시로 손익을 계산하지 않음.",
        needed: "기관별 대출 보유액·헤지·재매각 여부", channels: ["lender_borrower"],
      };
      continue;
    }
    if (supplyIndirect.has(nid) && applies === "sofr_floating" && hasComputed && computedDelta > 0) {
      const neededMap: Record<string, string> = {
        nvidia: "CoreWeave 연간 GPU 구매액", dell: "Dell 서버 구매액",
        sk_hynix: "NVIDIA HBM 매입 중 SK hynix 비중", tsmc: "NVIDIA 위탁생산 중 CoreWeave 관련 비중",
        samsung: "NVIDIA HBM 매입 중 Samsung 비중",
      };
      assessments[nid] = {
        category: "relationship_only", exposure_class: "potential_indirect", relation: rel, values: [],
        reason: "공급망 관계는 확인되나, 이자비용 증가 → CAPEX/구매 축소 규모는 가정 없이는 계산하지 않음 (잠재 전달 경로).",
        needed: neededMap[nid] || null, channels: ["supplier_customer"],
      };
      continue;
    }
    if (customerIds.has(nid) || facilityIds.has(nid)) {
      assessments[nid] = {
        category: "relationship_only", exposure_class: "potential_indirect", relation: rel, values: [],
        reason: "고객·데이터센터 관계는 확인되나, 금리 충격이 계약 대금·임차료로 전달된다는 공시가 없어 정량 영향을 만들지 않음.",
        needed: null, channels: [customerIds.has(nid) ? "supplier_customer" : "facility"],
      };
      continue;
    }
    assessments[nid] = {
      category: "relationship_only", exposure_class: "potential_indirect", relation: rel, values: [],
      reason: "관계는 확인되나 이번 금리 충격과 정량 전달 경로·데이터가 없음", needed: null, channels: [],
    };
  }

  let originStress = applies === "sofr_floating"
    ? computeOriginStress(fin, p.shock_bp, hasComputed ? computedDelta : null, floatingKnown, sofr, hasComputed)
    : null;

  // Scenario A/C: CoreWeave default assumption elevates origin band for contagion mapping.
  if (cwDefaultOn && originStress && originStress.level !== "critical") {
    originStress = {
      ...originStress,
      level: "critical",
      intensity: Math.max(originStress.intensity, 1.55),
      metric_trigger: (originStress.metric_trigger || "") + " · CW default scenario assumption",
      limitations: [
        ...(originStress.limitations || []),
        "CoreWeave default is a SCENARIO ASSUMPTION for counterparty mapping — not a predicted legal default.",
      ],
    };
  } else if (cwDefaultOn && !originStress) {
    originStress = {
      entity: ORIGIN, level: "critical", intensity: 1.55, score_delta_over_ocf: null,
      baseline_interest_ann_usd_m: null, stressed_interest_ann_usd_m: null, annualized_ocf_usd_m: null,
      baseline_coverage: null, stressed_coverage: null, coverage_change: null, delta_interest_usd_m: null,
      floating_principal_usd_m: floatingKnown, cash_usd_m: null, incremental_vs_cash_pct: null,
      baseline_sofr_pct: sofr, stressed_sofr_pct: r(sofr + p.shock_bp / 100, 4), shock_bp: p.shock_bp,
      critical_sofr_pct: null, critical_shock_bp: null, bp_to_critical: null,
      critical_trigger: "CW default scenario assumption", threshold_kind: "analytical",
      assumptions: ["User selected CoreWeave default scenario"], limitations: ["Not a legal default prediction"],
      source_ids: [], metric_trigger: "CW default scenario",
    };
  }

  const presentIds = new Set(net.nodes.map((n) => n.id));

  // Multi-hop counterparty contagion (orders 1…N). Financing-only skips network hops.
  const contagion = crisisMode === "financing" || !originStress
    ? propagateContagion(net, ORIGIN, "normal", p.shock_bp, { enabled: false })
    : propagateContagion(net, ORIGIN, originStress.level, p.shock_bp, { maxOrder: 6, enabled: true });

  for (const ev of contagion.events) {
    if (!presentIds.has(ev.entity_id)) continue;
    const rel = relationshipSummary(net, ORIGIN, ev.entity_id);
    const cls = ev.impact_kind === "quantified"
      ? (ev.order <= 1 ? "secondary_contagion" : "multihop_contagion")
      : ev.impact_kind === "qualitative"
        ? "qualitative_contagion"
        : ev.impact_kind === "pathway"
          ? "potential_indirect"
          : "insufficient_data";
    assessments[ev.entity_id] = {
      category: "relationship_only",
      exposure_class: cls,
      relation: rel,
      values: [],
      reason: ev.reason,
      needed: ev.impact_kind === "pathway" || ev.impact_kind === "unsupported"
        ? "보유액·헤지·계약현금흐름 규모"
        : null,
      channels: ["contagion", `order_${ev.order}`, ev.mechanism],
      mechanism: ev.mechanism,
    };
  }

  const sectorList = financingOn
    ? computeSectorFinancingStress(SECTOR_STRESS_DATA, presentIds, {
      shockBp: Math.max(0, p.shock_bp),
      refi: refiAvail,
      projectFinancing: projectFin,
      horizonMonths: horizon,
    })
    : [];
  // Do not re-stamp hop-contagion entities with sector unless sector is worse / insufficient-only
  for (const sec of sectorList) {
    if (!presentIds.has(sec.entity_id)) continue;
    const hop = contagion.by_entity[sec.entity_id];
    if (hop?.level === "critical" || hop?.level === "high") continue;
    const rel = relationshipSummary(net, ORIGIN, sec.entity_id);
    const cls = sec.level === "insufficient" ? "insufficient_data" : "sector_contagion";
    assessments[sec.entity_id] = {
      category: "relationship_only",
      exposure_class: cls,
      relation: rel,
      values: [],
      reason: sec.reason,
      needed: sec.level === "insufficient" ? "공개 연결 재무제표" : null,
      channels: ["sector_financing", sec.mechanism],
      mechanism: sec.mechanism,
    };
  }

  const hopStressed = contagion.events.filter((e) => e.level === "high" || e.level === "critical");
  const hopCrit = contagion.events.filter((e) => e.level === "critical");
  const spvCrit = contagion.events.filter((e) => e.mechanism === "spv_debt_service" && e.level === "critical");

  const classes = Object.fromEntries(Object.entries(assessments).map(([id, a]) => [id, a.exposure_class || ""]));
  const count = (cls: string) => Object.values(classes).filter((c) => c === cls).length;
  const insuff = ["insufficient_data", "qualitative_refi", "benchmark_mismatch"]
    .reduce((n, c) => n + count(c), 0);

  const allStressed = [
    ...(originStress && (originStress.level === "high" || originStress.level === "critical") ? [ORIGIN] : []),
    ...hopStressed.map((s) => s.entity_id),
    ...sectorList.filter((s) => s.level === "high" || s.level === "critical").map((s) => s.entity_id),
  ];
  const allCrit = [
    ...(originStress?.level === "critical" ? [ORIGIN] : []),
    ...hopCrit.map((s) => s.entity_id),
    ...sectorList.filter((s) => s.level === "critical").map((s) => s.entity_id),
  ];

  const summary: ShockSummary = {
    network_companies: net.nodes.length,
    direct_measurable: count("direct_computed"),
    potential_indirect: count("potential_indirect"),
    transmission_channels: count("transmission_channel"),
    insufficient_data: insuff,
    no_identified_exposure: count("no_identified_exposure"),
    total_incremental_interest_usd_m: hasComputed ? r(computedDelta) : null,
    floating_sofr_principal_usd_m: r(floatingKnown),
    fixed_principal_usd_m: r(fixedKnown),
    shock_bp: p.shock_bp,
    benchmark,
    stress_level: originStress?.level ?? null,
    companies_at_or_above_high: new Set(allStressed).size,
    companies_critical: new Set(allCrit).size,
    secondary_stressed: contagion.counts.order1 + contagion.counts.order2,
    secondary_critical: hopCrit.filter((e) => e.order <= 2).length,
    sector_stressed: sectorList.filter((s) => s.level !== "insufficient").length,
    sector_critical: sectorList.filter((s) => s.level === "critical").length,
    spv_critical: spvCrit.length,
    order1: contagion.counts.order1,
    order2: contagion.counts.order2,
    order3_plus: contagion.counts.order3_plus,
    quantified_contagion: contagion.counts.quantified,
    qualitative_contagion: contagion.counts.qualitative,
    pathway_only: contagion.counts.pathway,
    max_contagion_order: contagion.max_order_reached,
    crisis_mode: crisisMode,
    baseline_sofr_pct: sofr,
    stressed_sofr_pct: r(sofr + p.shock_bp / 100, 4),
  };

  const rounds = buildRounds(net, bm, p.shock_bp, applies, hasComputed, computedDelta, floatingKnown,
    assessments, instrumentRows, lenderIds, originStress, contagion, sectorList, crisisMode, cwDefaultOn);

  const metric = (id: string) => fin.metrics.find((mm) => mm.id === id)?.value_usd_m ?? null;

  return {
    mode: "RATE_SHOCK",
    origin: ORIGIN,
    benchmark: bm,
    params: { shock_bp: p.shock_bp, benchmark, sofr_pct: sofr },
    summary,
    origin_stress: originStress,
    secondary_stress: contagion.events,
    contagion,
    sector_stress: sectorList,
    instruments: instrumentRows,
    rounds,
    assessments,
    formulas: [
      "SOFR 연동 변동금리 (잔액 공시): 연간 이자 변화(USD M) = principal_usd_m × shock_bp / 10_000",
      "하한(floor) 있는 경우: 유효 금리변화 = max(SOFR+shock, floor) − max(SOFR, floor)",
      "고정금리: 만기 전 이자비용 불변 — 금액 미산정",
      "국채 충격은 SOFR 연동 이자에 자동 가산하지 않음",
      `직접 스트레스 점수 = Δ연간이자 / 연환산 OCF · 밴드: moderate≥${THRESHOLDS.moderate_delta_over_ocf * 100}%, high≥${THRESHOLDS.high_delta_over_ocf * 100}%, critical≥${THRESHOLDS.critical_delta_over_ocf * 100}% 또는 커버리지<${THRESHOLDS.critical_coverage}x (분석용, 약정 아님)`,
      "다단계 전염: 검증된 엣지 + 전달 규칙(임차·SPV·프로젝트지분·주선) · order 1…N · 확정 부도 아님",
      "경로 도달 ≠ 정량 손실. quantified / qualitative / pathway / unsupported 구분",
    ],
    warnings: warnings.slice(0, 12),
    notes: [
      "결과는 스트레스 시나리오이며 주가·부도·투자 예측이 아닙니다.",
      "행성 균열·파괴는 모델상 심각 재무 압박 경고이며 실제 파산 판정이 아닙니다.",
      "직접 금리 민감도(A), CoreWeave 채무불이행·임차 2차 전염(B), 섹터 자금경색(C)을 분리·결합해 모델링합니다.",
      "SPV 심각 스트레스 ≠ 모회사 자동 파산 (비소구 notes / 완공보증만).",
      "관계가 있다고 해서 재무 손실이 있다고 보지 않습니다.",
      "시장 관측값(국채·SOFR)과 시나리오 가정(충격 bp)을 구분합니다.",
      `SOFR 관측값 ${g(sofr)}% (${fin.market_inputs.sofr_date}) — 하한·스트레스 기준금리에 사용.`,
      `위기 모드: ${crisisMode} · 차환=${refiAvail} · 프로젝트금융=${projectFin} · ${horizon}개월`,
    ],
    result: {
      annual_interest_delta_usd_m: hasComputed ? r(computedDelta) : 0,
      shock_bp: p.shock_bp,
      rate_change_bp: p.shock_bp,
      new_rate_pct: r(sofr + p.shock_bp / 100, 4),
      existing_rate_pct: sofr,
      amount_usd_m: r(floatingKnown),
      refinanced_usd_m: null,
      not_refinanced_usd_m: null,
      annual_interest_existing_usd_m: originStress?.baseline_interest_ann_usd_m ?? null,
      annual_interest_new_usd_m: originStress?.stressed_interest_ann_usd_m ?? null,
      one_off_fee_usd_m: 0,
      funding_need_usd_m: 0,
      delta_6m_usd_m: hasComputed ? r(computedDelta / 2) : null,
      delta_6m_vs_ocf_6m_pct: originStress?.score_delta_over_ocf != null ? r(originStress.score_delta_over_ocf * 100, 2) : null,
      delta_6m_vs_interest_6m_pct: null,
      stressed_coverage: originStress?.stressed_coverage ?? null,
      critical_sofr_pct: originStress?.critical_sofr_pct ?? null,
    },
    instrument: {
      id: "ecosystem", name: `${bm.label_en} ${p.shock_bp >= 0 ? "+" : ""}${p.shock_bp}bp`, kind: "term_loan",
      principal_usd_m: r(floatingKnown), principal_as_of: fin.as_of, maturity: null,
      rate_type: applies === "sofr_floating" ? "floating" : "unknown",
      coupon_pct: null, spread_pct: null, effective_rate_pct: null, rate_status: "ASSUMED",
      rate_note: "생태계 금리 충격 시나리오", borrower: ORIGIN, recourse: null,
      source_ids: fin.filing ? [fin.filing] : [],
    },
    existing_rate: {
      rate_pct: applies === "sofr_floating" ? sofr : null, basis: "market",
      status: applies === "sofr_floating" ? "VERIFIED" : "ASSUMED",
      formula: `충격 ${p.shock_bp >= 0 ? "+" : ""}${p.shock_bp}bp · ${bm.label}`, fallback: false,
    },
    comparison: [],
    schedule: [],
    reference: {
      ocf_6m_usd_m: metric("ocf_6m"), contractual_interest_6m_usd_m: metric("contractual_interest_6m"),
      cash_usd_m: metric("cash"), capex_6m_usd_m: metric("capex_6m"), as_of: fin.as_of,
      source_ids: fin.filing ? [fin.filing] : [],
      nvidia_revenue_fy2026_usd_m: fin.reference.nvidia_revenue_fy2026_usd_m,
      nvidia_source_id: fin.reference.nvidia_source_id,
    },
    assumption_chain: {
      capex_absorption_pct: null, capex_cut_usd_m: null, gpu_share_pct: null,
      gpu_purchase_cut_usd_m: null, gpu_cut_vs_nvidia_revenue_pct: null,
    },
  };
}

function applyHopEvents(
  states: Record<string, NodeState>,
  events: ContagionEvent[],
): string[] {
  const edges: string[] = [];
  for (const ev of events) {
    states[ev.entity_id] = {
      status: contagionNodeStatus(ev.level, ev.impact_kind),
      label: ev.order >= 3
        ? `[L${ev.order}] ${ev.label_ko}`
        : ev.label_ko,
      category: "relationship_only",
      intensity: ev.intensity,
      stress: ev.level || undefined,
    };
    if (ev.edge_id) edges.push(ev.edge_id);
  }
  return edges;
}

function buildRounds(
  net: Network, bm: (typeof BENCHMARKS)[RateBenchmark], shockBp: number, applies: string,
  hasComputed: boolean, computedDelta: number, floatingKnown: number,
  assessments: RateShockResult["assessments"], instrumentRows: InstrumentExposure[],
  lenderIds: Set<string>,
  originStress: OriginStress | null,
  contagion: ContagionPropagationResult,
  sectorList: SectorStressResult[],
  crisisMode: CrisisMode,
  cwDefaultOn: boolean,
): RefiRound[] {
  const states: Record<string, NodeState> = {};
  const rounds: RefiRound[] = [];
  const signBp = `${shockBp >= 0 ? "+" : ""}${shockBp}`;
  const snap = (i: number, lines: string[], active: string[]) => {
    const ns: Record<string, NodeState> = {};
    for (const [k, v] of Object.entries(states)) ns[k] = { ...v };
    rounds.push({ round: i, stage: i + 1, title: `STAGE ${i + 1} · ${SHOCK_STAGES[i]}`, title_ko: SHOCK_STAGES_KO[i], lines, active_edges: active, node_states: ns });
  };

  let stage0: string[];
  if (originStress) {
    const st = stressStatus(originStress.level, true);
    states[ORIGIN] = {
      status: st,
      label: cwDefaultOn
        ? `CW 채무불이행 가정 · ${STRESS_LABEL_KO[originStress.level]}`
        : (hasComputed ? `이자 ${m(computedDelta)}/년 · ${STRESS_LABEL_KO[originStress.level]}` : STRESS_LABEL_KO[originStress.level]),
      category: hasComputed ? "computed" : "relationship_only",
      intensity: originStress.intensity,
      stress: originStress.level,
    };
    stage0 = [
      `모드 ${crisisMode} · SOFR ${g(originStress.baseline_sofr_pct)}% → ${g(originStress.stressed_sofr_pct)}% (${signBp}bp)`,
      hasComputed && applies === "sofr_floating"
        ? `CoreWeave SOFR 연동 ${u(floatingKnown)} → 연간 이자 ${m(computedDelta)}`
        : "직접 이자 민감도: 이번 설정에서 미산정 또는 해당 없음",
      cwDefaultOn ? "CoreWeave 계약 불이행은 시나리오 가정 — 법적 부도 예측 아님" : "",
      `다단계 전염 엔진 · max order 도달 ${contagion.max_order_reached} · ${contagion.stopped_reason}`,
    ].filter(Boolean);
  } else if (applies === "sofr_floating") {
    states[ORIGIN] = { status: "insufficient", label: "데이터 부족", category: "relationship_only", intensity: 0.35, stress: "insufficient" };
    stage0 = [`${bm.label} ${signBp}bp · 계산 가능한 SOFR 잔액 없음`];
  } else {
    states[ORIGIN] = { status: "potential", label: "정성 경로", category: "relationship_only", intensity: 0.4, stress: "not_applicable" };
    stage0 = [`${bm.label} ${signBp}bp`, (assessments[ORIGIN]?.reason || "").slice(0, 120)];
  }
  const insuffN0 = instrumentRows.filter((x) => x.exposure_class === "insufficient_data").length;
  if (insuffN0) stage0.push(`잔액·금리 미공시 차입금 ${insuffN0}건 — 금액 미산정`);
  snap(0, stage0, []);

  // Stage 1 — first-order counterparties (+ lender channels as contract_party backdrop)
  const finEdges: string[] = [];
  for (const lid of [...lenderIds].sort()) {
    if (!states[lid]) {
      states[lid] = { status: "contract_party", label: "전달 채널 · 미산정", category: "relationship_only" };
    }
    const e = edgeTo(net, ORIGIN, lid, "financial");
    if (e) finEdges.push(e);
  }
  const o1 = contagion.events.filter((e) => e.order === 1);
  const e1 = applyHopEvents(states, o1);
  snap(1, [
    `1차(order 1) ${o1.length}곳 · quantified ${o1.filter((e) => e.impact_kind === "quantified").length} · pathway ${o1.filter((e) => e.impact_kind === "pathway").length}`,
    ...o1.slice(0, 5).map((e) => `${net.nodes.find((n) => n.id === e.entity_id)?.name || e.entity_id}: ${e.label_en}`),
    o1.length === 0 ? "1차 전염 없음 — 원점 스트레스 또는 임차 집중도 임계 미충족" : "그래프 경로 ≠ 자동 손실",
    `대주 채널 ${lenderIds.size}곳 — 보유 미공시로 손익 미산정`,
  ].filter(Boolean), [...new Set([...finEdges, ...e1])]);

  // Stage 2 — second-order
  const o2 = contagion.events.filter((e) => e.order === 2);
  const e2 = applyHopEvents(states, o2);
  snap(2, [
    `2차(order 2) ${o2.length}곳 · SPV·프로젝트 자본 등`,
    ...o2.slice(0, 5).map((e) => `${net.nodes.find((n) => n.id === e.entity_id)?.name || e.entity_id}: ${e.label_en} ← ${e.from_entity}`),
    o2.length === 0 ? "2차 전염 없음 — 1차에서 추가 전파 임계 미충족" : "SPV 심각 ≠ 모회사 자동 파산",
  ], e2);

  // Stage 3 — third-order and beyond
  const o3 = contagion.events.filter((e) => e.order >= 3);
  const e3 = applyHopEvents(states, o3);
  snap(3, [
    `3차+(order≥3) ${o3.length}곳 · maxOrder=${contagion.max_order_reached}`,
    ...o3.slice(0, 6).map((e) => `L${e.order} ${net.nodes.find((n) => n.id === e.entity_id)?.name || e.entity_id}: ${e.label_en} (${e.impact_kind}) ← ${e.from_entity}`),
    o3.length === 0
      ? "3차 정량 스트레스 없음 — 주선은행 등은 pathway(보유≠손실)로만 표시되거나 데이터 부족"
      : "3차 정량 파괴는 공시 집중도·SPV 구조가 있을 때만",
  ], e3);

  // Stage 4 — sector funding (market-wide, not hop-based)
  const sectorEdges = [...e1, ...e2, ...e3];
  for (const sec of sectorList) {
    if (states[sec.entity_id]?.stress === "critical" || states[sec.entity_id]?.stress === "high") continue;
    states[sec.entity_id] = {
      status: sectorNodeStatus(sec.level),
      label: sec.label_ko,
      category: "relationship_only",
      intensity: sec.intensity,
      stress: sec.level === "insufficient" ? "insufficient" : sec.level,
    };
  }
  if (sectorList.length) {
    snap(4, [
      `섹터 자금조달(비-홉) ${sectorList.filter((s) => s.level !== "insufficient").length}곳 · 데이터부족 ${sectorList.filter((s) => s.level === "insufficient").length}`,
      ...sectorList.slice(0, 5).map((s) => `${net.nodes.find((n) => n.id === s.entity_id)?.name || s.entity_id}: ${s.label_en}`),
      "시장 공통 조달 스트레스 — 회사간 전염과 이중계산하지 않음",
    ], sectorEdges);
  } else {
    snap(4, [
      crisisMode === "financing" || crisisMode === "combined"
        ? "섹터 모드이나 임계 초과 기업 없음"
        : "섹터 자금경색 꺼짐 — Financing/Combined에서 활성화",
    ], []);
  }

  const cats: Record<string, number> = {};
  for (const a of Object.values(assessments)) {
    const c = a.exposure_class || "";
    cats[c] = (cats[c] || 0) + 1;
  }
  const insuffN = (cats.insufficient_data || 0) + (cats.qualitative_refi || 0) + (cats.benchmark_mismatch || 0);
  snap(5, [
    `네트워크 ${net.nodes.length} · 모드 ${crisisMode} · 전염 max order ${contagion.max_order_reached}`,
    `order1 ${contagion.counts.order1} · order2 ${contagion.counts.order2} · order3+ ${contagion.counts.order3_plus} · quantified ${contagion.counts.quantified} · qualitative ${contagion.counts.qualitative} · pathway ${contagion.counts.pathway}`,
    `심각(critical) hops ${contagion.counts.critical} · 섹터 critical ${sectorList.filter((s) => s.level === "critical").length} · 데이터부족/정성 ${insuffN}`,
    hasComputed ? `CW 추가 연간 이자 ${m(computedDelta)}` : "CW 추가 이자 미산정",
    "행성 파괴 = 모델상 심각 재무 압박 — 확정 파산 아님 · 경로≠손실",
  ], [...new Set([...finEdges, ...sectorEdges])].sort());

  return rounds;
}

/** Quick check used by UI: floating SOFR principal that would respond to a SOFR shock. */
export function sofrFloatingPrincipal(net: Network): number {
  return net.financials.instruments
    .filter((i: Instrument) => i.rate_type === "floating" && (i.base_rate || "").toUpperCase() === "SOFR" && (i.principal_usd_m || 0) > 0)
    .reduce((s, i) => s + (i.principal_usd_m || 0), 0);
}
