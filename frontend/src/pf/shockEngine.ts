/**
 * AI Data Center Project Finance shock engine.
 * Separate from semiconductor/CoreWeave rateShock — project DSCR, GPU rent, hyperscaler CAPEX.
 */
import type { Assessment, Category, NetEdge, Network, NodeState, RefiRound, StressLevel } from "../types";
import type {
  PfAffectedCompany, PfDefaultAssessment, PfImpactCategory, PfProject, PfProjectStress,
  PfShockForm, PfShockResult, PfProjectsFile,
} from "./types";
import { displayName } from "../lib/displayName";
import { REL_LABEL } from "../lib/format";

const GPU_OPERATORS = new Set(["coreweave", "lambda", "nebius", "nscale", "crusoe"]);
const KR_EQUIPMENT = new Set(["ls_electric", "hd_hyundai_electric", "hyosung_heavy", "doosan_enerbility", "lg_electronics"]);
const US_LANDLORDS = new Set(["core_scientific", "applied_digital", "galaxy_digital", "corz_finance_i", "galaxy_helios_ii", "helios_campus", "corz_cw_sites", "polaris_forge_1"]);

const CW_RANK: Record<string, number> = {
  normal: 0, moderate: 1, severe_liquidity: 2, payment_default: 3, insolvency: 4,
};

function cwStress(form: PfShockForm): { level: StressLevel; intensity: number; rank: number } {
  const rank = CW_RANK[form.coreweaveDistress] ?? 0;
  if (rank === 0) return { level: "normal", intensity: 0, rank };
  if (rank === 1) return { level: "moderate", intensity: 0.4, rank };
  if (rank === 2) return { level: "high", intensity: 0.7, rank };
  if (rank === 3) return { level: "critical", intensity: 0.88, rank };
  return { level: "critical", intensity: 0.95, rank };
}

function isKrFinGroup(group: string) {
  return group.startsWith("kr_") || group === "financial";
}

function classifyImpact(rel: string, contingent: boolean, group: string): PfImpactCategory {
  if (contingent || ["CREDIT_ENHANCEMENT", "COMPLETION_GUARANTEE", "DEBT_ASSUMPTION", "LOAN_GUARANTEE", "REFINANCING_UNDERWRITE"].includes(rel)) {
    return "보증·추가 자금부담 가능";
  }
  if (["PROJECT_LOAN", "ACQUISITION_LOAN", "EQUITY_INVESTMENT", "EQUITY_SPONSOR", "PREFERRED_EQUITY", "SHAREHOLDER_LOAN"].includes(rel)) {
    return "대출·투자금 손실 가능";
  }
  if (["EPC_CONTRACT", "FACILITY_OPERATION", "TENANT_LEASE", "LEASE_OR_COLOCATION"].includes(rel) || group === "kr_construction" || group === "kr_operator") {
    return "매출·수주 영향";
  }
  if (rel === "ARRANGER") return "영향 규모 판단 불가";
  return "상환·차환 부담 증가";
}

function defaultAssessment(opts: {
  contingent: boolean; quantified: boolean; isSpv: boolean; hasAmount: boolean;
}): PfDefaultAssessment {
  if (opts.isSpv) return "프로젝트 SPC 스트레스 (모회사 자동부도 아님)";
  if (opts.contingent) return "조건부 의무 — 발동 조건 충족 시에만";
  if (opts.quantified) return "정량 스트레스 계산 가능 (부도 판정 아님)";
  if (!opts.hasAmount) return "영향 확인 / 부도위험 판단 자료 부족";
  return "영향 확인 / 부도위험 판단 자료 부족";
}

function buildAffectedCompanies(
  net: Network,
  projectsFile: PfProjectsFile,
  byProject: Map<string, PfProjectStress>,
  impactEdges: Array<{ edgeId: string; companyId: string; projectId: string; contingent: boolean }>,
  nodeLevels: Record<string, { level: StressLevel; intensity: number; label: string; category: Category; reason: string }>,
  assessments: Record<string, Assessment & { exposure_class?: string }>,
  form: PfShockForm,
): PfAffectedCompany[] {
  const nodeById = new Map(net.nodes.map((n) => [n.id, n]));
  const edgeById = new Map(net.edges.map((e) => [e.id, e]));
  const projById = new Map(projectsFile.projects.map((p) => [p.id, p]));
  const byCompany = new Map<string, typeof impactEdges>();

  for (const row of impactEdges) {
    if (!byCompany.has(row.companyId)) byCompany.set(row.companyId, []);
    byCompany.get(row.companyId)!.push(row);
  }
  // Also include stressed KR companies that appear in nodeLevels via EPC/sector without impactEdges
  for (const [id, st] of Object.entries(nodeLevels)) {
    if (st.level === "normal") continue;
    const n = nodeById.get(id);
    if (!n || (n as { region?: string }).region !== "KR") continue;
    if (byCompany.has(id)) continue;
    byCompany.set(id, []);
  }

  const out: PfAffectedCompany[] = [];
  for (const [companyId, rows] of byCompany) {
    const n = nodeById.get(companyId);
    if (!n) continue;
    const st = nodeLevels[companyId];
    if (!st || st.level === "normal") continue;

    const projects = rows.map((r) => {
      const e = edgeById.get(r.edgeId);
      const pr = projById.get(r.projectId);
      const xe = e as NetEdge & {
        amount_krw_eok?: number | null; amount_type?: string; obligation_trigger?: string;
        evidence_status?: string; source_url?: string; source_title?: string; project_name?: string;
      };
      return {
        project_id: r.projectId,
        project_name: xe?.project_name || pr?.name_ko || pr?.name || r.projectId,
        edge_id: r.edgeId,
        relationship_type: e?.relationship_type || "RELATED",
        exposure_label: REL_LABEL[e?.relationship_type || ""] || e?.label || e?.relationship_type || "관계",
        amount_note: e?.amount_note || "금액 미공개",
        amount_krw_eok: xe?.amount_krw_eok ?? null,
        amount_type: xe?.amount_type || null,
        contingent: r.contingent,
        obligation_trigger: xe?.obligation_trigger || e?.explanation || "",
        evidence_status: xe?.evidence_status || e?.source_status || "UNKNOWN",
        source_url: xe?.source_url || null,
        source_title: xe?.source_title || null,
      };
    });

    // Deduplicate same edge/loan
    const seen = new Set<string>();
    const deduped = projects.filter((p) => {
      const key = `${p.edge_id}|${p.amount_type}|${p.amount_krw_eok}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    const primaryRel = deduped[0]?.relationship_type || "";
    const contingent = deduped.some((p) => p.contingent);
    const hasAmount = deduped.some((p) => p.amount_krw_eok != null);
    const ps = deduped.map((p) => byProject.get(p.project_id)).find(Boolean);
    const impact_category = classifyImpact(primaryRel, contingent, n.group);
    const isSpv = n.entity_type === "spv" || n.group === "project_finance";
    const hop = st.label.includes("sector") || st.label.includes("funding") ? 2 : 1;
    const pathParts = [
      form.coreweaveDistress !== "normal" ? `CoreWeave ${form.coreweaveDistress}` : null,
      form.hyperscalerCapexPct < 0 ? `AI CAPEX ${form.hyperscalerCapexPct}%` : null,
      form.rateBp > 0 || form.krRateBp > 0 ? `금리 +${form.rateBp}/${form.krRateBp}bp` : null,
      deduped[0] ? `${deduped[0].project_name} · ${deduped[0].exposure_label}` : st.reason,
      displayName(n),
    ].filter(Boolean);

    const a: PfAffectedCompany = {
      company_id: companyId,
      company_name: displayName(n),
      role: n.role || n.entity_type,
      impact_category,
      directness: hop === 1 && deduped.length ? "direct" : "indirect",
      hop,
      projects: deduped,
      transmission_path: pathParts.join(" → "),
      baseline_vs_scenario: isSpv && ps?.interest_delta_usd_m != null
        ? `기준(+0bp) 대비 이자·DSCR 시나리오 변화 (Δ이자 ${ps.interest_delta_usd_m} USD m)`
        : "기준(추가 충격 없음) 대비 관계·자금경로 스트레스 — 금액 증분은 자료 범위 내만 표시",
      default_assessment: defaultAssessment({
        contingent, quantified: !!ps?.quantified, isSpv, hasAmount,
      }),
      explanation_ko: [
        `${displayName(n)}은(는) ${impact_category} 범주로 분류됩니다.`,
        deduped.length
          ? `관련 사업 ${deduped.length}건: ${deduped.map((p) => p.project_name).slice(0, 3).join(", ")}.`
          : `검증된 사업 엣지보다 섹터·자금시장 경로로 표시됩니다.`,
        contingent
          ? "보증·인수확약·책임준공은 발동 조건이 충족될 때만 현금 부담이 됩니다."
          : "프로젝트 문제는 참여 기업의 자동 부도를 의미하지 않습니다.",
        !hasAmount && deduped.length ? "기관별 금액이 미공개라 손실액을 산정하지 않습니다." : "",
      ].filter(Boolean).join(" "),
      assumptions: [
        ...(assessments[companyId]?.needed ? [`필요 자료: ${assessments[companyId].needed}`] : []),
        "시나리오는 현재(+0bp·추가충격 없음) 기준과 비교합니다.",
      ],
      missing: [
        ...(hasAmount ? [] : ["기관별 현재 잔액 미확인"]),
        ...(!ps?.quantified && isSpv ? ["CFADS·DSCR 미공시"] : []),
      ],
      evidence_confidence: (deduped[0]?.evidence_status as PfAffectedCompany["evidence_confidence"])
        || (n.source_status as PfAffectedCompany["evidence_confidence"])
        || "UNKNOWN",
    };
    out.push(a);
  }

  const order: PfImpactCategory[] = [
    "상환·차환 부담 증가", "보증·추가 자금부담 가능", "대출·투자금 손실 가능", "매출·수주 영향", "영향 규모 판단 불가",
  ];
  out.sort((a, b) => order.indexOf(a.impact_category) - order.indexOf(b.impact_category)
    || a.company_name.localeCompare(b.company_name, "ko"));
  return out;
}

function exposureClass(n: { pf_exposure_class?: string; key_drivers?: string[] }): string {
  return n.pf_exposure_class || (n.key_drivers || [])[0] || "";
}

function clamp01(x: number) { return Math.max(0, Math.min(1, x)); }

function stressFromDscr(dscr: number | null, hasQuant: boolean): { level: StressLevel; intensity: number } {
  if (!hasQuant || dscr === null || !Number.isFinite(dscr)) return { level: "insufficient", intensity: 0 };
  if (dscr >= 1.35) return { level: "normal", intensity: 0 };
  if (dscr >= 1.15) return { level: "moderate", intensity: 0.35 };
  if (dscr >= 1.0) return { level: "high", intensity: 0.65 };
  return { level: "critical", intensity: 0.92 };
}

function mergeLevel(a: StressLevel, b: StressLevel): StressLevel {
  const rank: Record<StressLevel, number> = {
    normal: 0, not_applicable: 0, insufficient: 1, moderate: 2, high: 3, critical: 4,
  };
  return rank[b] > rank[a] ? b : a;
}

function effectiveKrBp(form: PfShockForm): number {
  if (form.krRateLinkPct > 0) {
    return form.krRateBp + form.rateBp * clamp01(form.krRateLinkPct);
  }
  return form.krRateBp;
}

function projectInterestDelta(p: PfProject, rateBp: number, krBp: number): {
  delta: number | null; baselineDs: number | null; stressedDs: number | null; reasons: string[]; quantified: boolean;
} {
  const reasons: string[] = [];
  const bp = (p.region === "KR" || p.country === "KR") ? krBp : rateBp;
  const floatP = p.floating_debt_usd_m ?? 0;
  const fixedP = p.fixed_debt_usd_m ?? (p.debt_rate_type === "fixed" ? (p.senior_debt_usd_m ?? 0) : 0);
  const baselineCoupon = p.debt_interest_rate_pct;

  let baselineDs = p.baseline_debt_service_usd_m ?? null;
  if (baselineDs === null && baselineCoupon != null && (p.senior_debt_usd_m ?? 0) > 0) {
    baselineDs = (p.senior_debt_usd_m as number) * (baselineCoupon / 100);
    reasons.push("Debt service approximated as coupon × senior face (interest-only proxy; amortization not modeled).");
  }

  if (bp === 0) {
    return { delta: 0, baselineDs, stressedDs: baselineDs, reasons, quantified: floatP > 0 || (fixedP > 0 && baselineDs != null) };
  }

  // Floating: apply full bp to floating balance (ASSUMED if spread unknown)
  let delta = 0;
  let quantified = false;
  if (floatP > 0) {
    delta += floatP * (bp / 10000);
    quantified = true;
    reasons.push(`Floating / construction debt ${floatP} USD m × ${bp}bp (ASSUMED all-in if spread undisclosed; hedges UNKNOWN).`);
  }
  if (fixedP > 0 && bp !== 0) {
    reasons.push(`Fixed-rate debt ${fixedP} USD m: coupon unchanged until refinance — no automatic +${bp}bp on fixed notes.`);
  }
  if (floatP <= 0 && fixedP <= 0 && (p.senior_debt_usd_m == null)) {
    reasons.push("Insufficient disclosed debt balances for interest sensitivity.");
    return { delta: null, baselineDs, stressedDs: null, reasons, quantified: false };
  }

  const stressedDs = baselineDs != null && delta != null ? baselineDs + (delta || 0) : (delta != null && delta > 0 ? delta : null);
  return { delta: quantified ? delta : null, baselineDs, stressedDs, reasons, quantified };
}

function stressProject(p: PfProject, form: PfShockForm): PfProjectStress {
  const rateBp = form.rateBp;
  const krBp = effectiveKrBp(form);
  const { delta, baselineDs, stressedDs, reasons, quantified: rateQ } = projectInterestDelta(p, rateBp, krBp);
  const missing = [...(p.missing || [])];

  let baselineDscr = p.baseline_dscr ?? null;
  let stressedDscr: number | null = null;
  let dscrDelta: number | null = null;
  let level: StressLevel = "insufficient";
  let intensity = 0;
  let quant = false;

  if (p.baseline_cfads_usd_m != null && stressedDs != null && stressedDs > 0) {
    baselineDscr = p.baseline_cfads_usd_m / (baselineDs && baselineDs > 0 ? baselineDs : stressedDs);
    stressedDscr = p.baseline_cfads_usd_m / stressedDs;
    dscrDelta = stressedDscr - (baselineDscr ?? stressedDscr);
    const s = stressFromDscr(stressedDscr, true);
    level = s.level; intensity = s.intensity; quant = true;
  } else if (rateQ && delta != null && delta > 0) {
    // No CFADS — use interest delta vs debt size as proxy stress (labeled insufficient for DSCR)
    const face = (p.floating_debt_usd_m || 0) + (p.fixed_debt_usd_m || 0) || (p.senior_debt_usd_m || 1);
    const score = delta / face;
    if (score >= 0.05) { level = "high"; intensity = 0.7; }
    else if (score >= 0.02) { level = "moderate"; intensity = 0.4; }
    else { level = "moderate"; intensity = 0.25; }
    reasons.push("DSCR not computable (CFADS undisclosed). Stress band uses interest-delta / debt face proxy — not a covenant breach.");
    quant = true;
    missing.push("CFADS for true DSCR");
  } else if (!rateQ && form.gpuRentPct === 0 && form.hyperscalerCapexPct === 0) {
    level = "normal"; intensity = 0;
  }

  // GPU rent — only direct operator exposure gets assumed revenue hit; leases protected
  let gpuImpact: PfProjectStress["gpu_revenue_impact"] = "none";
  if (form.gpuRentPct < 0) {
    if (p.gpu_rent_exposure === "gpu_cloud_operator" || p.gpu_rent_exposure === "owner_operator_cloud") {
      gpuImpact = "assumed_operator";
      const pass = clamp01(form.gpuOperatorMarginPassThrough);
      const hit = Math.abs(form.gpuRentPct) / 100 * pass;
      if (hit >= 0.2) { level = mergeLevel(level, "high"); intensity = Math.max(intensity, 0.55 + hit * 0.3); }
      else if (hit >= 0.08) { level = mergeLevel(level, "moderate"); intensity = Math.max(intensity, 0.35); }
      reasons.push(`GPU rental ${form.gpuRentPct}% with ASSUMED operator margin pass-through ${Math.round(pass * 100)}% — not equal to lease rate cut.`);
      quant = true;
    } else if (p.gpu_rent_exposure === "indirect_tenant" || (p.gpu_rent_pass_through_pct ?? 0) === 0) {
      gpuImpact = "lease_protected";
      reasons.push("Long-term lease / hosting: GPU rental decline does not auto-reduce contracted project revenue.");
      // Second-order: future demand only if combined with CAPEX cut
      if (form.hyperscalerCapexPct <= -20 && form.restrictNewFinancing) {
        level = mergeLevel(level, "moderate");
        intensity = Math.max(intensity, 0.3);
        reasons.push("Second-order: weak GPU economics + CAPEX cut may slow expansion / refinancing appetite (qualitative).");
      }
    } else {
      gpuImpact = "insufficient";
      reasons.push("GPU exposure path insufficiently disclosed.");
    }
  }

  // Stabilized operating colocation (e.g. Bundang Hostway) ≠ development PF hub.
  // Do NOT treat permit "completed" buildings as immune operating assets — only explicit markers.
  const isOperatingAsset =
    p.construction_stage === "stabilized_operating"
    || (p as { shock_role?: string }).shock_role === "operating_colocation_not_pf_hub"
    || p.hyperscaler_capex_exposure === "none_operating_asset"
    || p.id === "bundang_hostway_idc";

  let capexImpact: PfProjectStress["capex_demand_impact"] = "none";
  if (form.hyperscalerCapexPct < 0) {
    const e = clamp01(form.capexDemandElasticity);
    if (isOperatingAsset) {
      capexImpact = "none";
      // Keep stress at normal for CW/CAPEX — Hostway must not become the KR contagion sink
      level = "normal";
      intensity = 0;
      reasons.push("Stabilized operating colocation: CAPEX/CW demand shock does not auto-stress lease-backed ops. Not a Korean PF hub.");
    } else if (
      p.hyperscaler_capex_exposure === "demand_for_future_phases"
      || p.hyperscaler_capex_exposure === "future_permit_pipeline"
      || p.hyperscaler_capex_exposure === "domestic_demand_and_refi"
      || p.hyperscaler_capex_exposure === "domestic_cloud_demand"
      || p.construction_stage === "under_construction"
      || p.construction_stage === "planned"
      || p.construction_stage === "pre_construction"
      || p.construction_stage === "expanding"
    ) {
      capexImpact = p.construction_stage === "under_construction" ? "construction_funding" : "future_phases";
      const sev = Math.abs(form.hyperscalerCapexPct) / 100 * e;
      // Permit-only pipeline (no financing disclosure): qualitative only, lighter intensity
      const permitOnly = String(p.id).startsWith("kr_permit_") || (p as { financing_disclosed?: boolean }).financing_disclosed === false;
      if (permitOnly) {
        level = mergeLevel(level, "moderate");
        intensity = Math.max(intensity, Math.min(0.28, 0.12 + sev * 0.25));
        reasons.push(`Permit/development pipeline under CAPEX ${form.hyperscalerCapexPct}% — qualitative demand only; no disclosed PF to impair.`);
      } else if (form.restrictNewFinancing || sev >= 0.25) {
        level = mergeLevel(level, sev >= 0.35 ? "high" : "moderate");
        intensity = Math.max(intensity, 0.3 + sev * 0.4);
        reasons.push(`Hyperscaler AI CAPEX ${form.hyperscalerCapexPct}% with ASSUMED demand elasticity ${Math.round(e * 100)}% — future starts / leasing demand; not automatic lease cancel.`);
      } else {
        level = mergeLevel(level, "moderate");
        intensity = Math.max(intensity, 0.2);
        reasons.push(`Hyperscaler AI CAPEX ${form.hyperscalerCapexPct}% — moderate pipeline sensitivity.`);
      }
    } else {
      capexImpact = "qualitative";
      reasons.push("CAPEX reduction: qualitative demand channel only for this project.");
    }
  }

  // Construction liquidity gap: interest during construction on floating draws (proxy)
  let liqGap: number | null = null;
  if (delta != null && delta > 0 && (p.construction_stage === "under_construction" || p.construction_stage === "planned")) {
    liqGap = delta * (form.horizonMonths / 12);
    if (liqGap > 0 && (p.committed_construction_financing_usd_m == null || form.restrictNewFinancing)) {
      level = mergeLevel(level, form.restrictNewFinancing ? "high" : "moderate");
      intensity = Math.max(intensity, form.restrictNewFinancing ? 0.6 : 0.35);
      reasons.push(`Modeled IDC / interest pressure over ${form.horizonMonths}m ≈ ${liqGap.toFixed(1)} USD m (potential funding need — not automatic default).`);
    }
  }

  if (!quant && level === "insufficient" && (form.rateBp !== 0 || form.gpuRentPct !== 0 || form.hyperscalerCapexPct !== 0 || (form.coreweaveDistress && form.coreweaveDistress !== "normal"))) {
    reasons.push("Stress visible only qualitatively — key project cash-flow inputs missing.");
  }
  // Reset only when ALL primary + secondary shocks are idle (include CoreWeave).
  const cwIdle = !form.coreweaveDistress || form.coreweaveDistress === "normal";
  if (cwIdle && form.rateBp === 0 && form.gpuRentPct === 0 && form.hyperscalerCapexPct === 0 && effectiveKrBp(form) === 0 && !form.restrictNewFinancing) {
    level = "normal"; intensity = 0;
  }
  // Hostway / stabilized ops: only rate-driven quantitative stress may remain; strip sector contagion
  if (isOperatingAsset) {
    const rateOnly = rateQ && delta != null && delta > 0;
    if (!rateOnly) {
      level = "normal";
      intensity = 0;
    } else {
      intensity = Math.min(intensity, 0.35);
      if (level === "high" || level === "critical") level = "moderate";
      reasons.push("Operating-asset: rate sensitivity only — not a default CW/CAPEX contagion path.");
    }
  }

  return {
    project_id: p.id,
    name: p.name,
    region: p.region || p.country || "US",
    level,
    intensity: clamp01(intensity),
    baseline_dscr: baselineDscr,
    stressed_dscr: stressedDscr,
    dscr_delta: dscrDelta,
    interest_delta_usd_m: delta,
    debt_service_baseline_usd_m: baselineDs,
    debt_service_stressed_usd_m: stressedDs,
    liquidity_gap_usd_m: liqGap,
    gpu_revenue_impact: gpuImpact,
    capex_demand_impact: capexImpact,
    quantified: quant,
    qualitative: !quant && level !== "normal",
    reasons,
    missing,
    source_ids: p.source_ids || [],
  };
}

function edgeClass(e: NetEdge): string {
  return (e as NetEdge & { transmission_class?: string }).transmission_class || "direct_contract";
}

function buildUsKoreaPaths(net: Network): PfShockResult["pf"]["us_korea_paths"] {
  const region = new Map(net.nodes.map((n) => [n.id, (n as { region?: string }).region || "US"]));
  const out: PfShockResult["pf"]["us_korea_paths"] = [];
  for (const e of net.edges) {
    const rs = region.get(e.source);
    const rt = region.get(e.target);
    if ((rs === "US" && rt === "KR") || (rs === "KR" && rt === "US")) {
      out.push({
        from: e.source, to: e.target, edge_id: e.id,
        transmission_class: edgeClass(e),
        explanation: e.explanation,
      });
    }
  }
  // Also KR equipment → US project edges already covered; KR domestic linked to US via sector
  return out;
}

export function simulatePfShock(net: Network, projectsFile: PfProjectsFile, form: PfShockForm): PfShockResult {
  const projects = projectsFile.projects.map((p) => stressProject(p, form));
  const byProject = new Map(projects.map((p) => [p.project_id, p]));

  const nodeLevels: Record<string, { level: StressLevel; intensity: number; label: string; category: Category; reason: string }> = {};
  const setNode = (id: string, level: StressLevel, intensity: number, label: string, category: Category, reason: string) => {
    const prev = nodeLevels[id];
    if (!prev) {
      nodeLevels[id] = { level, intensity, label, category, reason };
      return;
    }
    const useNew = intensity >= prev.intensity;
    nodeLevels[id] = {
      level: mergeLevel(prev.level, level),
      intensity: Math.max(prev.intensity, intensity),
      label: useNew ? label : prev.label,
      category: prev.category === "computed" || category === "computed" ? "computed" : category,
      reason: useNew ? reason : prev.reason,
    };
  };

  const cw = cwStress(form);
  const nodeById = new Map(net.nodes.map((n) => [n.id, n]));

  // ---- Stage 0/1 primary: CoreWeave distress ----
  if (cw.rank > 0) {
    setNode("coreweave", cw.level, cw.intensity, "cw_distress", "assumed",
      `Primary shock A: CoreWeave ${form.coreweaveDistress} (modeled — not a legal finding)`);
    // US landlords / SPVs with CoreWeave lease credit support
    for (const e of net.edges) {
      if (!(e.source === "coreweave" || e.target === "coreweave")) continue;
      const other = e.source === "coreweave" ? e.target : e.source;
      if (!US_LANDLORDS.has(other) && e.relationship_type !== "TENANT_LEASE" && e.relationship_type !== "LESSOR") continue;
      const sev = cw.rank >= 3 ? "high" : cw.rank >= 2 ? "high" : "moderate";
      const inten = cw.intensity * (cw.rank >= 3 ? 0.85 : 0.55);
      setNode(other, sev as StressLevel, inten, "cw_lease_credit", "relationship_only",
        `CoreWeave is tenant/offtake credit support — distress may impair lease-backed US DC projects (not automatic SPV default)`);
    }
  }

  // ---- Primary B: hyperscaler CAPEX (also applied inside stressProject) ----
  // Stage 1: projects + GPU operators
  for (const ps of projects) {
    setNode(ps.project_id, ps.level, ps.intensity, ps.level, ps.quantified ? "computed" : "relationship_only", ps.reasons[0] || "");
    const proj = projectsFile.projects.find((x) => x.id === ps.project_id);
    if (proj?.spv) setNode(proj.spv, ps.level, ps.intensity * 0.95, ps.level, ps.quantified ? "computed" : "relationship_only", "SPV linked to project stress");
    if (proj?.developer) setNode(proj.developer, mergeLevel("moderate", ps.level === "critical" ? "high" : ps.level), ps.intensity * 0.55, "sponsor", "relationship_only", "Sponsor / developer — not automatic parent default");
  }

  if (form.gpuRentPct < 0) {
    const pass = clamp01(form.gpuOperatorMarginPassThrough);
    const hit = Math.abs(form.gpuRentPct) / 100 * pass;
    const lvl: StressLevel = hit >= 0.25 ? "high" : "moderate";
    for (const id of GPU_OPERATORS) {
      if (nodeById.has(id)) {
        setNode(id, lvl, clamp01(0.3 + hit), "gpu_rent", "assumed", `ASSUMED GPU rental pass-through ${Math.round(pass * 100)}% on operator margins`);
      }
    }
  }

  // Stage 2: lenders / financial counterparties on stressed projects (US + KR verified)
  const stressedProjects = new Set(projects.filter((p) => p.level === "high" || p.level === "critical" || p.level === "moderate").map((p) => p.project_id));
  // Also treat US SPVs stressed by CoreWeave as stressed project nodes
  for (const id of Object.keys(nodeLevels)) {
    if (US_LANDLORDS.has(id) && (nodeLevels[id].level === "high" || nodeLevels[id].level === "critical" || nodeLevels[id].level === "moderate")) {
      stressedProjects.add(id);
    }
  }
  // Map project id ↔ borrower SPV so lender edges (attached to SPV, not project id) receive stress
  const stressAnchor = new Map<string, string>();
  for (const pid of stressedProjects) {
    stressAnchor.set(pid, pid);
    const pr = projectsFile.projects.find((x) => x.id === pid);
    const spv = (pr as { borrower?: string | null } | undefined)?.borrower || pr?.spv;
    if (spv) stressAnchor.set(spv, pid);
  }
  // Historical / terminated — never propagate current credit loss
  const PAST_REL = new Set([
    "repaid", "terminated", "historical", "withdrawn", "expired", "refinanced", "transferred",
    "FULLY_REPAID", "REFINANCED", "TRANSFERRED", "EXPIRED", "HISTORICAL_ONLY", "SECURITIZED",
  ]);
  // Roles that are informational only — arrangement ≠ retained exposure
  const NON_LOSS_REL = new Set([
    "ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT", "ASSET_MANAGER",
    "TRUST_SERVICES", "PRIORITY_BENEFICIARY", "SUPPLIER", "CUSTOMER", "SECTOR_SUPPLY",
    "STRATEGIC_PARTNERSHIP", "PARENT_SPV", "PARENT_AFFILIATE", "ASSET_SALE", "ABS_SPONSOR",
    "HISTORICAL_FINANCING",
  ]);
  const NON_LOSS_AMT = new Set(["facility_total_context", "fee_paid", "underwrite_commitment"]);
  const LOSS_REL = new Set([
    "PROJECT_LOAN", "ACQUISITION_LOAN", "CORPORATE_LOAN", "BRIDGE_LOAN", "MORTGAGE_LOAN",
    "DIRECT_LOAN", "PROJECT_FINANCE_LOAN", "EQUITY_INVESTMENT", "EQUITY_SPONSOR",
    "PREFERRED_EQUITY", "SHAREHOLDER_LOAN", "SUBORDINATED_INVESTMENT", "ABS_HOLDING",
    "CREDIT_ENHANCEMENT", "COMPLETION_GUARANTEE", "DEBT_ASSUMPTION", "LOAN_GUARANTEE",
    "FINANCIAL_GUARANTEE", "LIQUIDITY_COMMITMENT", "REFINANCING_UNDERWRITE", "SHARE_PLEDGE",
  ]);
  const impactEdges: Array<{ edgeId: string; companyId: string; projectId: string; contingent: boolean }> = [];
  for (const e of net.edges) {
    const x = e as NetEdge & {
      relationship_status?: string; exposure_status?: string; layer?: string;
      project_id?: string; contingent_obligation?: boolean; amount_type?: string;
      shock_eligible?: boolean;
    };
    if (x.shock_eligible === false) continue;
    if (NON_LOSS_REL.has(e.relationship_type)) continue;
    if (!LOSS_REL.has(e.relationship_type)
      && e.impact_channel !== "financial"
      && e.relationship_type !== "CREDIT_ENHANCEMENT") {
      continue;
    }
    const relSt = (x.exposure_status || x.relationship_status || "").toUpperCase();
    const relStLower = (x.exposure_status || x.relationship_status || "").toLowerCase();
    if (PAST_REL.has(x.relationship_status || "") || PAST_REL.has(x.exposure_status || "")
      || PAST_REL.has(relSt) || PAST_REL.has(relStLower) || x.layer === "scenario") continue;
    if (NON_LOSS_AMT.has(x.amount_type || "")) continue;
    // Unverified historical edges: mark in dossier but do not create verified-loss paths
    if (relSt === "UNVERIFIED" || relStLower === "unverified") continue;
    const srcHit = stressAnchor.has(e.source);
    const tgtHit = stressAnchor.has(e.target);
    if (!srcHit && !tgtHit) continue;
    const anchorPid = stressAnchor.get(srcHit ? e.source : e.target)!;
    if (x.project_id && x.project_id !== anchorPid && !stressedProjects.has(x.project_id)) continue;
    const other = srcHit ? e.target : e.source;
    if (stressAnchor.has(other)) continue;
    const ps = byProject.get(x.project_id && byProject.has(x.project_id) ? x.project_id : anchorPid);
    const baseInt = ps?.intensity || nodeLevels[srcHit ? e.source : e.target]?.intensity || 0.3;
    const isEnhance = e.relationship_type === "CREDIT_ENHANCEMENT" || e.relationship_type === "REFINANCING_UNDERWRITE"
      || e.relationship_type === "COMPLETION_GUARANTEE" || e.relationship_type === "DEBT_ASSUMPTION" || e.relationship_type === "LOAN_GUARANTEE"
      || e.relationship_type === "FINANCIAL_GUARANTEE" || e.relationship_type === "LIQUIDITY_COMMITMENT"
      || !!x.contingent_obligation;
    const lvl: StressLevel = (ps?.level === "critical" || cw.rank >= 3) && isEnhance ? "high" : "moderate";
    // Short labels only — long explanations live in the compact SHOCK panel on demand
    setNode(other, lvl, baseInt * (isEnhance ? 0.55 : 0.4), isEnhance ? "보증·확약" : "대출·출자", "relationship_only",
      isEnhance
        ? `조건부 신용보강·보증 — 발동 시에만 현금 부담 (${edgeClass(e)})`
        : `검증된 금융 익스포저 — LGD 미계량 (${edgeClass(e)})`);
    impactEdges.push({ edgeId: e.id, companyId: other, projectId: x.project_id || anchorPid, contingent: isEnhance });
  }

  // Stage 3: Korean EPC / equipment — CAPEX path + verified domestic EPC on stressed KR projects
  if (form.hyperscalerCapexPct <= -10 || form.restrictNewFinancing || cw.rank >= 2) {
    const sev = Math.abs(form.hyperscalerCapexPct) / 100 * clamp01(form.capexDemandElasticity)
      + (cw.rank >= 2 ? 0.1 * clamp01(form.cwKrFundingPassThrough) : 0);
    for (const n of net.nodes) {
      if (n.group !== "kr_construction" && !KR_EQUIPMENT.has(n.id)) continue;
      const exp = exposureClass(n as { pf_exposure_class?: string; key_drivers?: string[] });
      if (exp === "research_candidate") continue;
      const epcEdges = net.edges.filter((e) =>
        (e.source === n.id || e.target === n.id) && e.relationship_type === "EPC_CONTRACT" && e.source_status === "VERIFIED");
      const touchesStressed = epcEdges.some((e) => stressedProjects.has(e.source) || stressedProjects.has(e.target)
        || projectsFile.projects.some((p) => (p.id === e.source || p.id === e.target || p.spv === e.source || p.spv === e.target)
          && stressedProjects.has(p.id)));
      if (epcEdges.length && touchesStressed) {
        setNode(n.id, "moderate", clamp01(0.35 + sev * 0.35), "kr_epc_verified", "relationship_only",
          "Verified Korean EPC/completion-guarantee on domestic DC project — construction receivables / contingent completion risk (not US SPV bilateral)");
      } else if (exp === "sector_sensitivity" || exp === "general_pf" || KR_EQUIPMENT.has(n.id)) {
        setNode(n.id, "moderate", clamp01(0.2 + sev * 0.35), "sector_kr", "relationship_only",
          "Korean EPC/equipment: sector demand sensitivity (class B/C) — not a confirmed US SPV contract loss");
      }
    }
  }

  // Stage 4: only ASSUMED funding_market edges that remain (no aggregate hub node).
  // Company-only map: do not invent a “KR PF market” sink.
  const fundingOn = cw.rank >= 2 || form.restrictNewFinancing || effectiveKrBp(form) >= 100 || form.rateBp >= 300;
  if (fundingOn) {
    const pass = clamp01(form.cwKrFundingPassThrough) * (cw.rank / 4);
    for (const e of net.edges) {
      if (edgeClass(e) !== "funding_market") continue;
      // Skip historical / unverified fabricated hubs
      if ((e as { relationship_status?: string }).relationship_status === "historical") continue;
      for (const id of [e.source, e.target]) {
        if (id === "coreweave") continue;
        if (!nodeById.has(id)) continue;
        setNode(id, "moderate", clamp01(0.18 + pass * 0.4), "funding_market", "assumed",
          "Funding-market / refinancing sentiment (class C) via explicit edge — not automatic institutional default");
      }
    }
  }

  // Stage 5: Level-3 sector channel for general_pf financials ONLY when funding stress is on
  // and they have no verified project bilateral edge. Not used as quantified loss.
  if (fundingOn && (form.restrictNewFinancing || cw.rank >= 3)) {
    for (const n of net.nodes) {
      if (!isKrFinGroup(n.group)) continue;
      const exp = exposureClass(n as { pf_exposure_class?: string; key_drivers?: string[] });
      if (exp === "confirmed_aidc_project" || exp === "confirmed_dc_finance") continue;
      if (exp === "general_pf" && !nodeLevels[n.id]) {
        const hasVerifiedFin = net.edges.some((e) =>
          (e.source === n.id || e.target === n.id)
          && e.source_status === "VERIFIED"
          && (e.impact_channel === "financial" || ["PROJECT_LOAN", "CREDIT_ENHANCEMENT", "EQUITY_INVESTMENT"].includes(e.relationship_type))
          && e.relationship_type !== "ARRANGER");
        if (hasVerifiedFin) continue;
        setNode(n.id, "moderate", 0.1, "sector_lending_capacity", "assumed",
          "Level-3 sector channel only — no verified bilateral DC PF edge; not a fabricated Hostway/project link");
      }
    }
  }

  // Semiconductor HBM: qualitative only under GPU+CAPEX combined
  if (form.gpuRentPct <= -30 && form.hyperscalerCapexPct <= -20) {
    for (const id of ["sk_hynix", "samsung", "nvidia"]) {
      if (nodeById.has(id)) {
        setNode(id, "moderate", 0.28, "hbm_demand", "relationship_only",
          "Qualitative: weaker AI infra cycle may slow accelerator/HBM demand — not equal to GPU rental %");
      }
    }
  }

  const assessments: Record<string, Assessment & { exposure_class?: string; channels?: string[]; mechanism?: string }> = {};
  for (const [id, st] of Object.entries(nodeLevels)) {
    assessments[id] = {
      category: st.category,
      relation: { kind: "direct", path: null, direct_edges: [] },
      values: [],
      reason: st.reason,
      needed: st.level === "insufficient" ? "project CFADS / covenants" : null,
      exposure_class: st.category === "computed" ? "measurable" : "potential_indirect",
      mechanism: st.label,
    };
  }

  const ns = (id: string): NodeState => {
    const st = nodeLevels[id];
    if (!st) return { status: "normal", label: "normal", category: "unconfirmed", intensity: 0, stress: "normal" };
    const status = st.level === "critical" ? "critical" : st.level === "high" ? "high" : st.level === "moderate" ? "elevated" : st.level === "insufficient" ? "unknown" : "normal";
    return { status, label: st.label, category: st.category, intensity: st.intensity, stress: st.level };
  };

  const activeFor = (pred: (id: string) => boolean) =>
    net.edges.filter((e) => pred(e.source) || pred(e.target)).map((e) => e.id);

  const round = (stage: number, title: string, title_ko: string, lines: string[], ids: string[], edgePred: (id: string) => boolean): RefiRound => ({
    round: stage, stage, title, title_ko, lines,
    active_edges: activeFor(edgePred),
    node_states: Object.fromEntries(ids.map((id) => [id, ns(id)])),
  });

  const allStressed = Object.keys(nodeLevels).filter((id) => nodeLevels[id].level !== "normal" && nodeLevels[id].level !== "not_applicable");
  const projIds = projects.map((p) => p.project_id);
  const stage1 = allStressed.filter((id) => id === "coreweave" || GPU_OPERATORS.has(id) || US_LANDLORDS.has(id) || projIds.includes(id) || net.nodes.find((n) => n.id === id)?.entity_type === "spv" || net.nodes.find((n) => n.id === id)?.entity_type === "project");
  const stage2 = allStressed.filter((id) => {
    const g = net.nodes.find((n) => n.id === id)?.group || "";
    return g === "financial" || g === "kr_securities" || g === "kr_bank" || g === "kr_savings" || g === "kr_insurance" || g === "kr_am" || g === "kr_trust";
  }).filter((id) => !stage1.includes(id));
  const stage3 = allStressed.filter((id) => {
    const g = net.nodes.find((n) => n.id === id)?.group || "";
    return g === "kr_construction" || g === "kr_operator" || KR_EQUIPMENT.has(id);
  }).filter((id) => !stage1.includes(id) && !stage2.includes(id));
  const stage4 = allStressed.filter((id) => net.nodes.find((n) => n.id === id)?.group === "kr_cooperative" || nodeLevels[id]?.label === "funding_market");
  const stage5 = allStressed.filter((id) => {
    const lab = nodeLevels[id]?.label || "";
    return lab === "lending_capacity" || lab === "sector_lending_capacity";
  });

  const rounds: RefiRound[] = [
    round(0, "Primary US shocks", "0단계 · 1차 충격 (CoreWeave · CAPEX)", [
      `CoreWeave: ${form.coreweaveDistress} · Big Tech AI CAPEX ${form.hyperscalerCapexPct}%`,
      `2차 변수: 금리 +${form.rateBp}bp · KR +${effectiveKrBp(form).toFixed(0)}bp · GPU ${form.gpuRentPct}%`,
      form.restrictNewFinancing ? "신규 프로젝트 금융 제한: ON" : "신규 PF 제한: OFF",
      "분석 단계이며 예측·확정 부도가 아닙니다.",
    ], [], () => false),
    round(1, "US infra & project stress", "1단계 · US 인프라·프로젝트", [
      `CoreWeave 및 임차 신용이 연결된 US DC/SPV`,
      `계량 프로젝트: ${projects.filter((p) => p.quantified && p.level !== "normal").length}`,
      "고정 임차 ≠ GPU 현물가 1:1",
    ], stage1, (id) => stage1.includes(id)),
    round(2, "Verified financial counterparties", "2단계 · 검증된 금융 상대방", [
      "대주·보증·인수확약 — 관계가 곧 전액 손실이 아닙니다.",
      `금융 노드: ${stage2.length}`,
    ], [...stage1, ...stage2], (id) => stage1.includes(id) || stage2.includes(id)),
    round(3, "Korean EPC / operators / equipment", "3단계 · 한국 EPC·운영·장비", [
      "검증 EPC(책임준공)와 섹터 수요(class B)를 구분합니다.",
      `한국 산업 노드: ${stage3.length}`,
    ], [...stage1, ...stage2, ...stage3], (id) => stage1.includes(id) || stage2.includes(id) || stage3.includes(id)),
    round(4, "Korean PF funding market", "4단계 · 한국 DC PF 자금시장", [
      `ASSUMED CW→KR 전가 ${Math.round((form.cwKrFundingPassThrough || 0) * 100)}% · 검증 크로스보더 여신 없음`,
      `자금시장·협동금융 노드: ${stage4.length}`,
    ], [...stage1, ...stage2, ...stage3, ...stage4], (id) => !stage5.includes(id) && allStressed.includes(id)),
    round(5, "Further lending capacity (conditional)", "5단계 · 추가 여신 여력(조건부)", [
      "Path E: 허브가 고스트레스일 때만 general_pf에 정성 압력 — 은행 간 허위 여신 없음",
      `추가 노드: ${stage5.length}`,
    ], allStressed, (id) => allStressed.includes(id)),
  ];

  const usKorea = buildUsKoreaPaths(net);
  const isBaseline = form.coreweaveDistress === "normal" && form.rateBp === 0 && form.krRateBp === 0
    && form.gpuRentPct === 0 && form.hyperscalerCapexPct === 0 && !form.restrictNewFinancing;
  const affectedCompanies = isBaseline
    ? []
    : buildAffectedCompanies(net, projectsFile, byProject, impactEdges, nodeLevels, assessments, form);
  const impactEdgeIds = [...new Set(affectedCompanies.flatMap((c) => c.projects.map((p) => p.edge_id)))];
  const measurable = projects.filter((p) => p.quantified).length;
  const dscrDet = projects.filter((p) => p.stressed_dscr != null && p.baseline_dscr != null && (p.stressed_dscr as number) < (p.baseline_dscr as number) - 0.01).length;
  const liq = projects.filter((p) => (p.liquidity_gap_usd_m || 0) > 0).length;
  const krVer = usKorea.filter((p) => p.transmission_class === "direct_contract").length;
  const krSec = usKorea.filter((p) => p.transmission_class === "sector_demand" || p.transmission_class === "funding_market").length;

  const totalDelta = projects.reduce((s, p) => s + (p.interest_delta_usd_m || 0), 0);
  const criticalN = Object.values(nodeLevels).filter((x) => x.level === "critical").length;
  const highN = Object.values(nodeLevels).filter((x) => x.level === "high" || x.level === "critical").length;

  const origin = form.coreweaveDistress !== "normal" ? "coreweave" : "helios_campus";
  const originStress = byProject.get(origin) || (origin === "coreweave" ? {
    project_id: "coreweave", name: "CoreWeave", region: "US", level: cw.level, intensity: cw.intensity,
    baseline_dscr: null, stressed_dscr: null, dscr_delta: null, interest_delta_usd_m: null,
    debt_service_baseline_usd_m: null, debt_service_stressed_usd_m: null, liquidity_gap_usd_m: null,
    gpu_revenue_impact: "assumed_operator" as const, capex_demand_impact: "none" as const,
    quantified: false, qualitative: cw.rank > 0, reasons: [`CoreWeave distress scenario: ${form.coreweaveDistress}`],
    missing: [], source_ids: [],
  } : undefined);

  return {
    mode: "RATE_SHOCK",
    origin,
    benchmark: {
      id: "pf_combined",
      label: "PF 복합 충격",
      label_en: "PF combined (rates / GPU rent / CAPEX)",
      plain: "프로젝트 금융 금리·GPU 임대료·하이퍼스케일러 CAPEX",
      applies_to: "project_finance",
    },
    params: { shock_bp: form.rateBp, benchmark: "sofr", sofr_pct: net.financials.market_inputs.sofr_pct },
    origin_stress: originStress ? {
      level: originStress.level,
      intensity: originStress.intensity,
      score_delta_over_ocf: null,
      baseline_interest_ann_usd_m: originStress.debt_service_baseline_usd_m,
      stressed_interest_ann_usd_m: originStress.debt_service_stressed_usd_m,
      annualized_ocf_usd_m: null,
      baseline_coverage: originStress.baseline_dscr,
      stressed_coverage: originStress.stressed_dscr,
      coverage_change: originStress.dscr_delta,
      delta_interest_usd_m: originStress.interest_delta_usd_m,
      floating_principal_usd_m: projectsFile.projects.find((p) => p.id === origin)?.floating_debt_usd_m ?? null,
      cash_usd_m: null,
      baseline_sofr_pct: net.financials.market_inputs.sofr_pct,
      stressed_sofr_pct: net.financials.market_inputs.sofr_pct + form.rateBp / 100,
      shock_bp: form.rateBp,
      critical_sofr_pct: null,
      critical_shock_bp: null,
      bp_to_critical: null,
      critical_trigger: null,
      metric_trigger: "project_dscr_or_interest_proxy",
      threshold_kind: "pf_scenario",
      assumptions: originStress.reasons,
      limitations: originStress.missing,
      source_ids: originStress.source_ids,
    } : null,
    summary: {
      network_companies: net.nodes.length,
      direct_measurable: measurable,
      potential_indirect: Object.keys(assessments).length - measurable,
      transmission_channels: net.edges.length,
      insufficient_data: projects.filter((p) => p.level === "insufficient").length,
      no_identified_exposure: net.nodes.length - allStressed.length,
      total_incremental_interest_usd_m: totalDelta || null,
      floating_sofr_principal_usd_m: projects.reduce((s, p) => s + (projectsFile.projects.find((x) => x.id === p.project_id)?.floating_debt_usd_m || 0), 0) || null,
      fixed_principal_usd_m: projects.reduce((s, p) => s + (projectsFile.projects.find((x) => x.id === p.project_id)?.fixed_debt_usd_m || 0), 0) || null,
      shock_bp: form.rateBp,
      benchmark: "pf_combined",
      stress_level: originStress?.level ?? null,
      companies_at_or_above_high: highN,
      companies_critical: criticalN,
      secondary_stressed: stage2.length,
      secondary_critical: stage2.filter((id) => nodeLevels[id]?.level === "critical").length,
      sector_stressed: stage3.length,
      sector_critical: 0,
      spv_critical: projects.filter((p) => p.level === "critical").length,
      order1: stage1.length,
      order2: stage2.length,
      order3_plus: stage3.length + stage4.length,
      quantified_contagion: measurable,
      qualitative_contagion: projects.filter((p) => p.qualitative).length + stage3.length,
      pathway_only: krSec,
      max_contagion_order: 5,
      crisis_mode: `cw:${form.coreweaveDistress}|capex:${form.hyperscalerCapexPct}`,
      baseline_sofr_pct: net.financials.market_inputs.sofr_pct,
      stressed_sofr_pct: net.financials.market_inputs.sofr_pct + form.rateBp / 100,
    },
    contagion: {
      max_order_reached: 5,
      counts: { order1: stage1.length, order2: stage2.length, order3: stage3.length, order4: stage4.length, order5: stage5.length },
      stopped_reason: "relationship_and_mechanism_exhausted",
      events: allStressed.map((id) => ({
        entity_id: id,
        order: stage1.includes(id) ? 1 : stage2.includes(id) ? 2 : stage3.includes(id) ? 3 : stage4.includes(id) ? 4 : 5,
        level: nodeLevels[id]?.level ?? null,
        impact_kind: assessments[id]?.exposure_class || "pathway",
        from_entity: form.coreweaveDistress !== "normal" ? "coreweave" : origin,
        mechanism: nodeLevels[id]?.label || "",
        reason: nodeLevels[id]?.reason || "",
      })),
    },
    instruments: net.financials.instruments.map((i) => ({
      id: i.id, name: i.name, rate_type: i.rate_type, principal_usd_m: i.principal_usd_m,
      exposure_class: i.rate_type === "floating" ? "floating_sensitive" : "fixed_coupon",
      annual_interest_delta_usd_m: i.rate_type === "floating" && i.principal_usd_m
        ? i.principal_usd_m * (form.rateBp / 10000) : 0,
      reason: i.rate_type === "fixed" ? "Fixed coupon unchanged" : "ASSUMED bp on floating / undisclosed spread",
      formula: i.rate_type === "floating" ? "principal × shock_bp / 10000" : null,
    })),
    rounds,
    assessments,
    formulas: [
      "ΔInterest_float ≈ floating_principal × shock_bp / 10000 (hedges UNKNOWN → no automatic offset)",
      "DSCR = CFADS / debt_service — only when CFADS disclosed",
      "GPU rent shock ≠ lease rate; pass-through only for gpu_cloud_operator with user ASSUMED margin share",
      "Hyperscaler CAPEX % × demand elasticity (ASSUMED) → future phases / order-book sensitivity",
    ],
    warnings: [
      "SPV distress ≠ parent bankruptcy",
      "DSCR < 1.0 is modeled covenant pressure, not confirmed legal default",
      "Korean sector edges are not fabricated bilateral losses",
    ],
    notes: [
      "PF engine is isolated from CoreWeave semiconductor rateShock calculations.",
      "US and Korean rate shocks are separate inputs unless the user sets an explicit linkage %.",
    ],
    result: {
      annual_interest_delta_usd_m: totalDelta,
      shock_bp: form.rateBp,
      rate_change_bp: form.rateBp,
      amount_usd_m: totalDelta,
    },
    instrument: { id: "pf_portfolio", name: "PF project portfolio" },
    existing_rate: { rate_pct: null, basis: "project", status: "mixed", formula: "per-project", fallback: false },
    comparison: [],
    schedule: [],
    reference: {},
    assumption_chain: {
      gpu_pass_through: form.gpuOperatorMarginPassThrough,
      capex_elasticity: form.capexDemandElasticity,
      kr_rate_link_pct: form.krRateLinkPct,
    },
    pf: {
      rate_bp: form.rateBp,
      kr_rate_bp: effectiveKrBp(form),
      gpu_rent_pct: form.gpuRentPct,
      hyperscaler_capex_pct: form.hyperscalerCapexPct,
      restrict_new_financing: form.restrictNewFinancing,
      coreweave_distress: form.coreweaveDistress,
      projects,
      measurable_projects: measurable,
      dscr_deterioration: dscrDet,
      liquidity_shortfalls: liq,
      korean_verified_exposure: krVer,
      korean_sector_sensitivity: krSec,
      us_korea_paths: usKorea,
      affected_companies: affectedCompanies,
      impact_edge_ids: impactEdgeIds,
      assumptions: [
        `CoreWeave distress = ${form.coreweaveDistress} (primary A)`,
        `Hyperscaler AI CAPEX ${form.hyperscalerCapexPct}% (primary B)`,
        `CW→KR funding pass-through ${Math.round((form.cwKrFundingPassThrough || 0) * 100)}% (ASSUMED)`,
        `GPU operator margin pass-through ${Math.round(form.gpuOperatorMarginPassThrough * 100)}% (ASSUMED)`,
        `CAPEX demand elasticity ${Math.round(form.capexDemandElasticity * 100)}% (ASSUMED)`,
        `KR rate linkage ${Math.round(form.krRateLinkPct * 100)}% of US shock (user-defined)`,
        "Comparison baseline = no additional shock (+0bp / CAPEX 0% / CW normal)",
      ],
      limitations: [
        "Most projects lack public CFADS → DSCR often UNKNOWN",
        "No verified CoreWeave bilateral loan to Korean banks",
        "Arranger / underwrite ≠ retained principal; LGD not fabricated",
        "Classes 3–5 Korean entities are not confirmed AI DC counterparties",
        "SPV distress ≠ parent default without documented guarantee",
        "영향 확인 / 부도위험 판단 자료 부족 — unknown exposure is not zero",
      ],
    },
  };
}

export const PF_SHOCK_STAGES = ["us_shock", "us_projects", "lenders", "kr_industry", "kr_funding", "lending_capacity"];
