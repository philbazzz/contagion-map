import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Api, MarketOverview, Network, NetworkStats, NodeVisual, PathResult, RateShockResult, RefiParams, RefiResult, RunRecord, SourcesResponse, QuotesOverview } from "./types";
import { TopBar, type Mode, type View } from "./components/TopBar";
import { ScenarioBuilder } from "./components/ScenarioBuilder";
import { PfScenarioBuilder } from "./components/PfScenarioBuilder";
import { EcosystemSelector, type LoadState } from "./components/EcosystemSelector";
import type { StatDef } from "./components/TopBar";
import { GuideCard, guideSeen } from "./components/GuideCard";
import { displayName } from "./lib/displayName";
import { UniverseView, type Banner } from "./components/UniverseView";
import { DetailPanel } from "./components/DetailPanel";
import { BottomBar } from "./components/BottomBar";
import { SourcesView } from "./components/SourcesView";
import { MarketPanel } from "./components/Market";
import { MapErrorBoundary } from "./components/MapErrorBoundary";
import { defaultForm, defaultShockForm, type RefiForm, type ShockForm } from "./lib/scenario";
import { usdM } from "./lib/format";
import { existingRate, STAGES_KO } from "./engine/refinancing";
import { SHOCK_STAGES_KO, simulateRateShock } from "./engine/rateShock";
import type { EcosystemId, PfBundle, PfShockResult } from "./pf/types";
import { defaultPfShockForm } from "./pf/scenario";
import type { PfShockForm } from "./pf/types";
import { loadPfBundle } from "./pf/load";
import { PF_SHOCK_STAGES_KO, simulatePfShock } from "./pf/shockEngine";
import { networkStats, shortestPath } from "./engine/relations";
import { appTitle } from "./lib/appTitle";
import {
  buildBorrowerSummary,
  borrowerHighlight,
  isBorrowerNode,
  type BorrowerEdgeMode,
  type InstCategoryId,
} from "./pf/borrowerSummary";

export type Selection = { kind: "node"; id: string } | { kind: "edge"; id: string } | { kind: "contract"; id: string } | null;

export type RunView =
  | { kind: "rate_shock"; params: ShockForm; result: RateShockResult; record: RunRecord; prev: RunRecord | null }
  | { kind: "pf_shock"; params: PfShockForm; result: PfShockResult; record: RunRecord; prev: RunRecord | null }
  | { kind: "refinancing"; params: RefiParams; result: RefiResult; record: RunRecord; prev: RunRecord | null };

/** PF analytical start: CoreWeave as US shock origin; Korean PF is the destination. */
const PF_ORIGIN = "coreweave";

function marketDigest(m: MarketOverview | null): Record<string, unknown> | null {
  if (!m) return null;
  const out: Record<string, unknown> = { collected_at: m.generated_at || m.snapshot_at || null };
  for (const i of m.indicators) {
    out[i.id] = i.id === "ust_10y" || i.id === "ust_2y"
      ? { value_bp: i.latest?.value ?? null, value: i.latest?.value ?? null, obs_date: i.latest?.obs_date ?? null, status: i.status }
      : { median_usd: i.latest?.median ?? null, snap_date: i.latest?.snap_date ?? null, status: i.status };
  }
  return out;
}

/** Form → engine request. Blank optional fields stay null so the engine uses disclosed defaults. */
export function toParams(f: RefiForm): RefiParams {
  return {
    instrument_id: f.instrumentId, new_rate_pct: f.newRate, amount_usd_m: f.amount, basis: f.basis, refi_date: f.refiDate,
    success_ratio: f.success, fee_pct: f.fee, new_tenor_years: f.tenor, sofr_pct: f.sofr,
    capex_absorption_pct: f.capexAbsorb, gpu_share_pct: f.gpuShare,
  };
}

/** Quantitative rate-shock borrower (disclosed floating debt). Network focus can be any company. */
const SHOCK_BORROWER = "coreweave";

export default function App({ api }: { api: Api }) {
  const [ecosystem, setEcosystem] = useState<EcosystemId>("semiconductor");
  const [net, setNet] = useState<Network | null>(null);
  const [pfBundle, setPfBundle] = useState<PfBundle | null>(null);
  const [pfLoad, setPfLoad] = useState<LoadState>({ state: "loading" });
  const [guideOpen, setGuideOpen] = useState(() => !guideSeen());
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [view, setView] = useState<View>("map");
  const [mode, setMode] = useState<Mode>("network");
  const [origin, setOrigin] = useState(SHOCK_BORROWER);
  const [quotes, setQuotes] = useState<QuotesOverview | null>(null);
  const [pfQuotes, setPfQuotes] = useState<QuotesOverview | null>(null);
  const [quotesBusy, setQuotesBusy] = useState(false);
  const [sources, setSources] = useState<SourcesResponse | null>(null);
  const [stats, setStats] = useState<NetworkStats | null>(null);
  const [market, setMarket] = useState<MarketOverview | null>(null);
  const [marketOpen, setMarketOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const [form, setForm] = useState<RefiForm | null>(null);
  const [shock, setShock] = useState<ShockForm>(defaultShockForm);
  const [pfShock, setPfShock] = useState<PfShockForm>(defaultPfShockForm);

  const [run, setRun] = useState<RunView | null>(null);
  const [stage, setStage] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [runNo, setRunNo] = useState(0);
  /** Bumps on replay / new shock so Universe clears stuck shatter FX and re-triggers. */
  const [fxGen, setFxGen] = useState(0);

  const [selection, setSelection] = useState<Selection>(null);
  const [pathQuery, setPathQuery] = useState<{ a: string; b: string; path: PathResult | null } | null>(null);
  /** Progressive disclosure for PFV/SPC clicks — does not change shock math. */
  const [borrowerEdgeMode, setBorrowerEdgeMode] = useState<BorrowerEdgeMode>("material");
  const [borrowerCategoryFocus, setBorrowerCategoryFocus] = useState<InstCategoryId | null>(null);
  const [hiddenCats, setHiddenCats] = useState<string[]>([]);
  const [hiddenGroups, setHiddenGroups] = useState<string[]>([]);
  const [panelOpen, setPanelOpen] = useState(() => typeof window === "undefined" || window.innerWidth >= 1200);
  const [tip, setTip] = useState<{ text: string; x: number; y: number; below: boolean } | null>(null);

  const simSeq = useRef(0);
  const pathSeq = useRef(0);
  const shockSeq = useRef(0);
  const quotesSeq = useRef(0);
  const modeRef = useRef(mode);
  modeRef.current = mode;

  const title = useMemo(() => appTitle(ecosystem), [ecosystem]);
  useEffect(() => {
    document.title = title.document;
  }, [title.document]);

  useEffect(() => {
    api.network().then((n) => { setNet(n); setForm(defaultForm(n)); }).catch((e) => setLoadErr(String(e?.message || e)));
    api.sources().then(setSources).catch(() => undefined);
    api.market().then(setMarket).catch(() => setMarket(null));
    api.quotes().then(setQuotes).catch(() => setQuotes(null));
    api.listRuns().then(setRuns).catch(() => undefined);
  }, [api]);

  const loadPf = useCallback(() => {
    setPfLoad({ state: "loading" });
    loadPfBundle()
      .then((b) => { setPfBundle(b); setPfQuotes(b.quotes); setPfLoad({ state: "ready" }); })
      .catch((e) => { console.warn("PF bundle load failed", e); setPfLoad({ state: "error", message: String(e?.message || e) }); });
  }, []);
  useEffect(() => { loadPf(); }, [loadPf]);

  const activeNetRaw = ecosystem === "datacenter_pf" ? pfBundle?.network ?? null : net;
  /** Map canvas: hide historical/arranger-only by default; DetailPanel keeps full ledger. */
  const activeNet = useMemo(() => {
    if (!activeNetRaw || ecosystem !== "datacenter_pf") return activeNetRaw;
    const HIST = new Set([
      "repaid", "terminated", "historical", "withdrawn", "expired", "refinanced", "transferred",
      "FULLY_REPAID", "REFINANCED", "TRANSFERRED", "EXPIRED", "HISTORICAL_ONLY", "SECURITIZED",
    ]);
    const isHist = (e: (typeof activeNetRaw.edges)[0]) => {
      const x = e as { exposure_status?: string; relationship_status?: string; shock_eligible?: boolean };
      const st = x.exposure_status || x.relationship_status || "";
      if (HIST.has(st) || HIST.has(st.toUpperCase())) return true;
      if (x.shock_eligible === false && ["ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT"].includes(e.relationship_type)) return true;
      return false;
    };
    if (pfShock.includeHistoricalRelationships) {
      return {
        ...activeNetRaw,
        edges: activeNetRaw.edges.map((e) => {
          if (!isHist(e)) return e;
          return { ...e, layer: "historical", explanation: (e.explanation || "") + " (과거·주선)" };
        }),
      };
    }
    return { ...activeNetRaw, edges: activeNetRaw.edges.filter((e) => !isHist(e)) };
  }, [activeNetRaw, ecosystem, pfShock.includeHistoricalRelationships]);
  const activeMarket = ecosystem === "datacenter_pf" ? (pfBundle?.market ?? market) : market;
  const activeQuotes = ecosystem === "datacenter_pf" ? pfQuotes : quotes;

  useEffect(() => {
    if (!activeNet) return;
    if (ecosystem === "datacenter_pf") {
      setStats(networkStats(activeNet, origin));
      return;
    }
    api.stats(origin).then(setStats).catch(() => undefined);
  }, [api, origin, ecosystem, activeNet]);

  const switchEcosystem = useCallback((id: EcosystemId) => {
    if (id === ecosystem) return;
    setEcosystem(id);
    setRun(null);
    setPlaying(false);
    setStage(0);
    setSelection(null);
    setPathQuery(null);
    setHiddenGroups([]);
    setPinnedNodeIds([]);
    setLocateRequest(null);
    if (id === "datacenter_pf") {
      setOrigin(PF_ORIGIN);
      setPfShock(defaultPfShockForm());
      setToast("AI Data Center PF 생태계로 전환했습니다");
    } else {
      setOrigin(SHOCK_BORROWER);
      setShock(defaultShockForm());
      setToast("AI Semiconductor 생태계로 전환했습니다");
    }
  }, [ecosystem]);

  const nodeMap = useMemo(() => new Map((activeNet?.nodes || []).map((n) => [n.id, n])), [activeNet]);
  const inst = useMemo(() => (net && form ? net.financials.instruments.find((x) => x.id === form.instrumentId) || null : null), [net, form]);

  // ---------- semiconductor rate-shock (unchanged engine) ----------
  const applyRateShock = useCallback(async (s: ShockForm, n: Network) => {
    const seq = ++shockSeq.current;
    try {
      const res: RateShockResult = simulateRateShock(n, {
        shock_bp: s.shockBp,
        benchmark: s.benchmark,
        sofr_pct: s.sofr,
        crisis_mode: s.crisisMode,
        refi_availability: s.refiAvailability,
        project_financing: s.projectFinancing,
        horizon_months: s.horizonMonths,
      });
      if (seq !== shockSeq.current) return;
      const mk = marketDigest(market);
      const record: RunRecord = {
        event: "rate_shock", origin: SHOCK_BORROWER, interest: s.benchmark,
        params: {
          shock_bp: s.shockBp, benchmark: s.benchmark, sofr_pct: s.sofr,
          crisis_mode: s.crisisMode, refi_availability: s.refiAvailability,
          project_financing: s.projectFinancing, horizon_months: s.horizonMonths,
        },
        market: mk,
        summary: {
          shock_bp: s.shockBp, benchmark: s.benchmark,
          annual_interest_delta_usd_m: res.summary.total_incremental_interest_usd_m,
          direct_measurable: res.summary.direct_measurable,
          potential_indirect: res.summary.potential_indirect,
          secondary_stressed: res.summary.secondary_stressed,
          sector_stressed: res.summary.sector_stressed,
          companies_critical: res.summary.companies_critical,
        },
      };
      setRun({ kind: "rate_shock", params: s, result: res as RateShockResult, record, prev: null });
      setRunNo((x) => x + 1);
      setFxGen((x) => x + 1);
      if (modeRef.current === "shock") {
        setStage(res.rounds.length - 1);
        setPlaying(false);
      }
    } catch (e) {
      if (seq === shockSeq.current) setToast(`충격 계산 실패: ${String((e as Error)?.message || e)}`);
    }
  }, [market]);

  const applyPfShock = useCallback((s: PfShockForm, bundle: PfBundle) => {
    const seq = ++shockSeq.current;
    try {
      const res = simulatePfShock(bundle.network, bundle.projects, s);
      if (seq !== shockSeq.current) return;
      const record: RunRecord = {
        event: "pf_shock", origin: s.coreweaveDistress !== "normal" ? "coreweave" : PF_ORIGIN, interest: "pf_combined",
        params: {
          coreweave_distress: s.coreweaveDistress,
          rate_bp: s.rateBp, kr_rate_bp: s.krRateBp, gpu_rent_pct: s.gpuRentPct,
          hyperscaler_capex_pct: s.hyperscalerCapexPct, restrict_new: s.restrictNewFinancing ? 1 : 0,
          cw_kr_pass: s.cwKrFundingPassThrough,
        },
        market: marketDigest(bundle.market),
        summary: {
          measurable_projects: res.pf.measurable_projects ?? 0,
          dscr_deterioration: res.pf.dscr_deterioration ?? 0,
          companies_critical: res.summary.companies_critical ?? 0,
          annual_interest_delta_usd_m: res.summary.total_incremental_interest_usd_m ?? 0,
        },
      };
      setRun({ kind: "pf_shock", params: s, result: res, record, prev: null });
      setRunNo((x) => x + 1);
      setFxGen((x) => x + 1);
      if (modeRef.current === "shock") {
        setStage(res.rounds.length - 1);
        setPlaying(false);
      }
    } catch (e) {
      if (seq === shockSeq.current) setToast(`PF 충격 계산 실패: ${String((e as Error)?.message || e)}`);
    }
  }, []);

  useEffect(() => {
    if (mode !== "shock") return;
    if (ecosystem === "datacenter_pf") {
      if (!pfBundle) return;
      const t = setTimeout(() => applyPfShock(pfShock, pfBundle), 120);
      return () => clearTimeout(t);
    }
    if (!net) return;
    const t = setTimeout(() => { void applyRateShock(shock, net); }, 120);
    return () => clearTimeout(t);
  }, [net, shock, mode, applyRateShock, ecosystem, pfBundle, pfShock, applyPfShock]);

  // ---------- refinancing (semiconductor only) ----------
  const doRunRefi = useCallback(async () => {
    if (ecosystem !== "semiconductor" || !net || !form) return;
    const seq = ++simSeq.current;
    setBusy(true);
    const params = toParams(form);
    const mk = marketDigest(market);
    try {
      const res = await api.simulateRefinancing(params);
      if (seq !== simSeq.current) return;
      const prev = runs.find((r) => r.event === "refinancing" && r.interest === form.instrumentId) || null;
      const record: RunRecord = {
        event: "refinancing", origin: SHOCK_BORROWER, interest: form.instrumentId,
        params: { ...params } as unknown as RunRecord["params"], market: mk,
        summary: {
          instrument: res.instrument.name, existing_rate_pct: res.existing_rate.rate_pct, new_rate_pct: res.result.new_rate_pct,
          annual_interest_delta_usd_m: res.result.annual_interest_delta_usd_m, amount_usd_m: res.result.amount_usd_m,
        },
      };
      setRun({ kind: "refinancing", params, result: res, record, prev });
      setRunNo((n) => n + 1);
      setSelection(null);
      setMode("shock"); // refinancing is a Shock-tab action — switch intentionally
      setStage(0);
      setPlaying(true);
      api.saveRun(record).then((saved) => {
        setRuns((rs) => [saved, ...rs]);
        setRun((r) => (r && r.kind === "refinancing" && r.record === record ? { ...r, record: saved } : r));
      }).catch(() => undefined);
    } catch (e) {
      if (seq === simSeq.current) setToast(`계산 실패: ${String((e as Error)?.message || e)}`);
    } finally {
      if (seq === simSeq.current) setBusy(false);
    }
  }, [api, net, form, market, runs, ecosystem]);

  const lastStage = run ? run.result.rounds.length - 1 : 0;
  useEffect(() => {
    if (!playing || !run) return;
    if (stage >= lastStage) { setPlaying(false); return; }
    const cur = run.result.rounds[stage];
    const prevE = new Set(stage ? run.result.rounds[stage - 1].active_edges : []);
    const fresh = cur.active_edges.filter((e) => !prevE.has(e)).length;
    // Rate-shock stages are fewer/heavier: linger longer so secondary crack/shatter is readable.
    const base = run.kind === "rate_shock" || run.kind === "pf_shock" ? 3200 : 2600;
    const ms = (fresh ? 1800 + (fresh - 1) * 550 : 0) + base + cur.lines.length * 500;
    const t = setTimeout(() => setStage((s) => Math.min(s + 1, lastStage)), ms / speed);
    return () => clearTimeout(t);
  }, [playing, stage, lastStage, run, speed]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 4200);
    return () => clearTimeout(t);
  }, [toast]);

  const reset = useCallback(() => {
    simSeq.current += 1;
    setBusy(false);
    setPlaying(false);
    setSelection(null);
    if (ecosystem === "datacenter_pf") setPfShock(defaultPfShockForm());
    else setShock(defaultShockForm());
  }, [ecosystem]);

  const { visuals, activeEdges, usedEdges, banner, focusIds } = useMemo(() => {
    const none = { visuals: null as Record<string, NodeVisual> | null, activeEdges: [] as string[], usedEdges: null as string[] | null, banner: null as Banner | null, focusIds: [] as string[] };
    if (mode === "market") {
      const v: Record<string, NodeVisual> = {};
      for (const q of activeQuotes?.items || []) {
        if (!q.listed) continue;
        const has = q.price !== null && q.price !== undefined && q.change_pct !== null && q.change_pct !== undefined;
        if (!has) { v[q.entity] = { status: "mk_na" }; continue; }
        const c = q.change_pct as number;
        v[q.entity] = { status: c > 0 ? "mk_up" : c < 0 ? "mk_down" : "mk_flat", label: `${c > 0 ? "+" : c < 0 ? "−" : ""}${Math.abs(c).toFixed(2)}%` };
      }
      return { ...none, visuals: v };
    }
    if (mode !== "shock" || !run) return none;
    const rounds = run.result.rounds;
    const rnd = rounds[Math.min(stage, rounds.length - 1)];
    const v: Record<string, NodeVisual> = {};
    for (const [id, s] of Object.entries(rnd.node_states)) {
      v[id] = { status: s.status, label: s.label, intensity: s.intensity, stress: s.stress, fx_gen: fxGen };
    }
    const used = [...new Set(rounds.flatMap((x) => x.active_edges))];
    const stageNames = run.kind === "pf_shock" ? PF_SHOCK_STAGES_KO : run.kind === "rate_shock" ? SHOCK_STAGES_KO : STAGES_KO;
    const b: Banner = {
      kicker: `${Math.min(rnd.stage + 1, rounds.length)}/${rounds.length}단계 · ${stageNames[rnd.round] || ""}`,
      title: rnd.title_ko,
      lines: rnd.lines,
      tone: "orange",
    };
    const focusOrigin = run.kind === "pf_shock" ? PF_ORIGIN : SHOCK_BORROWER;
    const ends = activeNet ? rnd.active_edges.flatMap((id) => { const e = activeNet.edges.find((x) => x.id === id); return e ? [e.source, e.target] : []; }) : [];
    const focus = [...new Set([focusOrigin, ...Object.keys(rnd.node_states), ...ends])];
    return { visuals: v, activeEdges: rnd.active_edges, usedEdges: used, banner: b, focusIds: focus };
  }, [run, stage, mode, activeQuotes, activeNet, fxGen]);

  const highlight = useMemo(() => {
    const empty = { nodes: [] as string[], edges: [] as string[] };
    if (!activeNet) return empty;
    if (pathQuery?.path) return { nodes: pathQuery.path.nodes, edges: pathQuery.path.edges };
    if (selection?.kind === "edge") {
      const e = activeNet.edges.find((x) => x.id === selection.id);
      return e ? { nodes: [e.source, e.target], edges: [e.id] } : empty;
    }
    if (selection?.kind === "contract" && ecosystem === "semiconductor" && net) {
      const x = net.financials.instruments.find((i) => i.id === selection.id);
      if (!x) return empty;
      const parts = x.participants.map((p) => p.entity);
      const edges = net.edges.filter((e) => e.contract_ids.includes(x.id) || (e.source === SHOCK_BORROWER && parts.includes(e.target) && e.impact_channel === "financial")).map((e) => e.id);
      return { nodes: [SHOCK_BORROWER, ...parts], edges };
    }
    // Company focus: selected firm + verified counterparties (PF network)
    if (ecosystem === "datacenter_pf" && selection?.kind === "node") {
      const id = selection.id;
      const node = activeNet.nodes.find((n) => n.id === id);
      const pfRes = run?.kind === "pf_shock" ? run.result : null;
      const impactIds = new Set(pfRes?.pf?.impact_edge_ids || []);
      const companyImpact = (pfRes?.pf?.affected_companies || []).find((c) => c.company_id === id);
      const preferEdges = companyImpact?.projects.map((p) => p.edge_id).filter(Boolean)
        || [...impactIds].filter((eid) => {
          const e = activeNet.edges.find((x) => x.id === eid);
          return e && (e.source === id || e.target === id);
        });

      // PFV / SPC: progressive disclosure — highlight top material edges only by default
      if (isBorrowerNode(node)) {
        const summary = buildBorrowerSummary(id, activeNetRaw || activeNet, {
          hiddenGroups,
          preferEdgeIds: preferEdges,
        });
        if (summary) {
          let hl = borrowerHighlight(summary, borrowerEdgeMode, borrowerCategoryFocus);
          if (mode === "shock" && preferEdges?.length && borrowerEdgeMode === "material") {
            const shockTop = preferEdges.slice(0, 5);
            const edges = shockTop
              .map((eid) => activeNet.edges.find((x) => x.id === eid))
              .filter(Boolean) as typeof activeNet.edges;
            hl = {
              nodes: [...new Set([id, ...edges.flatMap((e) => [e.source, e.target])])],
              edges: edges.map((e) => e.id),
            };
          }
          return hl;
        }
      }

      if (mode === "shock" && preferEdges && preferEdges.length) {
        const edges = preferEdges
          .map((eid) => activeNet.edges.find((x) => x.id === eid))
          .filter(Boolean) as typeof activeNet.edges;
        const nodes = [...new Set([id, ...edges.flatMap((e) => [e.source, e.target])])];
        return { nodes, edges: edges.map((e) => e.id) };
      }
      const edges = activeNet.edges.filter((e) =>
        (e.source === id || e.target === id) && e.source_status === "VERIFIED");
      const nodes = [...new Set([id, ...edges.flatMap((e) => [e.source, e.target])])];
      if (pfShock.showUsKoreaOnly) {
        const region = new Map(activeNet.nodes.map((n) => [n.id, (n as { region?: string }).region || "US"]));
        const cross = edges.filter((e) => {
          const a = region.get(e.source); const b = region.get(e.target);
          return (a === "US" && b === "KR") || (a === "KR" && b === "US");
        });
        if (cross.length) {
          return { nodes: [...new Set([id, ...cross.flatMap((e) => [e.source, e.target])])], edges: cross.map((e) => e.id) };
        }
      }
      return { nodes, edges: edges.map((e) => e.id) };
    }
    // US→Korea path highlight (no company selected)
    if (ecosystem === "datacenter_pf" && pfShock.showUsKoreaOnly) {
      const region = new Map(activeNet.nodes.map((n) => [n.id, (n as { region?: string }).region || "US"]));
      const edges = activeNet.edges.filter((e) => {
        const a = region.get(e.source); const b = region.get(e.target);
        return (a === "US" && b === "KR") || (a === "KR" && b === "US");
      });
      const nodes = [...new Set(edges.flatMap((e) => [e.source, e.target]))];
      return { nodes, edges: edges.map((e) => e.id) };
    }
    return empty;
  }, [activeNet, activeNetRaw, net, selection, pathQuery, ecosystem, pfShock.showUsKoreaOnly, run, mode, borrowerEdgeMode, borrowerCategoryFocus, hiddenGroups]);

  const [entityPath, setEntityPath] = useState<PathResult | null>(null);
  useEffect(() => {
    setEntityPath(null);
    if (selection?.kind !== "node" || selection.id === origin || !activeNet) return;
    // Borrowers: do not auto-paint the full origin→node path (visual flood).
    if (ecosystem === "datacenter_pf" && isBorrowerNode(activeNet.nodes.find((n) => n.id === selection.id))) return;
    const seq = ++pathSeq.current;
    if (ecosystem === "datacenter_pf") {
      const path = shortestPath(activeNet, origin, selection.id);
      if (seq === pathSeq.current) setEntityPath(path);
      return;
    }
    api.path(origin, selection.id).then((r) => { if (seq === pathSeq.current) setEntityPath(r.path); }).catch(() => undefined);
  }, [api, selection, origin, ecosystem, activeNet]);
  const mapHighlight = useMemo(() => {
    if (highlight.nodes.length) return highlight;
    const selNode = selection?.kind === "node" ? activeNet?.nodes.find((n) => n.id === selection.id) : null;
    if (ecosystem === "datacenter_pf" && isBorrowerNode(selNode)) return highlight;
    if (entityPath) return { nodes: entityPath.nodes, edges: entityPath.edges };
    return highlight;
  }, [highlight, entityPath, selection, activeNet, ecosystem]);

  const [locateRequest, setLocateRequest] = useState<{ id: string; seq: number } | null>(null);
  const [pinnedNodeIds, setPinnedNodeIds] = useState<string[]>([]);
  const locateSeqRef = useRef(0);

  const selectNode = useCallback((id: string) => {
    setPathQuery(null);
    setBorrowerEdgeMode("material");
    setBorrowerCategoryFocus(null);
    setSelection({ kind: "node", id });
  }, []);

  /** Search / explicit locate: select + fly camera + pin through category filters. */
  const locateNode = useCallback((id: string) => {
    if (!activeNet?.nodes.some((n) => n.id === id)) {
      setToast("맵에 없는 노드입니다 (사업 메타만 존재할 수 있음)");
      return;
    }
    setView("map");
    setPathQuery(null);
    setBorrowerEdgeMode("material");
    setBorrowerCategoryFocus(null);
    setPinnedNodeIds([id]);
    setSelection({ kind: "node", id });
    locateSeqRef.current += 1;
    setLocateRequest({ id, seq: locateSeqRef.current });
  }, [activeNet]);

  const clearSearchPins = useCallback(() => {
    setPinnedNodeIds([]);
    setLocateRequest(null);
  }, []);

  const selectEdge = useCallback((id: string) => { setPathQuery(null); setSelection({ kind: "edge", id }); }, []);
  const selectContract = useCallback((id: string) => { setPathQuery(null); setView("map"); setSelection({ kind: "contract", id }); }, []);

  const selectedIsBorrower = useMemo(() => {
    if (selection?.kind !== "node" || !activeNet) return false;
    // While locating from search, always allow camera fly (handled via locateRequest).
    if (locateRequest?.id === selection.id) return false;
    return isBorrowerNode(activeNet.nodes.find((n) => n.id === selection.id));
  }, [selection, activeNet, locateRequest]);
  const findPath = useCallback((a: string, b: string) => {
    if (ecosystem === "datacenter_pf" && activeNet) {
      setPathQuery({ a, b, path: shortestPath(activeNet, a, b) });
      return;
    }
    api.path(a, b).then((r) => setPathQuery({ a, b, path: r.path })).catch(() => setPathQuery({ a, b, path: null }));
  }, [api, ecosystem, activeNet]);

  useEffect(() => {
    const onKey = (ev: KeyboardEvent) => {
      const tag = (ev.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
      if (ev.key === "Escape") { setSelection(null); setPathQuery(null); setMarketOpen(false); }
      if (!run) return;
      if (ev.key === "ArrowRight") { setPlaying(false); setStage((s) => Math.min(s + 1, lastStage)); }
      if (ev.key === "ArrowLeft") { setPlaying(false); setStage((s) => Math.max(s - 1, 0)); }
      if (ev.key === " ") { ev.preventDefault(); setPlaying((p) => !p); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [run, lastStage]);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    const show = (ev: Event) => {
      const el = (ev.target as HTMLElement)?.closest?.("[data-tip]") as HTMLElement | null;
      if (timer) clearTimeout(timer);
      if (!el) { setTip(null); return; }
      const text = el.getAttribute("data-tip") || "";
      if (!text) { setTip(null); return; }
      timer = setTimeout(() => {
        const r = el.getBoundingClientRect();
        const below = r.top < 90;
        setTip({ text, x: Math.min(Math.max(r.left + r.width / 2, 150), window.innerWidth - 150), y: below ? r.bottom + 6 : r.top - 6, below });
      }, 220);
    };
    const hide = () => { if (timer) clearTimeout(timer); setTip(null); };
    document.addEventListener("mouseover", show);
    document.addEventListener("focusin", show);
    document.addEventListener("scroll", hide, true);
    document.addEventListener("mousedown", hide);
    return () => {
      document.removeEventListener("mouseover", show);
      document.removeEventListener("focusin", show);
      document.removeEventListener("scroll", hide, true);
      document.removeEventListener("mousedown", hide);
    };
  }, []);

  useEffect(() => { if (selection) setPanelOpen(true); }, [selection]);

  useEffect(() => {
    if (mode !== "shock") setPlaying(false);
  }, [mode]);

  // Market View: load/refresh observed quotes only (never tied to shock bp).
  useEffect(() => {
    if (mode !== "market") return;
    const seq = ++quotesSeq.current;
    setQuotesBusy(true);
    if (ecosystem === "datacenter_pf") {
      const req = (api.kind === "http" || api.live)
        ? api.refreshQuotes({ ecosystem: "datacenter_pf" })
        : loadPfBundle().then((b) => b.quotes);
      req
        .then((q) => {
          if (seq !== quotesSeq.current) return;
          setPfQuotes(q);
          if (api.kind !== "http") {
            loadPfBundle().then((b) => { if (seq === quotesSeq.current) setPfBundle(b); }).catch(() => undefined);
          }
        })
        .catch(() => { if (seq === quotesSeq.current) setToast("PF 시세 조회 실패"); })
        .finally(() => { if (seq === quotesSeq.current) setQuotesBusy(false); });
      return;
    }
    api.refreshQuotes({ ecosystem: "semiconductor" })
      .then((q) => { if (seq === quotesSeq.current) setQuotes(q); })
      .catch(() => undefined)
      .finally(() => { if (seq === quotesSeq.current) setQuotesBusy(false); });
    api.refreshMarket().then((m) => m && setMarket(m)).catch(() => undefined);
  }, [mode, api, ecosystem]);

  const pricedCount = useMemo(
    () => (activeQuotes?.items || []).filter((q) => q.listed && q.price !== null && q.price !== undefined).length,
    [activeQuotes],
  );

  const refreshActiveQuotes = useCallback(() => {
    const seq = ++quotesSeq.current;
    setQuotesBusy(true);
    const applyMsg = (q: QuotesOverview) => {
      const st = q.refresh_status;
      if (st === "throttled") setToast(q.refresh_detail || "갱신 간격 제한 — 직전 시세 유지");
      else if (st === "partial") setToast(q.refresh_detail || "일부 종목만 갱신됨");
      else if (st === "error") setToast(q.refresh_detail || "시세 조회 오류");
      else if (st === "stale_retained") setToast(q.refresh_detail || "이전 시세 유지");
      else setToast(q.refresh_detail || "시세 조회 완료 (가격 변동 없어도 정상일 수 있음)");
    };
    if (ecosystem === "datacenter_pf") {
      const req = (api.kind === "http" || api.live)
        ? api.refreshQuotes({ ecosystem: "datacenter_pf" })
        : loadPfBundle().then((b) => ({
            ...b.quotes,
            retrieved_at: new Date().toISOString(),
            refresh_status: "stale_retained" as const,
            refresh_detail: "정적/로컬 모드 — quotes.json 재로드. 실시간 수집은 start.bat 백엔드를 사용하세요.",
          }));
      req
        .then((q) => {
          if (seq !== quotesSeq.current) return;
          setPfQuotes(q);
          applyMsg(q);
        })
        .catch(() => {
          if (seq !== quotesSeq.current) return;
          setPfQuotes((prev) => prev ? {
            ...prev,
            retrieved_at: new Date().toISOString(),
            refresh_status: "stale_retained",
            refresh_detail: "조회 실패 — 이전에 불러온 시세를 유지합니다.",
          } : prev);
          setToast("PF 시세 조회 실패 — 이전 데이터 유지");
        })
        .finally(() => { if (seq === quotesSeq.current) setQuotesBusy(false); });
      return;
    }
    api.refreshQuotes({ ecosystem: "semiconductor" })
      .then((q) => {
        if (seq !== quotesSeq.current) return;
        setQuotes(q);
        applyMsg(q);
      })
      .catch(() => {
        if (seq !== quotesSeq.current) return;
        setQuotes((prev) => prev ? {
          ...prev,
          retrieved_at: new Date().toISOString(),
          refresh_status: "stale_retained",
          refresh_detail: "조회 실패 — 이전에 불러온 시세를 유지합니다.",
        } : prev);
        setToast("시세 조회 실패 — 이전 데이터 유지");
      })
      .finally(() => { if (seq === quotesSeq.current) setQuotesBusy(false); });
  }, [api, ecosystem]);

  if (loadErr) {
    return (
      <div className="boot boot-error">
        <div className="wordmark">{title.brand}</div>
        <p>네트워크 데이터를 불러오지 못했습니다: {loadErr}</p>
        <p className="muted">권장: 프로젝트 루트에서 <code>start.bat</code> (백엔드+프론트). 정적 미리보기: <code>preview.bat</code>.</p>
      </div>
    );
  }
  if (!net || !form || !inst) return (<div className="boot"><div className="wordmark">{title.brand}</div><p className="muted">불러오는 중…</p></div>);
  if (ecosystem === "datacenter_pf" && !pfBundle) {
    return (
      <div className={`boot ${pfLoad.state === "error" ? "boot-error" : ""}`} role={pfLoad.state === "error" ? "alert" : "status"}>
        <div className="wordmark">{title.brand}</div>
        {pfLoad.state === "error" ? (
          <>
            <p>국내 AI 데이터센터 PF 데이터를 불러오지 못했습니다.</p>
            <p className="muted">{pfLoad.message}</p>
            <div className="boot-actions">
              <button type="button" className="btn" onClick={loadPf}>다시 시도</button>
              <button type="button" className="btn-text" onClick={() => switchEcosystem("semiconductor")}>AI 반도체 생태계로 돌아가기</button>
            </div>
          </>
        ) : <p className="muted">국내 AI 데이터센터 PF 데이터 불러오는 중…</p>}
      </div>
    );
  }
  if (!activeNet) return (<div className="boot"><div className="wordmark">{title.brand}</div><p className="muted">불러오는 중…</p></div>);

  const sofr = form.sofr ?? net.financials.market_inputs.sofr_pct;
  let exText = "기존 금리 확인 불가";
  try { const ex = existingRate(inst, form.basis, sofr); exText = `기존 ${ex.rate_pct}%`; } catch { /* shown as block reason below */ }
  const amount = form.amount ?? inst.principal_usd_m;
  const blockReason = amount === null || amount === undefined
    ? `${inst.name}: 2026.6.30 기준 잔액이 공시되지 않았습니다. 고급 변수에서 차환 대상 금액을 입력하세요.`
    : exText === "기존 금리 확인 불가" ? `${inst.name}: 기존 금리(표면·유효)가 모두 공시되지 않아 계산할 수 없습니다.` : null;
  const summary = `CoreWeave ${inst.name} ${amount !== null && amount !== undefined ? usdM(amount) : "(금액 입력 필요)"}을 ${form.newRate}%로 차환한다고 가정합니다 (${exText}${form.success < 1 ? ` · 성공 ${Math.round(form.success * 100)}%` : ""}).`;
  const stale = !!run && run.kind === "refinancing" && JSON.stringify(run.params) !== JSON.stringify(toParams(form));
  const shockResult = run?.kind === "rate_shock" ? run.result : null;
  /** Inputs moved but the debounced engine has not produced the new result yet. */
  const quotesLive = api.kind === "http" || !!api.live;
  const shockPending = mode === "shock" && (ecosystem === "datacenter_pf"
    ? !!run && run.kind === "pf_shock" && JSON.stringify(run.params) !== JSON.stringify(pfShock)
    : !!run && run.kind === "rate_shock" && JSON.stringify(run.params) !== JSON.stringify(shock));
  const pfShockResult = run?.kind === "pf_shock" ? run.result : null;

  const idleShock = run?.kind === "pf_shock"
    ? `PF Shock · CW ${run.result.pf.coreweave_distress || "normal"} · CAPEX ${run.result.pf.hyperscaler_capex_pct}% · 금리 +${run.result.pf.rate_bp}bp · 계량 ${run.result.pf.measurable_projects}`
    : run?.kind === "rate_shock"
      ? `Shock View · ${run.result.benchmark.label_en} ${run.result.summary.shock_bp > 0 ? "+" : ""}${run.result.summary.shock_bp}bp · 직접 ${run.result.summary.direct_measurable} · 잠재 간접 ${run.result.summary.potential_indirect}`
      : ecosystem === "datacenter_pf"
        ? "PF Shock · 좌측에서 금리·GPU 임대·CAPEX를 조절하세요"
        : "Shock View · 좌측에서 금리 충격을 조절하세요";

  const focusName = displayName(nodeMap.get(origin) || { id: origin, name: origin }) || origin;
  const isPf = ecosystem === "datacenter_pf";
  const statDefs: StatDef[] = [
    { key: "ent", label: isPf ? "기업·SPC" : "Entities", value: stats?.entities,
      tip: isPf ? "국내 AI 데이터센터 PF 지도에 등록된 회사·SPC·펀드 수 (사업장·허가지는 제외)" : "공개자료로 확인되어 등록된 기업·기관 수 (CoreWeave 포함). 생태계 전체 규모가 아닙니다." },
    { key: "dir", label: "Direct", value: stats?.direct, tip: `현재 초점(${focusName})과 직접 연결된(1단계) 기업·기관 수` },
    { key: "ind", label: "Indirect", value: stats?.indirect, tip: `현재 초점(${focusName})과 다른 기업을 거쳐 연결된(2단계 이상) 기업·기관 수` },
    { key: "ctr", label: isPf ? "US PF 계약" : "Contracts", value: stats?.financing_contracts,
      tip: isPf
        ? "미국 AI 데이터센터 프로젝트의 공시 금융계약 수 (차주: Galaxy·Applied Digital·Core Scientific SPC). CoreWeave 자체 차입이 아닙니다. 국내 PF 대출은 관계(엣지)로 별도 표시됩니다."
        : "CoreWeave 10-Q로 확인된 금융계약(대출·채권·전환사채·리볼버) 수. 공급사 금융 제외. 우측 Contracts 목록은 공급사 금융을 포함할 수 있습니다." },
    { key: "inds", label: "Industrial", value: stats?.industrial_relationships, tip: "확인된 산업 관계(공급·고객·데이터센터·약정) 수" },
  ];
  const scopeText = (
    <>
      {isPf ? "국내 AI 데이터센터 PF · 회사 중심 관계망" : "미국 AI 반도체 · CoreWeave 중심 관계망"}
      {" · 초점 "}<b>{focusName}</b>
      {activeNet.meta?.as_of ? <> · 자료 기준일 <span className="num">{activeNet.meta.as_of}</span></> : null}
    </>
  );

  return (
    <div className={`app view-${view} mode-${mode} eco-${ecosystem} ${panelOpen ? "" : "panel-closed"}`}>
      <TopBar view={view} onView={setView} mode={mode} onMode={setMode} panelOpen={panelOpen} onTogglePanel={() => setPanelOpen((o) => !o)}
        statDefs={statDefs} brand={title.brand} brandSub={title.sub} scope={scopeText} onGuide={() => setGuideOpen(true)}>
        <EcosystemSelector value={ecosystem} onChange={switchEcosystem} pfLoad={pfLoad} />
      </TopBar>
      {ecosystem === "datacenter_pf" && pfBundle ? (
        <PfScenarioBuilder
          mode={mode}
          net={activeNet}
          projects={pfBundle.projects}
          pfShock={pfShock}
          onPfShock={(x) => setPfShock((s) => ({ ...s, ...x }))}
          shockResult={mode === "shock" ? pfShockResult : null}
          quotes={activeQuotes}
          quotesBusy={quotesBusy}
          onRefreshQuotes={refreshActiveQuotes}
          hiddenGroups={hiddenGroups}
          onToggleGroup={(g) => setHiddenGroups((h) => (h.includes(g) ? h.filter((x) => x !== g) : [...h, g]))}
          visuals={visuals}
          selectedId={selection?.kind === "node" ? selection.id : null}
          onSelect={selectNode}
          onLocate={locateNode}
          onClearSearchPins={clearSearchPins}
          onClearSelection={() => { setSelection(null); setPathQuery(null); clearSearchPins(); }}
          shockPending={shockPending}
          quotesLive={quotesLive}
        />
      ) : (
        <ScenarioBuilder
          mode={mode}
          net={net}
          quotes={activeQuotes}
          quotesBusy={quotesBusy}
          onRefreshQuotes={refreshActiveQuotes}
          shock={shock}
          onShock={(x) => setShock((s) => ({ ...s, ...x }))}
          shockResult={mode === "shock" ? shockResult : null}
          form={form}
          onForm={(x) => setForm((f) => (f ? { ...f, ...x } : f))}
          summary={summary}
          canRunRefi={!blockReason} blockReason={blockReason} busy={busy} stale={stale}
          onRunRefi={() => { setView("map"); doRunRefi(); }}
          hiddenGroups={hiddenGroups}
          onToggleGroup={(g) => setHiddenGroups((h) => (h.includes(g) ? h.filter((x) => x !== g) : [...h, g]))}
          visuals={visuals} selectedId={selection?.kind === "node" ? selection.id : null} onSelect={selectNode}
          onOpenContract={selectContract}
          shockPending={shockPending}
          quotesLive={quotesLive}
        />
      )}
      <main className="stage-area">
        {view === "sources" ? <SourcesView net={activeNet} sources={ecosystem === "datacenter_pf" ? { sources: activeNet.sources, status_counts: {}, meta: activeNet.meta } : sources} onSelectNode={(id) => { setView("map"); selectNode(id); }} onSelectContract={selectContract} projects={ecosystem === "datacenter_pf" ? pfBundle?.projects.projects : undefined} /> : null}
        <MapErrorBoundary>
          <UniverseView
            hidden={view === "sources"}
            net={activeNet}
            origin={origin}
            visuals={visuals}
            activeEdges={activeEdges}
            usedEdges={usedEdges}
            banner={banner}
            mode={mode}
            staged={mode === "shock"}
            focusIds={focusIds}
            focusKey={mode === "shock" && run ? `${runNo}:${stage}` : ""}
            quotesDemo={!!activeQuotes?.demo}
            quotes={activeQuotes}
            idleLabel={mode === "market"
              ? (ecosystem === "datacenter_pf"
                ? `PF Market · 공시·관측 지표 · 가설 Shock과 분리 · 프로젝트 ${pfBundle?.projects.projects.length ?? 0}`
                : (pricedCount
                  ? `Market View · 관측 주가 등락률 (상승 빨강 · 하락 파랑) · ${pricedCount}개 종목`
                  : "Market View · 관측 시세 로딩 중이거나 미수집 · 좌측 목록 · 우측 패널 · TradingView"))
              : mode === "shock" ? idleShock
              : `Network View · ${ecosystem === "datacenter_pf" ? "PF · " : ""}초점 ${(nodeMap.get(origin)?.name_ko && /[가-힣]/.test(nodeMap.get(origin)!.name_ko!) ? nodeMap.get(origin)!.name_ko : nodeMap.get(origin)?.name) || origin} · 관계 ${activeNet.edges.length} · 기업 ${activeNet.nodes.length}`}
            selection={selection}
            highlight={mapHighlight}
            hasRun={mode === "shock" && !!run}
            hiddenCats={hiddenCats}
            onToggleCat={(c) => setHiddenCats((h) => (h.includes(c) ? h.filter((x) => x !== c) : [...h, c]))}
            hiddenGroups={hiddenGroups}
            speed={speed}
            resetKey={mode === "shock" ? String(runNo) : `view-${mode}-${ecosystem}`}
            preserveCameraOnSelect={selectedIsBorrower && locateRequest?.id !== selection?.id}
            locateRequest={locateRequest}
            pinnedNodeIds={pinnedNodeIds}
            onSelectNode={selectNode}
            onSelectEdge={selectEdge}
            onSelectNone={() => { setSelection(null); setPathQuery(null); clearSearchPins(); }}
            nodeMap={nodeMap}
          />
        </MapErrorBoundary>
        {toast ? <div className="toast" role="status">{toast}</div> : null}
        {guideOpen ? <GuideCard onClose={() => setGuideOpen(false)} onStartPf={() => { setView("map"); switchEcosystem("datacenter_pf"); }} /> : null}
      </main>
      <DetailPanel
        api={api}
        quotesLive={quotesLive}
        net={activeNet}
        origin={origin}
        onSetOrigin={(id) => {
          setOrigin(id);
          setMode("network");
          setView("map");
          setToast(`${(nodeMap.get(id)?.name_ko && /[가-힣]/.test(nodeMap.get(id)!.name_ko!) ? nodeMap.get(id)!.name_ko : nodeMap.get(id)?.name) || id}을(를) 네트워크 초점으로 설정했습니다`);
        }}
        nodeMap={nodeMap}
        stats={stats}
        quotes={activeQuotes}
        quotesBusy={quotesBusy}
        onRefreshQuotes={refreshActiveQuotes}
        selection={selection}
        run={run}
        mode={mode}
        stage={stage}
        entityPath={entityPath}
        pathQuery={pathQuery}
        onFindPath={findPath}
        onClearPath={() => setPathQuery(null)}
        onSelectNode={selectNode}
        onSelectEdge={selectEdge}
        onSelectContract={selectContract}
        onUseContract={(id) => { setForm((f) => (f ? { ...f, instrumentId: id, amount: null, refiDate: null } : f)); setToast("차환 대상 차입금을 바꿨습니다. 좌측에서 상세 차환 분석을 여세요."); }}
        onClose={() => { setSelection(null); setPathQuery(null); }}
        onCollapse={() => setPanelOpen(false)}
        pfProjects={ecosystem === "datacenter_pf" ? pfBundle?.projects.projects : undefined}
        pfShockResult={pfShockResult}
        pfLedgerNet={ecosystem === "datacenter_pf" ? activeNetRaw ?? undefined : undefined}
        borrowerEdgeMode={borrowerEdgeMode}
        onBorrowerEdgeMode={setBorrowerEdgeMode}
        borrowerCategoryFocus={borrowerCategoryFocus}
        onBorrowerCategoryFocus={setBorrowerCategoryFocus}
        hiddenGroups={hiddenGroups}
      />
      {mode === "shock" ? (
        <BottomBar
          run={run}
          stage={stage}
          lastStage={lastStage}
          playing={playing}
          speed={speed}
          onPlayPause={() => {
            if (!run) return;
            if (playing) { setPlaying(false); return; }
            // Replay from clean baseline using CURRENT scenario result (already tied to latest params).
            if (stage >= lastStage) {
              setFxGen((x) => x + 1);
              setStage(0);
              setPlaying(true);
              return;
            }
            setPlaying(true);
          }}
          onPrev={() => { setPlaying(false); setStage((s) => Math.max(0, s - 1)); }}
          onNext={() => { setPlaying(false); setStage((s) => Math.min(lastStage, s + 1)); }}
          onSeek={(s) => { setPlaying(false); setStage(s); }}
          onReset={reset}
          onSpeed={setSpeed}
        />
      ) : (
        <footer className="bb bb-market" aria-label={mode === "market" ? "Market 요약" : "Network"}>
          <div className="bb-transport">
            <p className="bb-idle-lbl">
              {mode === "market"
                ? `MARKET · 관측 시세 ${pricedCount}개 · 금리 충격 슬라이더와 무관`
                : "NETWORK · 관계 구조만 표시 · Shock 탭에서 시나리오"}
            </p>
          </div>
          {mode === "market" && activeQuotes ? (
            <dl className="kpi-strip">
              <div className="kpi"><dt>Listed</dt><dd className="num">{activeQuotes.items.filter((q) => q.listed).length}</dd></div>
              <div className="kpi"><dt>Priced</dt><dd className="num">{pricedCount}</dd></div>
              <div className="kpi"><dt>Up</dt><dd className="num is-up">{activeQuotes.items.filter((q) => (q.change_pct ?? 0) > 0 && q.price != null).length}</dd></div>
              <div className="kpi"><dt>Down</dt><dd className="num is-down">{activeQuotes.items.filter((q) => (q.change_pct ?? 0) < 0 && q.price != null).length}</dd></div>
            </dl>
          ) : <div className="kpi-strip" />}
        </footer>
      )}
      {tip ? <div className={`gtip ${tip.below ? "below" : ""}`} style={{ left: tip.x, top: tip.y }} role="tooltip">{tip.text}</div> : null}
      {marketOpen ? (
        <MarketPanel
          market={activeMarket}
          isDemo={api.kind === "local"}
          snapshotOnly={api.kind === "static" && !api.live}
          onClose={() => setMarketOpen(false)}
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            if (ecosystem === "datacenter_pf") {
              loadPfBundle().then((b) => { setPfBundle(b); }).catch(() => setToast("PF 시장 데이터 갱신 실패")).finally(() => setRefreshing(false));
              return;
            }
            api.refreshMarket().then((m) => m && setMarket(m)).catch(() => setToast("시장 데이터 갱신 요청 실패")).finally(() => setRefreshing(false));
          }}
        />
      ) : null}
    </div>
  );
}
