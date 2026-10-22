/**
 * Port of backend/app/engine/refinancing.py — used by the standalone demo (no server).
 * Keep the two in step: `npm run parity` compares both outputs field by field.
 */
import type { Assessment, Instrument, Network, NodeState, RefiParams, RefiResult, RefiRound, RefiCore, ScheduleRow } from "../types";
import { relationshipSummary } from "./relations";

export const STAGES = ["Refinancing Event", "Funding Cost", "Investment Capacity", "GPU Supply Chain", "HBM Supply Chain", "Network Impact"];
export const STAGES_KO = ["차환 발생", "자금조달 비용", "투자여력", "GPU 공급망", "HBM 공급망", "네트워크 종합"];
export const COMPARE_RATES = [9, 12, 15];
const ORIGIN = "coreweave";

export class RefiError extends Error {}

// ---- formatting helpers (identical arithmetic to the Python side) ----
export function r(x: number, nd = 4): number {
  const k = 10 ** nd;
  return Math.floor(x * k + 0.5) / k;
}
const fix = (x: number, nd: number) => r(Math.abs(x), nd).toFixed(nd);
export function g(x: number): string {
  const s = r(x, 6).toFixed(6).replace(/0+$/, "").replace(/\.$/, "");
  return s === "-0" || s === "" ? "0" : s;
}
const sign = (x: number) => (x < 0 ? "−" : x > 0 ? "+" : "");
function group(s: string): string {
  const [whole0, frac] = s.split(".");
  let whole = whole0, out = "";
  while (whole.length > 3) { out = "," + whole.slice(-3) + out; whole = whole.slice(0, -3); }
  return whole + out + (frac ? "." + frac : "");
}
function m(x: number): string {
  const a = Math.abs(x);
  const s = a >= 1000 ? `$${fix(a / 1000, 2)}B` : a >= 10 ? `$${group(fix(a, 0))}M` : `$${fix(a, 1)}M`;
  return sign(x) + s;
}
const u = (x: number) => m(Math.abs(x)).replace(/^[+−]+/, "");

function parseYm(s: string): [number, number] {
  const parts = s.split("-");
  const y = parseInt(parts[0], 10), mth = parts.length > 1 ? parseInt(parts[1], 10) : 12;
  if (!(mth >= 1 && mth <= 12)) throw new RefiError(`잘못된 날짜: ${s}`);
  return [y, mth];
}

export function nextMaturityId(net: Network, today?: string): string | null {
  const t = (today || net.meta.as_of).slice(0, 7);
  const c = net.financials.instruments.filter((x) => x.maturity && (x.principal_usd_m || 0) > 0 && x.maturity >= t);
  c.sort((a, b) => (a.maturity! < b.maturity! ? -1 : a.maturity! > b.maturity! ? 1 : 0));
  return c.length ? c[0].id : null;
}

export function existingRate(inst: Instrument, basis: string, sofr: number) {
  if (basis !== "stated" && basis !== "effective") throw new RefiError("basis는 stated 또는 effective");
  if (basis === "stated") {
    if (inst.rate_type === "fixed" && inst.coupon_pct !== null) {
      return { rate_pct: inst.coupon_pct, basis: "stated", status: inst.rate_status, formula: `표면금리 ${g(inst.coupon_pct)}% (고정)`, fallback: false };
    }
    if (inst.rate_type === "floating" && inst.spread_pct !== null) {
      const base = inst.floor_pct === null ? sofr : Math.max(sofr, inst.floor_pct);
      const st = inst.rate_status !== "VERIFIED" ? "INFERRED" : "VERIFIED";
      return { rate_pct: r(base + inst.spread_pct), basis: "stated", status: st, formula: `SOFR ${g(base)}% + 가산금리 ${g(inst.spread_pct)}%`, fallback: false };
    }
  }
  if (inst.effective_rate_pct !== null) {
    return { rate_pct: inst.effective_rate_pct, basis: "effective", status: "VERIFIED",
      formula: `10-Q 유효이자율 ${g(inst.effective_rate_pct)}% (반올림 공시값)`, fallback: basis === "stated" };
  }
  throw new RefiError(`${inst.name}: 기존 금리를 확인할 수 없어 계산할 수 없습니다 (표면금리·유효이자율 모두 미공시).`);
}

function core(amount: number, success: number, ex: number, nw: number, fee: number, ref: Record<string, number | null>): RefiCore {
  const refinanced = amount * success;
  const delta = (refinanced * (nw - ex)) / 100;
  return {
    new_rate_pct: nw,
    existing_rate_pct: ex,
    rate_change_bp: r((nw - ex) * 100, 1),
    amount_usd_m: r(amount),
    refinanced_usd_m: r(refinanced),
    not_refinanced_usd_m: r(amount - refinanced),
    annual_interest_existing_usd_m: r((refinanced * ex) / 100),
    annual_interest_new_usd_m: r((refinanced * nw) / 100),
    annual_interest_delta_usd_m: r(delta),
    one_off_fee_usd_m: r((refinanced * fee) / 100),
    funding_need_usd_m: r(amount - refinanced),
    delta_6m_usd_m: r(delta / 2),
    delta_6m_vs_ocf_6m_pct: ref.ocf_6m ? r((delta / 2 / ref.ocf_6m) * 100) : null,
    delta_6m_vs_interest_6m_pct: ref.contractual_interest_6m ? r((delta / 2 / ref.contractual_interest_6m) * 100) : null,
  };
}

function schedule(refinanced: number, ex: number, nw: number, fee: number, start: [number, number], tenor: number): ScheduleRow[] {
  const [sy, sm] = start;
  const endIndex = sy * 12 + (sm - 1) + tenor * 12;
  const rows: ScheduleRow[] = [];
  for (let y = sy; y < sy + tenor + 1; y++) {
    const first = Math.max(y * 12, sy * 12 + sm - 1);
    const last = Math.min(y * 12 + 12, endIndex);
    const months = Math.max(0, last - first);
    if (months === 0 && y !== sy + tenor) continue;
    const base = (((refinanced * ex) / 100) * months) / 12;
    const nwv = (((refinanced * nw) / 100) * months) / 12;
    const principal = Math.floor((endIndex - 1) / 12) === y ? refinanced : 0;
    const f = y === sy ? (refinanced * fee) / 100 : 0;
    if (months === 0 && principal === 0) continue;
    rows.push({ year: y, months, interest_existing_usd_m: r(base), interest_new_usd_m: r(nwv), interest_delta_usd_m: r(nwv - base),
      fee_usd_m: r(f), principal_usd_m: r(principal), debt_service_new_usd_m: r(nwv + f + principal) });
  }
  return rows;
}

function metric(net: Network, id: string): number | null {
  const x = net.financials.metrics.find((mm) => mm.id === id);
  return x ? x.value_usd_m : null;
}

export function simulateRefinancing(net: Network, p: RefiParams): RefiResult {
  const fin = net.financials;
  const inst = fin.instruments.find((x) => x.id === p.instrument_id);
  if (!inst) throw new RefiError(`알 수 없는 차입금: ${p.instrument_id}`);
  const newRate = p.new_rate_pct;
  const success = p.success_ratio ?? 1;
  const fee = p.fee_pct ?? 0;
  const tenor = p.new_tenor_years ?? 5;
  const basis = p.basis ?? "stated";
  const absorb = p.capex_absorption_pct ?? null;
  const gshare = p.gpu_share_pct ?? null;
  if (!(newRate >= 0 && newRate <= 40)) throw new RefiError("신규 금리는 0~40% 범위");
  if (!(success >= 0 && success <= 1)) throw new RefiError("차환 성공 비율은 0~1");
  if (!(fee >= 0 && fee <= 10)) throw new RefiError("추가 조달비용은 0~10%");
  if (!(Math.trunc(tenor) >= 1 && Math.trunc(tenor) <= 15)) throw new RefiError("신규 만기는 1~15년");
  for (const [v, nm] of [[absorb, "CAPEX 흡수율"], [gshare, "GPU 비중"]] as [number | null, string][]) {
    if (v !== null && !(v >= 0 && v <= 100)) throw new RefiError(`${nm}은 0~100%`);
  }
  const sofr = p.sofr_pct === null || p.sofr_pct === undefined ? fin.market_inputs.sofr_pct : p.sofr_pct;
  if (!(sofr >= 0 && sofr <= 20)) throw new RefiError("SOFR는 0~20%");

  const warnings: string[] = [];
  const amountIn = p.amount_usd_m ?? null;
  const amount = amountIn !== null ? amountIn : inst.principal_usd_m;
  if (amount === null || amount <= 0) throw new RefiError(`${inst.name}: 2026.6.30 기준 잔액이 공시되지 않았습니다. 차환 대상 금액을 직접 입력하세요.`);
  if (amountIn === null && (inst.amortization || "").includes("분할상환")) {
    warnings.push("분할상환 차입금이라 만기 시점 잔액은 2026.6.30 잔액보다 작습니다. 개별 상환 스케줄이 공시되지 않아 6.30 잔액을 기본값으로 썼습니다.");
  }
  if (amountIn !== null && inst.principal_usd_m && amountIn > inst.principal_usd_m) warnings.push("입력 금액이 공시 잔액보다 큽니다.");

  const ex = existingRate(inst, basis, sofr);
  if (ex.fallback) warnings.push(`${inst.name}의 표면금리가 공시되지 않아 10-Q 유효이자율로 비교했습니다.`);
  if (ex.status === "INFERRED" && inst.effective_rate_pct !== null) warnings.push(`기존 금리의 가산금리는 2차 출처 값(INFERRED)입니다. 공시 유효이자율 ${g(inst.effective_rate_pct)}% 기준으로도 비교해 보세요.`);
  if (inst.kind === "convertible") warnings.push("전환사채는 낮은 표면금리 대신 전환권을 준 구조라 일반 차입금리와 단순 비교 시 차이가 크게 보입니다.");

  let refiDate = p.refi_date ?? null;
  if (refiDate === null) {
    const mt = inst.maturity;
    refiDate = mt && mt.length >= 7 ? mt.slice(0, 7) : mt ? `${mt}-01` : net.meta.as_of.slice(0, 7);
  }
  const start = parseYm(refiDate);

  const ref = { ocf_6m: metric(net, "ocf_6m"), contractual_interest_6m: metric(net, "contractual_interest_6m"),
    cash: metric(net, "cash"), capex_6m: metric(net, "capex_6m") };
  const main = core(amount, success, ex.rate_pct, newRate, fee, ref);
  const sched = schedule(amount * success, ex.rate_pct, newRate, fee, start, Math.trunc(tenor));
  const rates = p.compare_rates ?? COMPARE_RATES;
  const comparison = rates.map((rt, i) => ({ ...core(amount, success, ex.rate_pct, rt, fee, ref), label: `Scenario ${String.fromCharCode(65 + i)}` }));

  const delta = main.annual_interest_delta_usd_m;
  let capexCut: number | null = null, gpuCut: number | null = null;
  if (absorb !== null && delta > 0) {
    capexCut = r((delta * absorb) / 100);
    if (gshare !== null) gpuCut = r((capexCut * gshare) / 100);
  }
  const nvRev = fin.reference.nvidia_revenue_fy2026_usd_m;
  const gpuVsNv = gpuCut !== null ? r((gpuCut / nvRev) * 100, 6) : null;

  const rounds = buildRounds(net, inst, ex, main, newRate, absorb, gshare, capexCut, gpuCut, gpuVsNv);
  const assessments = buildAssessments(net, inst, main, capexCut, gpuCut, gpuVsNv);
  const pick = <K extends keyof Instrument>(k: K) => (inst[k] === undefined ? null : inst[k]);

  return {
    mode: "REFINANCING",
    origin: ORIGIN,
    instrument: {
      id: inst.id, name: inst.name, kind: inst.kind, principal_usd_m: pick("principal_usd_m"), principal_as_of: inst.principal_as_of,
      maturity: pick("maturity"), rate_type: inst.rate_type, coupon_pct: pick("coupon_pct"), spread_pct: pick("spread_pct"),
      effective_rate_pct: pick("effective_rate_pct"), rate_status: inst.rate_status, rate_note: inst.rate_note, borrower: pick("borrower"),
      recourse: pick("recourse"), source_ids: inst.source_ids,
    },
    params: { instrument_id: p.instrument_id, new_rate_pct: newRate, amount_usd_m: amount, basis, refi_date: refiDate, success_ratio: success,
      fee_pct: fee, new_tenor_years: Math.trunc(tenor), sofr_pct: sofr, capex_absorption_pct: absorb, gpu_share_pct: gshare },
    existing_rate: ex,
    result: main,
    schedule: sched,
    comparison,
    reference: { ocf_6m_usd_m: ref.ocf_6m, contractual_interest_6m_usd_m: ref.contractual_interest_6m, cash_usd_m: ref.cash,
      capex_6m_usd_m: ref.capex_6m, as_of: fin.as_of, source_ids: [fin.filing], nvidia_revenue_fy2026_usd_m: nvRev,
      nvidia_source_id: fin.reference.nvidia_source_id },
    assumption_chain: { capex_absorption_pct: absorb, capex_cut_usd_m: capexCut, gpu_share_pct: gshare, gpu_purchase_cut_usd_m: gpuCut,
      gpu_cut_vs_nvidia_revenue_pct: gpuVsNv },
    rounds,
    assessments,
    warnings,
    notes: [
      "추가 이자비용은 차환 대상 차입금 하나에만 적용했습니다. 다른 차입금의 금리는 바뀌지 않습니다.",
      "비교 기준선은 '같은 기간 기존 금리 유지'입니다. 실제 기존 차입금은 만기에 상환되므로, 기준선은 비교용입니다.",
      "상반기 비교는 연간 추가 이자의 1/2을 같은 6개월 실적과 비교한 값입니다(기간 기준 일치).",
      "금리 상승이 곧 부도나 투자 축소를 뜻하지 않습니다. 투자 축소 이후 단계는 사용자 가정이 있을 때만 숫자로 표시합니다.",
    ],
  };
}

function edgeTo(net: Network, a: string, b: string, prefer?: string): string | null {
  const c = net.edges.filter((e) => e.source === a && e.target === b);
  if (prefer) for (const e of c) if (e.impact_channel === prefer) return e.id;
  return c.length ? c[0].id : null;
}

function buildRounds(net: Network, inst: Instrument, ex: ReturnType<typeof existingRate>, main: RefiCore, newPct: number,
  absorb: number | null, gshare: number | null, capexCut: number | null, gpuCut: number | null, gpuVsNv: number | null): RefiRound[] {
  const delta = main.annual_interest_delta_usd_m;
  const parts = inst.participants || [];
  const partIds = parts.map((x) => x.entity);
  const finEdges = partIds.map((pid) => edgeTo(net, ORIGIN, pid, "financial")).filter((x): x is string => !!x);
  const states: Record<string, NodeState> = {};
  const rounds: RefiRound[] = [];
  const snap = (i: number, lines: string[], active: string[]) => {
    const ns: Record<string, NodeState> = {};
    for (const [k, v] of Object.entries(states)) ns[k] = { ...v };
    rounds.push({ round: i, stage: i + 1, title: `STAGE ${i + 1} · ${STAGES[i]}`, title_ko: STAGES_KO[i], lines, active_edges: active, node_states: ns });
  };

  states[ORIGIN] = { status: "shock_origin", label: `${inst.name} → ${g(newPct)}%`, category: "computed" };
  for (const pid of partIds) states[pid] = { status: "contract_party", label: "계약 참여 · 영향 미산정", category: "relationship_only" };
  let lines = [`CoreWeave가 ${inst.name} ${u(main.amount_usd_m)}을(를) ${g(newPct)}%로 차환한다고 가정 (기존 비교금리 ${g(ex.rate_pct)}%, ${ex.formula})`];
  lines.push(parts.length ? `계약 참여 기관 ${parts.length}곳 표시 — 기관별 보유액 미공시로 영향 미산정` : "공시된 계약 참여 기관 없음");
  snap(0, lines, finEdges);

  states[ORIGIN] = { status: "shock_origin", label: `이자 ${m(delta)}/년`, category: "computed" };
  lines = [`연간 이자비용 ${u(main.annual_interest_existing_usd_m)} → ${u(main.annual_interest_new_usd_m)} (차이 ${m(delta)}/년, ${sign(main.rate_change_bp)}${g(Math.abs(main.rate_change_bp))}bp)`];
  if (main.delta_6m_vs_ocf_6m_pct !== null) lines.push(`6개월 환산 ${m(main.delta_6m_usd_m)} = 2026 상반기 영업현금흐름의 ${sign(main.delta_6m_vs_ocf_6m_pct)}${fix(main.delta_6m_vs_ocf_6m_pct, 2)}%`);
  if (main.funding_need_usd_m) lines.push(`차환되지 않은 ${u(main.funding_need_usd_m)}은 자체 자금으로 상환 필요 (자금조달 필요액)`);
  snap(1, lines, []);

  if (delta <= 0) lines = ["이자 부담이 늘지 않아 투자여력 감소 경로가 생기지 않습니다."];
  else if (capexCut !== null) {
    states[ORIGIN] = { status: "shock_origin", label: `CAPEX ${m(-capexCut)}/년 (가정)`, category: "assumed" };
    lines = [`사용자 가정: 추가 이자의 ${g(absorb!)}%를 CAPEX 축소로 흡수 → CAPEX ${m(-capexCut)}/년`];
  } else lines = ["투자여력이 줄어들 수 있으나, 축소 규모는 가정 없이는 계산하지 않습니다 (CAPEX 흡수율 미입력)."];
  snap(2, lines, []);

  const propagate = delta > 0;
  const gpuEdges = propagate ? [edgeTo(net, ORIGIN, "nvidia", "supply_chain"), edgeTo(net, ORIGIN, "dell", "supply_chain")].filter((x): x is string => !!x) : [];
  if (propagate) {
    if (gpuCut !== null) {
      states.nvidia = { status: "assumed", label: `GPU 구매 ${m(-gpuCut)} (가정)`, category: "assumed" };
      lines = [`사용자 가정: CAPEX 축소분의 ${g(gshare!)}%가 GPU 구매 → GPU 구매 ${m(-gpuCut)}/년`,
        `NVIDIA FY2026 매출 대비 ${fix(gpuVsNv!, 4)}% (가정 기반 비율, 매출 감소 예측 아님)`];
    } else {
      states.nvidia = { status: "potential", label: "잠재 경로 · 미산정", category: "relationship_only" };
      lines = ["NVIDIA로 GPU 구매 변화가 전달될 수 있으나, CAPEX·GPU 비중 가정이 없어 금액을 계산하지 않습니다."];
    }
    states.dell = { status: "potential", label: "잠재 경로 · 미산정", category: "relationship_only" };
    lines.push("Dell: CoreWeave의 Dell 서버 구매 비중이 공시되지 않아 미산정");
  } else lines = ["추가 이자 부담이 없으므로 공급망 전달 경로를 표시하지 않습니다."];
  snap(3, lines, gpuEdges);

  const hbmEdges = propagate ? [edgeTo(net, "nvidia", "sk_hynix"), edgeTo(net, "nvidia", "tsmc"), edgeTo(net, "dell", "nvidia")].filter((x): x is string => !!x) : [];
  if (propagate) {
    states.sk_hynix = { status: "potential", label: "잠재 경로 · 미산정", category: "relationship_only" };
    states.tsmc = { status: "potential", label: "잠재 경로 · 미산정", category: "relationship_only" };
    lines = ["SK hynix: NVIDIA의 HBM 매입 중 SK hynix 비중이 공시되지 않아 금액 미산정 (관계는 확인)",
      "TSMC: NVIDIA 위탁생산 관계는 산업 구조 추론(INFERRED), 금액 미산정"];
  } else lines = ["전달 경로 없음"];
  snap(4, lines, hbmEdges);

  const cats: Record<string, number> = {};
  for (const v of Object.values(states)) cats[v.category] = (cats[v.category] || 0) + 1;
  const assumedN = Object.entries(states).filter(([k, v]) => v.category === "assumed" && k !== ORIGIN).length;
  lines = [`계산값: CoreWeave 이자비용 ${m(delta)}/년`,
    `가정 기반 계산 ${assumedN}곳 · 관계만 확인(미산정) ${cats.relationship_only || 0}곳`,
    "고객사·데이터센터 임대인은 이번 차환 충격과 정량 전달 경로가 없어 표시하지 않습니다."];
  snap(5, lines, [...new Set([...finEdges, ...gpuEdges, ...hbmEdges])].sort());
  return rounds;
}

const NEEDED: Record<string, string> = {
  nvidia: "CoreWeave의 연간 NVIDIA GPU 구매액, NVIDIA 매출 중 CoreWeave 비중",
  dell: "CoreWeave의 Dell 서버 구매액과 Dell AI 서버 매출 중 비중",
  sk_hynix: "NVIDIA HBM 매입액 중 SK hynix 비중, CoreWeave발 GPU 수요의 HBM 환산액",
  tsmc: "NVIDIA 위탁생산 금액 중 CoreWeave 관련 비중",
};

function buildAssessments(net: Network, inst: Instrument, main: RefiCore, capexCut: number | null, gpuCut: number | null,
  gpuVsNv: number | null): Record<string, Assessment> {
  const parts = new Map((inst.participants || []).map((x) => [x.entity, x]));
  const delta = main.annual_interest_delta_usd_m;
  const out: Record<string, Assessment> = {};
  for (const n of net.nodes) {
    const nid = n.id;
    const rel = relationshipSummary(net, ORIGIN, nid);
    if (nid === ORIGIN) {
      out[nid] = { category: "computed", relation: rel, values: [
        { label: "추가 연간 이자비용", usd_m: delta, status: "computed", round: 1 },
        ...(capexCut !== null ? [{ label: "CAPEX 축소 (가정)", usd_m: -capexCut, status: "assumed", round: 2 }] : [])],
        reason: "공시 차입금 잔액·금리와 사용자 신규 금리로 직접 계산", needed: null };
      continue;
    }
    if (rel.kind === "unconfirmed") {
      out[nid] = { category: "unconfirmed", relation: rel, values: [], reason: "공개자료에서 CoreWeave와의 관계 경로가 확인되지 않음", needed: "관계를 입증할 공시·계약 자료" };
      continue;
    }
    if (nid === "nvidia" && gpuCut !== null) {
      out[nid] = { category: "assumed", relation: rel, values: [
        { label: "GPU 구매 감소 (가정)", usd_m: -gpuCut, status: "assumed", round: 3 },
        { label: "NVIDIA FY2026 매출 대비", pct: gpuVsNv, status: "assumed", round: 3 }],
        reason: "CAPEX 흡수율·GPU 비중 사용자 가정으로 계산", needed: NEEDED.nvidia };
      continue;
    }
    const pp = parts.get(nid);
    if (pp) {
      out[nid] = { category: "relationship_only", relation: rel, values: [],
        reason: `${inst.name} 참여(${pp.roles.join(", ")}). 기관별 보유액이 공시되지 않아 영향 미산정. 금리 상승은 대주에게 손실이 아니라 이자수익 변화입니다.`,
        needed: "기관별 대출 보유액·재매각 여부" };
      continue;
    }
    if (NEEDED[nid] && (delta || 0) > 0) {
      out[nid] = { category: "relationship_only", relation: rel, values: [], reason: "공급망 관계는 확인되나 전달 규모를 계산할 공개 데이터가 없음", needed: NEEDED[nid] };
      continue;
    }
    out[nid] = { category: "relationship_only", relation: rel, values: [], reason: "관계는 확인되나 이번 차환 시나리오와 정량 전달 경로가 없음", needed: null };
  }
  return out;
}
