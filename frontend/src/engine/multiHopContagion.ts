/**
 * Iterative multi-hop financial contagion (orders 1…N).
 *
 * Replaces the prior hard stop at “CW lessors + SPVs” with a BFS over verified
 * edges and transmission rules. Does NOT invent loss percentages on every edge.
 *
 * Impact kinds:
 *   quantified  — stress band from disclosed concentration / SPV structure
 *   qualitative — modeled counterparty/investor watch (not bank default)
 *   pathway     — verified edge, no stress band assigned
 *   unsupported — relationship exists but transmission blocked
 *
 * Analytical scenario estimates — NOT confirmed default/bankruptcy.
 */
import type { Network, NetEdge } from "../types";
import type { StressLevel } from "./stressModel";
import { stressStatus } from "./stressModel";
import { CW_LESSOR_EXPOSURES, type ConcentrationTier } from "./secondaryContagion";

export const DEFAULT_MAX_ORDER = 6;

export type ImpactKind = "quantified" | "qualitative" | "pathway" | "unsupported";

export interface ContagionEvent {
  entity_id: string;
  /** Propagation wave / order: 1 = direct from origin, 2 = secondary, 3 = tertiary… */
  order: number;
  level: StressLevel | null;
  intensity: number;
  impact_kind: ImpactKind;
  from_entity: string;
  edge_id: string | null;
  mechanism: string;
  label_en: string;
  label_ko: string;
  reason: string;
  source_ids: string[];
  /** Parent auto-default never implied for SPV→parent. */
  parent_auto_default: false;
}

export interface ContagionPropagationResult {
  events: ContagionEvent[];
  /** Best (worst) stress by entity among quantified/qualitative. */
  by_entity: Record<string, ContagionEvent>;
  max_order_reached: number;
  counts: {
    order1: number; order2: number; order3_plus: number;
    quantified: number; qualitative: number; pathway: number; critical: number;
  };
  stopped_reason: string;
}

const RANK: Record<string, number> = {
  not_applicable: -1, normal: 0, insufficient: 0.5, moderate: 1, high: 2, critical: 3,
};

function worse(a: StressLevel | null, b: StressLevel | null): StressLevel | null {
  if (!a) return b;
  if (!b) return a;
  return (RANK[a] || 0) >= (RANK[b] || 0) ? a : b;
}

function intensityFor(level: StressLevel | null): number {
  if (!level) return 0.3;
  switch (level) {
    case "moderate": return 0.85;
    case "high": return 1.15;
    case "critical": return 1.55;
    case "insufficient": return 0.35;
    default: return 0.4;
  }
}

function mapLessorTier(tier: ConcentrationTier, origin: StressLevel, shockBp: number): StressLevel | null {
  if (origin === "normal" || origin === "insufficient" || origin === "not_applicable") return null;
  if (tier === "sole_segment") {
    if (origin === "moderate") return "moderate";
    if (origin === "high") return "high";
    if (origin === "critical") return "critical";
  }
  if (tier === "material_backlog" || tier === "named_campus_tenant") {
    if (origin === "moderate") return null;
    if (origin === "high") return "moderate";
    if (origin === "critical") return shockBp >= 500 ? "critical" : "high";
  }
  return null;
}

const LABEL_EN: Record<string, string> = {
  moderate: "Modeled Counterparty Stress",
  high: "High Modeled Contagion Stress",
  critical: "Critical Modeled Financial Distress",
  qualitative: "Qualitative Tertiary Exposure",
  pathway: "Verified Pathway — Unquantified",
};

const LABEL_KO: Record<string, string> = {
  moderate: "거래상대방 스트레스(시나리오)",
  high: "높은 전염 스트레스",
  critical: "심각 재무 압박 — 시나리오 추정",
  qualitative: "3차 정성 노출",
  pathway: "확인된 경로 · 금액 미산정",
};

type TxResult = {
  level: StressLevel | null;
  impact_kind: ImpactKind;
  mechanism: string;
  reason: string;
  source_ids: string[];
  label_en?: string;
  label_ko?: string;
  /** If true, continue BFS from this node when level is moderate+. */
  propagates: boolean;
};

/**
 * Decide how stress at `fromId` transmits across `edge` to the other endpoint.
 * Returns null if this edge is not a transmission candidate for the from-node.
 */
function transmit(
  fromId: string,
  fromLevel: StressLevel,
  edge: NetEdge,
  shockBp: number,
): { toId: string; tx: TxResult } | null {
  const toId = edge.source === fromId ? edge.target : edge.target === fromId ? edge.source : null;
  if (!toId) return null;

  const rt = (edge.relationship_type || "").toUpperCase();
  const ch = edge.impact_channel;

  // --- Lease / facility: tenant → landlord (CoreWeave → lessor) ---
  if (ch === "facility" && (rt === "LESSOR" || rt.includes("LEASE"))) {
    // Only transmit from tenant (edge.source) to landlord (edge.target)
    if (edge.source !== fromId) return null;
    // Direct CW→SPV facility: treat as pathway reinforcement, primary SPV stress via PARENT_SPV
    // so that wave order preserves CORZ→SPV→purchasers as 1→2→3.
    if (toId.endsWith("_finance_i") || toId.includes("helios_ii") || toId.startsWith("galaxy_helios")) {
      return {
        toId,
        tx: {
          level: null,
          impact_kind: "pathway",
          mechanism: "facility_to_spv_pathway",
          reason: "임차→SPV 경로 확인. SPV 스트레스는 모회사 PARENT_SPV 전파로 산정(순서 보존).",
          source_ids: edge.source_ids || [],
          propagates: false,
        },
      };
    }
    const exp = CW_LESSOR_EXPOSURES.find((e) => e.entity_id === toId);
    if (exp) {
      const level = mapLessorTier(exp.tier, fromLevel, shockBp);
      if (!level) {
        return {
          toId,
          tx: {
            level: null,
            impact_kind: "pathway",
            mechanism: "lease_watch",
            reason: `${exp.concentration_note} — 원점 스트레스가 임차 임계 미만.`,
            source_ids: exp.source_ids,
            propagates: false,
          },
        };
      }
      return {
        toId,
        tx: {
          level,
          impact_kind: "quantified",
          mechanism: "lease_cashflow",
          reason: `임차 현금흐름 집중: ${exp.concentration_note}`,
          source_ids: exp.source_ids,
          propagates: level === "high" || level === "critical",
        },
      };
    }
    // Other facility edges: pathway only
    return {
      toId,
      tx: {
        level: null,
        impact_kind: "pathway",
        mechanism: "facility_pathway",
        reason: "시설·임차 관계는 확인되나 매출 집중도 미공시로 스트레스 밴드 미산정.",
        source_ids: edge.source_ids || [],
        propagates: false,
      },
    };
  }

  // --- Parent → SPV ---
  if (rt === "PARENT_SPV" || rt.includes("PARENT_SPV")) {
    if (edge.source !== fromId) return null; // parent is source
    if (fromLevel !== "high" && fromLevel !== "critical") {
      return {
        toId,
        tx: {
          level: null,
          impact_kind: "pathway",
          mechanism: "parent_spv_watch",
          reason: "모회사 스트레스가 SPV 전파 임계(high/critical) 미만.",
          source_ids: edge.source_ids || [],
          propagates: false,
        },
      };
    }
    // Single-tenant CW SPVs → critical; others high
    const singleTenant = toId.includes("finance_i") || toId.includes("helios");
    const level: StressLevel = singleTenant && fromLevel === "critical" ? "critical" : "high";
    return {
      toId,
      tx: {
        level,
        impact_kind: "quantified",
        mechanism: "spv_debt_service",
        reason:
          `모회사 ${fromLevel} → 프로젝트 SPV 부채상환·완공 압박(시나리오). ` +
          `모회사 notes 미보증이어도 SPV 자체는 심각할 수 있음. 모회사 자동 파산 아님.`,
        source_ids: edge.source_ids || [],
        propagates: level === "critical" || level === "high",
        label_en: level === "critical"
          ? "Critical Modeled Financial Distress (Project SPV)"
          : "High Modeled Contagion Stress (Project SPV)",
        label_ko: level === "critical"
          ? "심각 재무 압박 — 프로젝트 SPV"
          : "높은 전염 스트레스 — 프로젝트 SPV",
      },
    };
  }

  // --- Investor / preferred equity (company → capital partner) ---
  if (rt === "INVESTOR" || rt.includes("INVESTOR") || rt.includes("PREFERRED")) {
    if (edge.source !== fromId) return null;
    if (fromLevel !== "high" && fromLevel !== "critical") return null;
    // Diversified asset managers: qualitative moderate only — never auto-critical
    return {
      toId,
      tx: {
        level: "moderate",
        impact_kind: "qualitative",
        mechanism: "project_equity",
        reason:
          `프로젝트 우선주·자본 파트너 노출(한도 ${edge.amount_usd_m ?? "미공시"} USD M). ` +
          `기관 전체 부도로 해석하지 않음 — 해당 약정 가치 하락·회수 리스크(정성).`,
        source_ids: edge.source_ids || [],
        propagates: false, // stop: do not cascade into bank subsidiaries
        label_en: "Qualitative Project-Equity Exposure",
        label_ko: "프로젝트 지분·우선주 정성 노출",
      },
    };
  }

  // --- Initial purchaser / arranger / underwriter (SPV → bank) ---
  if (
    rt === "INITIAL_PURCHASER" || rt === "ARRANGER" || rt === "UNDERWRITER"
    || rt.includes("PURCHASER") || rt.includes("ARRANGER") || rt.includes("BOOKRUNNER")
  ) {
    if (edge.source !== fromId) return null; // SPV/issuer is source
    if (fromLevel !== "critical" && fromLevel !== "high") return null;
    return {
      toId,
      tx: {
        level: null, // pathway / watch — no bank stress band
        impact_kind: "pathway",
        mechanism: "arranger_underwriter",
        reason:
          "주선·초기매수 대표는 보유액≠손실. 증권화 유통 후 보유는 QIB에 분산 — " +
          "은행 행성 파괴로 연결하지 않음. 경로만 표시.",
        source_ids: edge.source_ids || [],
        propagates: false,
        label_en: LABEL_EN.pathway,
        label_ko: LABEL_KO.pathway,
      },
    };
  }

  // --- Supply / customer / generic lender: NO automatic contagion event ---
  // Reachability ≠ loss. These remain visible in Network view and lender Stage backdrop,
  // but do not consume hop orders or pin banks at order 1 ahead of SPV→purchaser paths.
  return null;
}

function edgesTouching(net: Network, id: string): NetEdge[] {
  return net.edges.filter((e) => e.source === id || e.target === id);
}

export function propagateContagion(
  net: Network,
  originId: string,
  originLevel: StressLevel,
  shockBp: number,
  opts?: { maxOrder?: number; enabled?: boolean },
): ContagionPropagationResult {
  const maxOrder = opts?.maxOrder ?? DEFAULT_MAX_ORDER;
  if (opts?.enabled === false || originLevel === "normal" || originLevel === "not_applicable") {
    return {
      events: [],
      by_entity: {},
      max_order_reached: 0,
      counts: { order1: 0, order2: 0, order3_plus: 0, quantified: 0, qualitative: 0, pathway: 0, critical: 0 },
      stopped_reason: "Origin not in distress band — no counterparty contagion",
    };
  }

  type Q = { id: string; order: number; level: StressLevel };
  const queue: Q[] = [{ id: originId, order: 0, level: originLevel }];
  const bestLevel = new Map<string, StressLevel | null>([[originId, originLevel]]);
  const bestOrder = new Map<string, number>([[originId, 0]]);
  const events: ContagionEvent[] = [];
  const eventKey = new Set<string>(); // entity|order|mechanism to allow pathway + stress

  let guard = 0;
  while (queue.length && guard++ < 5000) {
    // Deterministic: sort by order then id
    queue.sort((a, b) => a.order - b.order || a.id.localeCompare(b.id));
    const cur = queue.shift()!;
    if (cur.order >= maxOrder) continue;

    const neighbors = edgesTouching(net, cur.id).slice().sort((a, b) => a.id.localeCompare(b.id));
    for (const edge of neighbors) {
      const hit = transmit(cur.id, cur.level, edge, shockBp);
      if (!hit) continue;
      const { toId, tx } = hit;
      if (toId === originId) continue; // no cycle back to origin as victim

      const newOrder = cur.order + 1;
      const prev = bestLevel.has(toId) ? (bestLevel.get(toId) ?? null) : undefined;
      const prevOrder = bestOrder.get(toId);
      const hasPriorStress = prev != null;
      // Pathway-only must not pin order; first stress path defines order (so CORZ→SPV stays L2, not L1).
      const orderToUse = tx.level != null
        ? (hasPriorStress && prevOrder !== undefined ? Math.min(prevOrder, newOrder) : newOrder)
        : (prevOrder ?? newOrder);

      const ek = `${toId}|${tx.mechanism}|${tx.impact_kind}`;
      const isBetterStress = tx.level != null && (prev == null || prev === undefined
        || (RANK[tx.level] || 0) > (RANK[prev] || 0));
      const isNew = !eventKey.has(ek);

      if (isNew || isBetterStress) {
        eventKey.add(ek);
        const idx = events.findIndex((e) => e.entity_id === toId && e.mechanism === tx.mechanism);
        const ev: ContagionEvent = {
          entity_id: toId,
          order: orderToUse,
          level: tx.level,
          intensity: intensityFor(tx.level),
          impact_kind: tx.impact_kind,
          from_entity: cur.id,
          edge_id: edge.id,
          mechanism: tx.mechanism,
          label_en: tx.label_en
            || (tx.level ? LABEL_EN[tx.level] : LABEL_EN[tx.impact_kind] || LABEL_EN.pathway),
          label_ko: tx.label_ko
            || (tx.level ? LABEL_KO[tx.level] : LABEL_KO[tx.impact_kind] || LABEL_KO.pathway),
          reason: `order ${orderToUse}: ${fromPath(cur.id)} → ${toId}. ${tx.reason}`,
          source_ids: tx.source_ids,
          parent_auto_default: false,
        };
        if (idx >= 0) events[idx] = ev;
        else events.push(ev);
      }

      if (tx.level != null && (prev == null || prev === undefined
        || (RANK[tx.level] || 0) > (RANK[prev] || 0))) {
        bestLevel.set(toId, tx.level);
        bestOrder.set(toId, orderToUse);
        if (tx.propagates && newOrder < maxOrder) {
          queue.push({ id: toId, order: newOrder, level: tx.level });
        }
      } else if (tx.level == null) {
        if (!bestLevel.has(toId)) bestLevel.set(toId, null);
        if (prevOrder === undefined) bestOrder.set(toId, newOrder);
      }
    }
  }

  // Collapse to best display event per entity (prefer quantified/qualitative over pathway)
  const by_entity: Record<string, ContagionEvent> = {};
  const ranked = (e: ContagionEvent) => {
    const ik = e.impact_kind === "quantified" ? 3 : e.impact_kind === "qualitative" ? 2 : e.impact_kind === "pathway" ? 1 : 0;
    return ik * 10 + (RANK[e.level || "normal"] || 0);
  };
  for (const e of events) {
    const prev = by_entity[e.entity_id];
    if (!prev || ranked(e) > ranked(prev)) by_entity[e.entity_id] = e;
  }

  const list = Object.values(by_entity);
  const max_order_reached = list.reduce((m, e) => Math.max(m, e.order), 0);
  const counts = {
    order1: list.filter((e) => e.order === 1).length,
    order2: list.filter((e) => e.order === 2).length,
    order3_plus: list.filter((e) => e.order >= 3).length,
    quantified: list.filter((e) => e.impact_kind === "quantified").length,
    qualitative: list.filter((e) => e.impact_kind === "qualitative").length,
    pathway: list.filter((e) => e.impact_kind === "pathway").length,
    critical: list.filter((e) => e.level === "critical").length,
  };

  return {
    events: list.sort((a, b) => a.order - b.order || a.entity_id.localeCompare(b.entity_id)),
    by_entity,
    max_order_reached,
    counts,
    stopped_reason: max_order_reached >= maxOrder
      ? `Reached maxOrder=${maxOrder}`
      : guard >= 5000
        ? "Iteration guard"
        : "No further justified transmissions",
  };
}

function fromPath(id: string): string {
  return id;
}

export function contagionNodeStatus(level: StressLevel | null, impact: ImpactKind): string {
  if (level) return stressStatus(level, true);
  if (impact === "pathway" || impact === "unsupported") return "potential";
  if (impact === "qualitative") return "potential";
  return "insufficient";
}

/** Synthetic chain helper for unit tests (does not touch production network). */
export function propagateSyntheticChain(
  nodeIds: string[],
  /** Directed edges i→i+1 transmit quantified stress one band down. */
  maxOrder = 6,
): ContagionPropagationResult {
  const nodes = nodeIds.map((id) => ({
    id, name: id, group: "demo", sector: "", entity_type: "company", role: "", description: "",
    listed: false, ticker: null, exchange: null, quote_currency: null, listing_note: null,
    display_size: 3, source_status: "ASSUMED" as const, source_ids: [], key_drivers: [],
  }));
  const edges: NetEdge[] = [];
  for (let i = 0; i < nodeIds.length - 1; i++) {
    // Use LESSOR facility so transmit() maps sole_segment-like via a synthetic exposure hack:
    // We'll use PARENT_SPV for hops after first, and facility for first.
    if (i === 0) {
      edges.push({
        id: `e_${i}`, source: nodeIds[i], target: nodeIds[i + 1],
        relationship_type: "LESSOR", impact_channel: "facility",
        label: "syn", impact_label: "syn", source_status: "ASSUMED",
        source_ids: [], contract_ids: [], commercial_ids: [],
        amount_usd_m: null, amount_note: "", roles: [], explanation: "",
      });
    } else {
      edges.push({
        id: `e_${i}`, source: nodeIds[i], target: nodeIds[i + 1],
        relationship_type: "PARENT_SPV", impact_channel: "financial",
        label: "syn", impact_label: "syn", source_status: "ASSUMED",
        source_ids: [], contract_ids: [], commercial_ids: [],
        amount_usd_m: null, amount_note: "", roles: [], explanation: "",
      });
    }
  }
  // Inject temporary lessor exposure for B (nodeIds[1])
  const prev = [...CW_LESSOR_EXPOSURES];
  CW_LESSOR_EXPOSURES.length = 0;
  CW_LESSOR_EXPOSURES.push({
    entity_id: nodeIds[1],
    name: nodeIds[1],
    tier: "sole_segment",
    contract_value_usd_m: 1,
    concentration_note: "synthetic",
    source_ids: [],
    edge_prefer: "facility",
  });
  try {
    const net = {
      meta: { name: "syn", as_of: "", currency_unit: "USD", disclaimer: "", status_legend: {} },
      sources: [], nodes, edges,
      financials: {} as Network["financials"],
      contracts: [],
    } as Network;
    return propagateContagion(net, nodeIds[0], "critical", 500, { maxOrder });
  } finally {
    CW_LESSOR_EXPOSURES.length = 0;
    CW_LESSOR_EXPOSURES.push(...prev);
  }
}
