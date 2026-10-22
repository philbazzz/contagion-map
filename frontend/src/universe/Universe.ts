/**
 * Universe — dependency-free 3D network renderer on a 2D canvas.
 *
 * Perspective projection, orbit camera, additive "bloom" glow, depth-sorted
 * star nodes, dashed/solid relation lines, flowing particles and shock waves.
 * Framework-agnostic: React talks to it through the public methods below.
 */
import type { NetEdge, NetNode, NodeVisual } from "../types";

type V3 = { x: number; y: number; z: number };
type Proj = { sx: number; sy: number; z: number; s: number; ok: boolean };

export interface UniverseCallbacks {
  onHoverNode?: (id: string | null, x: number, y: number) => void;
  onHoverEdge?: (id: string | null, x: number, y: number) => void;
  onSelectNode?: (id: string) => void;
  onSelectEdge?: (id: string) => void;
  onSelectNone?: () => void;
}

export const GROUP_COLORS: Record<string, string> = {
  ai_infra: "#8DF1FF",
  semiconductor: "#B39DFF",
  server: "#7EE8C2",
  cloud: "#6FA8FF",
  customer: "#6FA8FF",
  financial: "#F2C14E",
  datacenter: "#86E3A6",
  project_finance: "#C4A882",
  demo: "#FF7FC3",
  // Korean PF ecosystem clusters (distinct hues, same planetary style)
  kr_construction: "#7BC47F",
  kr_trust: "#D4B483",
  kr_savings: "#E8A87C",
  kr_cooperative: "#C9A66B",
  kr_bank: "#F2C14E",
  kr_securities: "#E6C35C",
  kr_am: "#B8A0D4",
  kr_insurance: "#9BB8E8",
  kr_operator: "#6EC9B8",
};

// Shock View statuses. Critical orange-crimson = modeled severe stress warning, NOT a default event.
export const STATUS_COLORS: Record<string, string> = {
  shock_origin: "#FF8A3D",
  stress_normal: "#FF9A4A",
  stress_moderate: "#FFB020",
  stress_high: "#FF6B35",
  stress_critical: "#E85D4C",
  contract_party: "#F2C14E",
  assumed: "#FFB020",
  potential: "#7C8AA8",
  insufficient: "#5A6578",
  // Market View (observed prices, Korean convention: up = red, down = blue). Never used by the Shock View.
  mk_up: "#F0605D",
  mk_down: "#4D8DF5",
  mk_flat: "#AEB8C8",
  mk_na: "#3A4458",
};

const STRESS_RANK: Record<string, number> = {
  stress_normal: 1,
  shock_origin: 1,
  stress_moderate: 2,
  stress_high: 3,
  stress_critical: 4,
};
const MARKET = (s: string) => s.startsWith("mk_");

export type EdgeCat = "financial" | "supply" | "customer" | "facility";
export const EDGE_CATEGORY = (e: NetEdge): EdgeCat => {
  if (e.impact_channel === "financial" || e.impact_channel === "equity") return "financial";
  if (e.impact_channel === "supply_chain") return "supply";
  if (e.impact_channel === "facility") return "facility";
  return "customer";
};

const EDGE_COLORS: Record<string, string> = {
  FINANCING_PARTICIPATION: "#F2C14E",
  COLLATERAL_AGENT: "#BFA96A",
  EQUITY_INVESTMENT: "#5EE6D0",
  SUPPLIER: "#B39DFF",
  INDIRECT_SUPPLY_CHAIN: "#B39DFF",
  CUSTOMER: "#6FA8FF",
  LESSOR: "#86E3A6",
  CAPACITY_BACKSTOP: "#8899BB",
  STRATEGIC_PARTNERSHIP: "#7EC8E3",
  POWER_SUPPLY: "#F0C27A",
};

const GROUP_DIRS: Record<string, V3> = {
  semiconductor: { x: 1, y: 0.08, z: -0.15 },
  server: { x: 0.55, y: -0.25, z: 1 },
  cloud: { x: -1, y: -0.1, z: 0.25 },
  customer: { x: -1, y: -0.1, z: 0.25 },
  datacenter: { x: -0.35, y: -1, z: 0.45 },
  financial: { x: -0.15, y: 1, z: -0.35 },
  project_finance: { x: 0.2, y: 0.55, z: -0.85 },
  ai_infra: { x: 0.75, y: 0.35, z: 0.55 },
  demo: { x: -0.2, y: -1, z: -0.2 },
  // Korean clusters fan into the lower-left / lower hemisphere so US stays readable at center-right
  kr_construction: { x: -0.85, y: -0.55, z: 0.2 },
  kr_operator: { x: -0.7, y: -0.25, z: -0.45 },
  kr_trust: { x: -0.55, y: 0.35, z: -0.75 },
  kr_savings: { x: -0.95, y: 0.15, z: 0.55 },
  kr_cooperative: { x: -0.75, y: 0.55, z: 0.35 },
  kr_bank: { x: -0.4, y: 0.85, z: -0.15 },
  kr_securities: { x: -0.25, y: 0.7, z: 0.55 },
  kr_am: { x: -0.6, y: 0.45, z: 0.75 },
  kr_insurance: { x: -0.35, y: 0.55, z: 0.85 },
};

// ---------- tiny vector + color helpers ----------
const add = (a: V3, b: V3): V3 => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z });
const sub = (a: V3, b: V3): V3 => ({ x: a.x - b.x, y: a.y - b.y, z: a.z - b.z });
const mul = (a: V3, k: number): V3 => ({ x: a.x * k, y: a.y * k, z: a.z * k });
const dot = (a: V3, b: V3) => a.x * b.x + a.y * b.y + a.z * b.z;
const cross = (a: V3, b: V3): V3 => ({ x: a.y * b.z - a.z * b.y, y: a.z * b.x - a.x * b.z, z: a.x * b.y - a.y * b.x });
const len = (a: V3) => Math.hypot(a.x, a.y, a.z) || 1e-9;
const norm = (a: V3) => mul(a, 1 / len(a));
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

function hexToRgb(h: string): [number, number, number] {
  const n = parseInt(h.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
const rgba = (c: [number, number, number], a: number) =>
  `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${Math.max(0, Math.min(1, a)).toFixed(3)})`;

function seeded(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

interface Frag {
  ang: number; dist: number; spin: number; size: number; life: number;
}
interface NodeRT {
  n: NetNode;
  pos: V3;
  color: [number, number, number];
  target: [number, number, number];
  scale: number;
  dim: number;
  visual: NodeVisual;
  proj: Proj;
  /** Peak stress rank seen; used for crack geometry intensity. */
  stressPeak: number;
  /** One-shot shatter clock (seconds since critical crossed); null if intact. */
  shatterT: number | null;
  frags: Frag[];
  /** Last fx_gen applied — replay bumps this to clear stuck shatter. */
  fxGen: number;
}
interface EdgeRT {
  e: NetEdge;
  a: NodeRT;
  b: NodeRT;
  bend: number;
  seed: number;
  dim: number;
  pts?: { x0: number; y0: number; cx: number; cy: number; x1: number; y1: number; s: number };
}
interface Wave { node: NodeRT; t0: number; color: [number, number, number]; dur: number; }

export class Universe {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private cb: UniverseCallbacks;
  private nodes: NodeRT[] = [];
  private nodeMap = new Map<string, NodeRT>();
  private edges: EdgeRT[] = [];
  private origin = "";
  private stars: { d: V3; m: number; tw: number }[] = [];
  private dust: { p: V3; v: V3; m: number }[] = [];
  private W = 0;
  private H = 0;
  private dpr = 1;
  private raf = 0;
  private last = 0;
  private time = 0;
  private reduceMotion = false;

  // camera
  private yaw = 0.62;
  private pitch = 0.3;
  private dist = 1250;
  private target: V3 = { x: 0, y: 0, z: 0 };
  private goal: { yaw?: number; pitch?: number; dist?: number; target?: V3; slow?: boolean } | null = null;
  private camPos: V3 = { x: 0, y: 0, z: 0 };
  private right: V3 = { x: 1, y: 0, z: 0 };
  private up: V3 = { x: 0, y: 1, z: 0 };
  private fwd: V3 = { x: 0, y: 0, z: 1 };
  private focal = 800;
  private autoRotate = false;
  private idleSince = 0;

  // interaction state
  private hoverNode: string | null = null;
  private hoverEdge: string | null = null;
  private selectedNode: string | null = null;
  private selectedEdge: string | null = null;
  private pathNodes = new Set<string>();
  private pathEdges = new Set<string>();
  private hiddenCats = new Set<string>();
  private hiddenGroups = new Set<string>();
  /** Search / locate: keep these node ids drawable even if their group filter is off. */
  private pinnedVisible = new Set<string>();
  private activeEdges = new Set<string>();
  private usedEdges: Set<string> | null = null;
  private activeMode: "financial" | "industrial" = "financial";
  private activeSince = 0;
  private waves: Wave[] = [];
  private speed = 1;
  private pointers = new Map<number, { x: number; y: number }>();
  private dragMoved = false;
  private downAt = { x: 0, y: 0 };
  private pinchStart = 0;
  private dims = { banner: "" };
  // staged playback: each newly active edge draws itself from source to target, then the target lights up
  private edgeStart = new Map<string, number>();
  private pending: { node: NodeRT; visual: NodeVisual; at: number }[] = [];
  private focusSet = new Set<string>();
  private travel = 1.8;
  private radius = 600;
  /** Soft floor / hard ceiling for orbit distance. Ceiling scales with network radius so large PF maps can fully fit. */
  private minDist = 220;
  private maxDist = 12000;

  constructor(canvas: HTMLCanvasElement, cb: UniverseCallbacks = {}) {
    this.canvas = canvas;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Canvas 2D not supported");
    this.ctx = ctx;
    this.cb = cb;
    this.reduceMotion = typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
    this.makeStars();
    this.bind();
    this.resize();
    this.last = performance.now();
    this.raf = requestAnimationFrame(this.frame);
  }

  // ================= public API =================
  /** Topology signature — skip full layout when only metadata/visuals change. */
  private dataSig = "";

  setData(nodes: NetNode[], edges: NetEdge[], origin: string) {
    const sig = `${origin}|${nodes.length}|${edges.length}|${nodes.map((n) => n.id).join(",")}|${edges.map((e) => e.id).join(",")}`;
    const sameTopo = sig === this.dataSig && this.nodes.length === nodes.length;
    this.origin = origin;

    if (sameTopo) {
      // Preserve positions & camera — only refresh node/edge payloads (avoids black flash on re-select).
      const byId = new Map(this.nodes.map((r) => [r.n.id, r]));
      for (const n of nodes) {
        const r = byId.get(n.id);
        if (r) r.n = n;
      }
      const edgeById = new Map(this.edges.map((er) => [er.e.id, er]));
      for (const e of edges) {
        const er = edgeById.get(e.id);
        if (er) er.e = e;
      }
      return;
    }
    this.dataSig = sig;

    // Preserve prior positions for shared node ids (mode switch / incremental data).
    const prevPos = new Map(this.nodes.map((r) => [r.n.id, r.pos]));
    const layout = this.computeLayout(nodes, edges, origin);
    // Guarantee every node has a finite position (missing layout → black/NaN camera).
    let orphan = 0;
    const safePos = (id: string): V3 => {
      const keep = prevPos.get(id);
      if (keep && Number.isFinite(keep.x) && Number.isFinite(keep.y) && Number.isFinite(keep.z)) return keep;
      const p = layout.get(id);
      if (p && Number.isFinite(p.x) && Number.isFinite(p.y) && Number.isFinite(p.z)) return p;
      const a = orphan++ * Math.PI * (3 - Math.sqrt(5));
      return { x: Math.cos(a) * 420, y: ((orphan * 0.17) % 1) - 0.5, z: Math.sin(a) * 420 };
    };
    this.nodes = nodes.map((n) => {
      const c = hexToRgb(GROUP_COLORS[n.group] || "#cfd8ea");
      return {
        n, pos: safePos(n.id), color: [...c] as [number, number, number], target: c, scale: 1, dim: 1,
        visual: { status: "normal" }, proj: { sx: 0, sy: 0, z: 0, s: 0, ok: false },
        stressPeak: 0, shatterT: null, frags: [], fxGen: 0,
      };
    });
    this.nodeMap = new Map(this.nodes.map((r) => [r.n.id, r]));
    const pairCount = new Map<string, number>();
    const pairIdx = new Map<string, number>();
    for (const e of edges) {
      const k = [e.source, e.target].sort().join("|");
      pairCount.set(k, (pairCount.get(k) || 0) + 1);
    }
    const rnd = seeded(7);
    this.edges = edges
      .filter((e) => this.nodeMap.has(e.source) && this.nodeMap.has(e.target))
      .map((e) => {
        const k = [e.source, e.target].sort().join("|");
        const n = pairCount.get(k)!;
        const i = pairIdx.get(k) || 0;
        pairIdx.set(k, i + 1);
        const flip = e.source < e.target ? 1 : -1;
        return { e, a: this.nodeMap.get(e.source)!, b: this.nodeMap.get(e.target)!, bend: n > 1 ? (i - (n - 1) / 2) * 0.22 * flip : 0, seed: rnd(), dim: 1 };
      });
    const radii = this.nodes.map((r) => len(r.pos)).filter((x) => Number.isFinite(x));
    this.radius = Math.max(300, ...(radii.length ? radii : [300]));
    // Large PF graphs: never allow the camera inside the constellation (looks like a black void).
    this.minDist = Math.max(520, this.radius * 0.32);
    this.maxDist = Math.max(12000, this.radius * 8 + 2400);
    this.dist = Math.max(this.minDist, Math.min(this.maxDist, this.dist || this.fitDist()));
    // After layout, frame the full graph with padding so top/bottom nodes are not clipped.
    this.resetView();
  }

  /**
   * Apply per-node visuals and the edges that carry the shock in this stage.
   * staged=true (Shock View playback): every edge that becomes active travels from source to target one after
   * another; the target only shows its new state when the light arrives, so the order of propagation is visible.
   */
  setSimState(states: Record<string, NodeVisual> | null, activeEdges: string[], mode: "financial" | "industrial", banner = "", staged = false) {
    const prevActive = this.activeEdges;
    const fresh = activeEdges.filter((id) => !prevActive.has(id));
    const travel = this.travel / this.speed;
    const stagger = 0.55 / this.speed;
    const arrival = new Map<string, number>();
    this.pending = [];
    if (staged && !this.reduceMotion) {
      fresh.forEach((id, i) => {
        const start = this.time + i * stagger;
        this.edgeStart.set(id, start);
        const er = this.edges.find((x) => x.e.id === id);
        if (er) {
          const tgt = er.e.target === this.origin ? er.e.source : er.e.target;
          arrival.set(tgt, Math.max(arrival.get(tgt) ?? 0, start + travel));
        }
      });
    } else {
      for (const id of activeEdges) this.edgeStart.set(id, this.time - 10);
    }
    for (const id of [...this.edgeStart.keys()]) if (!activeEdges.includes(id)) this.edgeStart.delete(id);
    this.focusSet = new Set(states && !Object.values(states).every((v) => MARKET(v.status)) ? Object.keys(states) : []);
    for (const r of this.nodes) {
      const v = states?.[r.n.id] || { status: "normal" };
      const at = arrival.get(r.n.id);
      const changed = v.status !== r.visual.status || v.label !== r.visual.label
        || v.intensity !== r.visual.intensity || v.stress !== r.visual.stress;
      if (at !== undefined && changed) this.pending.push({ node: r, visual: v, at });
      else this.applyVisual(r, v, staged);
    }
    const same = activeEdges.length === this.activeEdges.size && activeEdges.every((id) => this.activeEdges.has(id));
    if (!same) this.activeSince = this.time;
    this.activeEdges = new Set(activeEdges);
    this.activeMode = mode;
    this.dims.banner = banner;
  }

  private applyVisual(r: NodeRT, v: NodeVisual, wave: boolean) {
    const gen = v.fx_gen ?? 0;
    if (gen !== r.fxGen) {
      r.fxGen = gen;
      r.shatterT = null;
      r.frags = [];
      r.stressPeak = 0;
    }
    const was = r.visual.status;
    const wasRank = STRESS_RANK[was] || 0;
    const nowRank = STRESS_RANK[v.status] || 0;
    r.visual = v;
    const sc = STATUS_COLORS[v.status];
    r.target = sc ? hexToRgb(sc) : hexToRgb(GROUP_COLORS[r.n.group] || "#cfd8ea");
    r.stressPeak = Math.max(r.stressPeak || 0, nowRank, v.intensity ? Math.min(4, v.intensity * 2.2) : 0);

    // Reversible: dropping below critical clears shatter; crossing into critical triggers once.
    // Replay (fx_gen bump) clears shatter first so critical can re-fire even if status was already critical.
    if (nowRank < 4) {
      r.shatterT = null;
      r.frags = [];
      if (nowRank < wasRank) r.stressPeak = nowRank;
    } else if ((wasRank < 4 || r.shatterT === null) && nowRank >= 4) {
      r.shatterT = this.time;
      const rnd = seeded((r.n.id.length * 9973) ^ 0xc2ac4);
      r.frags = Array.from({ length: this.reduceMotion ? 4 : 14 }, () => ({
        ang: rnd() * Math.PI * 2,
        dist: 0,
        spin: (rnd() - 0.5) * 4,
        size: 0.18 + rnd() * 0.35,
        life: 1,
      }));
      this.waves.push({ node: r, t0: this.time, color: hexToRgb("#E85D4C"), dur: 3.2 });
    }

    if (wave && was !== v.status && !MARKET(v.status) && v.status !== "normal") {
      const dur = nowRank >= 4 ? 3.0 : nowRank >= 3 ? 2.4 : v.status.startsWith("stress_") || v.status === "shock_origin" ? 2.2 : 1.6;
      this.waves.push({ node: r, t0: this.time, color: hexToRgb(sc || "#FF8A3D"), dur });
    }
  }

  /** Frame a set of entities (the ones involved in the current stage) with a slow, readable camera move. */
  focusNodes(ids: string[]) {
    const pts = ids.map((id) => this.nodeMap.get(id)?.pos).filter(Boolean) as V3[];
    if (!pts.length) return;
    const c = mul(pts.reduce((acc, p) => add(acc, p), { x: 0, y: 0, z: 0 }), 1 / pts.length);
    const rad = Math.max(160, ...pts.map((p) => len(sub(p, c))));
    const half = 0.5 * Math.min(this.W, this.H);
    const dist = Math.max(560, Math.min(this.maxDist, rad * (this.focal / half) * 1.55 + 320));
    this.goal = { target: c, dist, pitch: Math.min(0.22, this.pitch), slow: true };
    this.idleSince = this.time;
  }

  setSelection(nodeId: string | null, edgeId: string | null = null) {
    this.selectedNode = nodeId;
    this.selectedEdge = edgeId;
  }

  /** Edges used by the current calculation. Others are drawn as faint reference lines. null = no run. */
  setUsedEdges(ids: string[] | null) {
    this.usedEdges = ids ? new Set(ids) : null;
  }

  setHighlightPath(nodes: string[], edges: string[]) {
    this.pathNodes = new Set(nodes);
    this.pathEdges = new Set(edges);
  }

  /** Screen-only filters: relationship layers and entity classes (never change a calculation). */
  setFilters(hiddenCategories: string[], hiddenGroups: string[]) {
    this.hiddenCats = new Set(hiddenCategories);
    this.hiddenGroups = new Set(hiddenGroups);
  }

  /** Temporarily force-draw nodes (e.g. search hit behind a category filter). */
  setPinnedVisible(ids: string[]) {
    this.pinnedVisible = new Set(ids.filter(Boolean));
  }

  setSpeed(x: number) { this.speed = Math.max(0.25, Math.min(4, x)); }
  setAutoRotate(on: boolean) { this.autoRotate = on; }

  /**
   * Fly toward a node while keeping the camera OUTSIDE dense clusters (inside = black void).
   * preferTarget: search/locate — frame the node itself rather than midpoint with origin.
   */
  focusNode(id: string, opts?: { preferTarget?: boolean }) {
    const r = this.nodeMap.get(id);
    if (!r?.pos || !Number.isFinite(r.pos.x)) return;
    this.pinnedVisible.add(id);
    const o = this.nodeMap.get(this.origin)?.pos || { x: 0, y: 0, z: 0 };
    // Local packing radius — dense Korean PF hubs sit ~190–400 apart after relaxation.
    let nearest = Infinity;
    for (const other of this.nodes) {
      if (other.n.id === id) continue;
      const d = len(sub(other.pos, r.pos));
      if (d > 0 && d < nearest) nearest = d;
    }
    const localR = Number.isFinite(nearest) ? Math.max(240, Math.min(900, nearest * 4.2)) : 420;
    const mid = opts?.preferTarget
      ? { x: r.pos.x, y: r.pos.y, z: r.pos.z }
      : {
        x: lerp(o.x, r.pos.x, 0.55),
        y: lerp(o.y, r.pos.y, 0.55),
        z: lerp(o.z, r.pos.z, 0.55),
      };
    const half = Math.max(100, 0.5 * Math.min(this.W || 900, this.H || 600));
    const span = opts?.preferTarget
      ? Math.max(localR * 2.8, 420)
      : Math.max(len(sub(r.pos, o)), localR * 2.2, this.radius * 0.22);
    const framed = span * 1.2 * (this.focal / half) + 480;
    const dist = Math.max(this.minDist, Math.min(this.maxDist, framed));
    this.goal = { target: mid, dist, pitch: 0.22 };
    this.idleSince = this.time;
  }

  /** Distance that fits the full network radius into the canvas with vertical padding. */
  private fitDist() {
    // Use height more aggressively — top clipping was caused by under-weighting H vs W.
    const halfH = Math.max(120, this.H * 0.42);
    const halfW = Math.max(120, this.W * 0.46);
    const half = Math.min(halfW, halfH);
    const pad = 1.28; // padding so labels / topmost nodes stay inside
    const raw = this.radius * (this.focal / half) * pad + 280;
    return Math.max(this.minDist, 700, Math.min(this.maxDist, raw));
  }

  /** Fit entire visible network (origin-centered) with shallow pitch so top nodes are not clipped. */
  fitAll() {
    const visible = this.nodes.filter((r) => this.nodeVisible(r));
    const pts = (visible.length ? visible : this.nodes).map((r) => r.pos);
    if (!pts.length) {
      this.resetView();
      return;
    }
    const c = mul(pts.reduce((acc, p) => add(acc, p), { x: 0, y: 0, z: 0 }), 1 / pts.length);
    const rad = Math.max(this.radius * 0.85, ...pts.map((p) => len(sub(p, c))));
    const half = Math.max(120, Math.min(this.W * 0.46, this.H * 0.42));
    const dist = Math.max(this.minDist, 700, Math.min(this.maxDist, rad * (this.focal / half) * 1.32 + 320));
    this.goal = { target: c, dist, pitch: 0.18, yaw: this.yaw, slow: false };
    this.idleSince = this.time;
  }

  resetView() {
    // Shallow pitch keeps northern nodes on-screen; previous 0.3 clipped the top of large graphs.
    this.goal = { target: { x: 0, y: 0, z: 0 }, dist: this.fitDist(), pitch: 0.18 };
  }

  pulse(id: string, color = "#FF3B4E") {
    const r = this.nodeMap.get(id);
    if (r) this.addWave(r, color);
  }

  screenPosOf(id: string): { x: number; y: number } | null {
    const r = this.nodeMap.get(id);
    if (!r || !r.proj.ok) return null;
    return { x: r.proj.sx, y: r.proj.sy };
  }

  destroy() {
    cancelAnimationFrame(this.raf);
    this.unbind();
  }

  /** Public: recover from a blank canvas without destroying selection / layout. */
  recoverView() {
    this.goal = null;
    this.yaw = 0.62;
    this.pitch = 0.22;
    this.target = { x: 0, y: 0, z: 0 };
    this.dist = Math.max(this.minDist, this.fitDist());
    this.resize();
  }

  resize = () => {
    const rect = this.canvas.getBoundingClientRect();
    // Cap DPR for large PF graphs — 2× on 4K + 300 nodes overwhelms 2D canvas fillText.
    const nodeBudget = this.nodes.length > 200 ? 1.5 : 2;
    this.dpr = Math.min(window.devicePixelRatio || 1, nodeBudget);
    const prevW = this.W, prevH = this.H;
    this.W = Math.max(1, rect.width);
    this.H = Math.max(1, rect.height);
    const bw = Math.round(this.W * this.dpr);
    const bh = Math.round(this.H * this.dpr);
    // Avoid pointless buffer realloc that can blank the canvas mid-frame.
    if (this.canvas.width !== bw || this.canvas.height !== bh) {
      this.canvas.width = bw;
      this.canvas.height = bh;
    }
    this.focal = Math.min(this.W, this.H * 1.25) * 0.95;
    // Recalculate fit when canvas size changes meaningfully (sidebar / window resize).
    if (this.nodes.length && (Math.abs(prevW - this.W) > 8 || Math.abs(prevH - this.H) > 8)) {
      this.maxDist = Math.max(12000, this.radius * 8 + 2400);
      this.minDist = Math.max(this.minDist, Math.max(520, this.radius * 0.32));
      if (!this.goal) this.dist = Math.min(this.maxDist, Math.max(this.dist, this.fitDist() * 0.92));
    }
  };

  // ================= layout =================
  private computeLayout(nodes: NetNode[], edges: NetEdge[], origin: string): Map<string, V3> {
    const adj = new Map<string, string[]>();
    for (const e of edges) {
      if (!adj.has(e.source)) adj.set(e.source, []);
      if (!adj.has(e.target)) adj.set(e.target, []);
      adj.get(e.source)!.push(e.target);
      adj.get(e.target)!.push(e.source);
    }
    const depth = new Map<string, number>([[origin, 0]]);
    const parent = new Map<string, string>();
    const q = [origin];
    while (q.length) {
      const c = q.shift()!;
      for (const nb of adj.get(c) || []) {
        if (!depth.has(nb)) { depth.set(nb, depth.get(c)! + 1); parent.set(nb, c); q.push(nb); }
      }
    }
    const pos = new Map<string, V3>();
    pos.set(origin, { x: 0, y: 0, z: 0 });
    const byNode = new Map(nodes.map((n) => [n.id, n]));
    const maxD = Math.max(0, ...[...depth.values()]);
    const golden = Math.PI * (3 - Math.sqrt(5));
    let orphanIdx = 0;
    for (let d = 1; d <= maxD + 1; d++) {
      const level = nodes.filter((n) => (depth.get(n.id) ?? maxD + 1) === d && n.id !== origin);
      const buckets = new Map<string, NetNode[]>();
      for (const n of level) {
        const key = d === 1 ? n.group : `${n.group}|${parent.get(n.id) || "none"}`;
        if (!buckets.has(key)) buckets.set(key, []);
        buckets.get(key)!.push(n);
      }
      for (const [key, list] of buckets) {
        const group = key.split("|")[0];
        let base: V3;
        let dir: V3;
        const par = d > 1 ? parent.get(list[0].id) : undefined;
        if (d === 1 || !par || !pos.has(par)) {
          dir = norm(GROUP_DIRS[group] || {
            x: Math.cos(orphanIdx * golden), y: ((orphanIdx * 0.37) % 1) - 0.5, z: Math.sin(orphanIdx * golden),
          });
          orphanIdx++;
          base = mul(dir, d === 1 ? 340 : 340 + (d - 1) * 230);
        } else {
          const pp = pos.get(par)!;
          const gdir = GROUP_DIRS[byNode.get(par)!.group] || GROUP_DIRS[group] || { x: 1, y: 0, z: 0 };
          dir = norm(add(norm(pp.x || pp.y || pp.z ? pp : gdir), mul(norm(GROUP_DIRS[group] || gdir), 0.35)));
          base = add(pp, mul(dir, 300));
        }
        const helper = Math.abs(dir.y) > 0.9 ? { x: 1, y: 0, z: 0 } : { x: 0, y: 1, z: 0 };
        const u = norm(cross(dir, helper));
        const v = norm(cross(dir, u));
        const n = list.length;
        // Wider rings for large Korean institution clusters so labels remain separable
        const radius = n > 1 ? 90 + n * (n > 12 ? 42 : 30) : 0;
        list.forEach((node, i) => {
          const a = (i / Math.max(1, n)) * Math.PI * 2 + d * 0.9;
          pos.set(node.id, add(base, add(mul(u, Math.cos(a) * radius), mul(v, Math.sin(a) * radius))));
        });
      }
    }
    // relaxation: keep stars apart without losing the constellation shape
    // Cap iterations for large PF graphs (300+ nodes) so layout never freezes the UI into a black flash.
    const ids = [...pos.keys()];
    const iters = ids.length > 220 ? 28 : ids.length > 120 ? 48 : 80;
    for (let it = 0; it < iters; it++) {
      for (let i = 0; i < ids.length; i++) {
        for (let j = i + 1; j < ids.length; j++) {
          const a = pos.get(ids[i])!, b = pos.get(ids[j])!;
          const dv = sub(b, a);
          const dd = len(dv);
          const min = 190;
          if (dd < min) {
            const push = mul(norm(dv), (min - dd) / 2);
            if (ids[i] !== origin) pos.set(ids[i], sub(a, push));
            if (ids[j] !== origin) pos.set(ids[j], add(b, push));
          }
        }
      }
    }
    // Ensure every input node has a position (disconnected stubs, etc.)
    let orphan = 0;
    for (const n of nodes) {
      if (pos.has(n.id)) continue;
      const a = orphan++ * Math.PI * (3 - Math.sqrt(5));
      pos.set(n.id, { x: Math.cos(a) * 480, y: ((orphan * 0.19) % 1) - 0.5, z: Math.sin(a) * 480 });
    }
    return pos;
  }

  private makeStars() {
    const r = seeded(42);
    for (let i = 0; i < 1500; i++) {
      const u = r() * 2 - 1, t = r() * Math.PI * 2;
      const s = Math.sqrt(1 - u * u);
      this.stars.push({ d: { x: s * Math.cos(t), y: u, z: s * Math.sin(t) }, m: Math.pow(r(), 3), tw: r() * 10 });
    }
    for (let i = 0; i < 240; i++) {
      const p = { x: (r() - 0.5) * 1900, y: (r() - 0.5) * 1300, z: (r() - 0.5) * 1900 };
      this.dust.push({ p, v: { x: (r() - 0.5) * 4, y: (r() - 0.5) * 3, z: (r() - 0.5) * 4 }, m: r() });
    }
  }

  // ================= camera / projection =================
  private sanitizeCamera() {
    if (!Number.isFinite(this.yaw)) this.yaw = 0.62;
    if (!Number.isFinite(this.pitch)) this.pitch = 0.22;
    // Keep pitch away from ±90° gimbal lock (black / empty projection).
    this.pitch = Math.max(-0.92, Math.min(0.92, this.pitch));
    if (!Number.isFinite(this.dist) || this.dist < this.minDist) {
      this.dist = Math.max(this.minDist, this.fitDist() * 0.85);
    }
    this.dist = Math.min(this.maxDist, this.dist);
    if (!Number.isFinite(this.target.x) || !Number.isFinite(this.target.y) || !Number.isFinite(this.target.z)) {
      this.target = { x: 0, y: 0, z: 0 };
      this.goal = null;
    }
  }

  private updateCamera() {
    this.sanitizeCamera();
    const cp = Math.cos(this.pitch);
    const off = {
      x: this.dist * cp * Math.sin(this.yaw),
      y: this.dist * Math.sin(this.pitch),
      z: this.dist * cp * Math.cos(this.yaw),
    };
    this.camPos = add(this.target, off);
    this.fwd = norm(sub(this.target, this.camPos));
    // Stable basis even when looking nearly straight up/down.
    let right = cross(this.fwd, { x: 0, y: 1, z: 0 });
    if (len(right) < 1e-4) right = cross(this.fwd, { x: 1, y: 0, z: 0 });
    this.right = norm(right);
    this.up = norm(cross(this.right, this.fwd));
    if (!Number.isFinite(this.fwd.x) || !Number.isFinite(this.right.x) || !Number.isFinite(this.up.x)) {
      this.yaw = 0.62;
      this.pitch = 0.22;
      this.dist = Math.max(this.minDist, this.fitDist());
      this.target = { x: 0, y: 0, z: 0 };
      this.goal = null;
      const off2 = {
        x: this.dist * Math.cos(this.pitch) * Math.sin(this.yaw),
        y: this.dist * Math.sin(this.pitch),
        z: this.dist * Math.cos(this.pitch) * Math.cos(this.yaw),
      };
      this.camPos = add(this.target, off2);
      this.fwd = norm(sub(this.target, this.camPos));
      this.right = norm(cross(this.fwd, { x: 0, y: 1, z: 0 }));
      this.up = norm(cross(this.right, this.fwd));
    }
  }

  private project(p: V3): Proj {
    if (!p || !Number.isFinite(p.x) || !Number.isFinite(p.y) || !Number.isFinite(p.z)) {
      return { sx: 0, sy: 0, z: 0, s: 0, ok: false };
    }
    const d = sub(p, this.camPos);
    const z = dot(d, this.fwd);
    // Soft near-plane — was 20 and buried the camera inside dense PF hubs (everything clipped = black).
    if (z < 8 || !Number.isFinite(z)) return { sx: 0, sy: 0, z, s: 0, ok: false };
    const s = this.focal / z;
    if (!Number.isFinite(s) || s <= 0) return { sx: 0, sy: 0, z, s: 0, ok: false };
    const sx = this.W / 2 + dot(d, this.right) * s;
    const sy = this.H / 2 - dot(d, this.up) * s;
    if (!Number.isFinite(sx) || !Number.isFinite(sy)) return { sx: 0, sy: 0, z, s: 0, ok: false };
    return { sx, sy, z, s, ok: true };
  }

  // ================= events =================
  private bind() {
    const c = this.canvas;
    c.addEventListener("pointerdown", this.onDown);
    window.addEventListener("pointermove", this.onMove);
    window.addEventListener("pointerup", this.onUp);
    window.addEventListener("pointercancel", this.onUp);
    c.addEventListener("wheel", this.onWheel, { passive: false });
    c.addEventListener("pointerleave", this.onLeave);
    window.addEventListener("resize", this.resize);
    window.addEventListener("contagion:lp-resize", this.resize as EventListener);
  }
  private unbind() {
    const c = this.canvas;
    c.removeEventListener("pointerdown", this.onDown);
    window.removeEventListener("pointermove", this.onMove);
    window.removeEventListener("pointerup", this.onUp);
    window.removeEventListener("pointercancel", this.onUp);
    c.removeEventListener("wheel", this.onWheel);
    c.removeEventListener("pointerleave", this.onLeave);
    window.removeEventListener("resize", this.resize);
    window.removeEventListener("contagion:lp-resize", this.resize as EventListener);
  }
  private local(ev: PointerEvent | WheelEvent) {
    const r = this.canvas.getBoundingClientRect();
    return { x: ev.clientX - r.left, y: ev.clientY - r.top };
  }
  private onDown = (ev: PointerEvent) => {
    const p = this.local(ev);
    this.pointers.set(ev.pointerId, p);
    this.dragMoved = false;
    this.downAt = p;
    this.goal = null;
    this.idleSince = this.time;
    if (this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      this.pinchStart = Math.hypot(a.x - b.x, a.y - b.y) / this.dist;
    }
    try { this.canvas.setPointerCapture(ev.pointerId); } catch { /* ignore */ }
  };
  private onMove = (ev: PointerEvent) => {
    const p = this.local(ev);
    const prev = this.pointers.get(ev.pointerId);
    if (prev) {
      if (this.pointers.size === 2) {
        this.pointers.set(ev.pointerId, p);
        const [a, b] = [...this.pointers.values()];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (this.pinchStart > 0) this.dist = Math.max(this.minDist, Math.min(this.maxDist, d / this.pinchStart));
        this.dragMoved = true;
        return;
      }
      const dx = p.x - prev.x, dy = p.y - prev.y;
      if (Math.hypot(p.x - this.downAt.x, p.y - this.downAt.y) > 4) this.dragMoved = true;
      this.yaw -= dx * 0.0055;
      this.pitch = Math.max(-0.92, Math.min(0.92, this.pitch + dy * 0.0045));
      this.pointers.set(ev.pointerId, p);
      this.idleSince = this.time;
      return;
    }
    if (ev.target !== this.canvas) return;
    this.pick(p.x, p.y, false);
  };
  private onUp = (ev: PointerEvent) => {
    if (!this.pointers.has(ev.pointerId)) return;
    const p = this.local(ev);
    this.pointers.delete(ev.pointerId);
    if (!this.dragMoved && this.pointers.size === 0) this.pick(p.x, p.y, true);
  };
  private onLeave = () => {
    if (this.pointers.size) return;
    if (this.hoverNode) { this.hoverNode = null; this.cb.onHoverNode?.(null, 0, 0); }
    if (this.hoverEdge) { this.hoverEdge = null; this.cb.onHoverEdge?.(null, 0, 0); }
    this.canvas.style.cursor = "grab";
  };
  private onWheel = (ev: WheelEvent) => {
    ev.preventDefault();
    this.goal = null;
    this.dist = Math.max(this.minDist, Math.min(this.maxDist, this.dist * Math.exp(ev.deltaY * 0.0011)));
    this.idleSince = this.time;
  };

  private edgeVisible(er: EdgeRT) {
    if (this.hiddenCats.has(EDGE_CATEGORY(er.e))) return false;
    return this.nodeVisible(er.a) && this.nodeVisible(er.b);
  }
  private nodeVisible(r: NodeRT) {
    if (r.n.id === this.origin || this.pinnedVisible.has(r.n.id) || this.selectedNode === r.n.id) return true;
    return !this.hiddenGroups.has(r.n.group);
  }

  private pick(x: number, y: number, click: boolean) {
    let best: NodeRT | null = null;
    let bestZ = Infinity;
    for (const r of this.nodes) {
      if (!r.proj.ok || !this.nodeVisible(r)) continue;
      const rad = Math.max(12, r.n.display_size * 3.4 * r.proj.s * r.scale * 1.25);
      if (Math.hypot(r.proj.sx - x, r.proj.sy - y) <= rad && r.proj.z < bestZ) { best = r; bestZ = r.proj.z; }
    }
    let edge: EdgeRT | null = null;
    if (!best) {
      let bd = 7;
      for (const er of this.edges) {
        if (!er.pts || !this.edgeVisible(er)) continue;
        const d = distToQuad(x, y, er.pts);
        if (d < bd) { bd = d; edge = er; }
      }
    }
    if (click) {
      if (best) this.cb.onSelectNode?.(best.n.id);
      else if (edge) this.cb.onSelectEdge?.(edge.e.id);
      else this.cb.onSelectNone?.();
      return;
    }
    const nid = best ? best.n.id : null;
    const eid = edge ? edge.e.id : null;
    const nodeChanged = nid !== this.hoverNode;
    const edgeChanged = eid !== this.hoverEdge;
    if (nodeChanged) this.hoverNode = nid;
    if (edgeChanged) this.hoverEdge = eid;
    // Fire React only when the hovered entity changes — not on every pointer pixel.
    if (nodeChanged) this.cb.onHoverNode?.(nid, x, y);
    if (edgeChanged || nodeChanged) this.cb.onHoverEdge?.(nid ? null : eid, x, y);
    this.canvas.style.cursor = nid || eid ? "pointer" : "grab";
  }

  private addWave(r: NodeRT, color: string) {
    this.waves.push({ node: r, t0: this.time, color: hexToRgb(color), dur: 2.2 });
  }

  // ================= frame =================
  private frame = (now: number) => {
    const dt = Math.min(0.05, (now - this.last) / 1000);
    this.last = now;
    this.time += dt;
    try {
      this.step(dt);
      this.draw();
    } catch (err) {
      // Never kill the RAF loop — a thrown draw() left the canvas cleared (= black screen).
      console.warn("[Universe] frame error (recovered)", err);
      try {
        const { ctx } = this;
        ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
        ctx.globalCompositeOperation = "source-over";
        ctx.fillStyle = "#060A17";
        ctx.fillRect(0, 0, this.W, this.H);
        ctx.fillStyle = "rgba(226,234,250,0.85)";
        ctx.font = "600 13px Pretendard, Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("맵 렌더 복구 중…", this.W / 2, this.H / 2);
      } catch { /* ignore nested */ }
    }
    this.raf = requestAnimationFrame(this.frame);
  };

  private step(dt: number) {
    // staged reveals whose light has arrived
    if (this.pending.length) {
      const due = this.pending.filter((p) => this.time >= p.at);
      if (due.length) {
        this.pending = this.pending.filter((p) => this.time < p.at);
        for (const p of due) this.applyVisual(p.node, p.visual, true);
      }
    }
    if (this.goal) {
      const k = 1 - Math.pow(this.goal.slow ? 0.12 : 0.0025, dt);
      if (this.goal.target) {
        this.target = { x: lerp(this.target.x, this.goal.target.x, k), y: lerp(this.target.y, this.goal.target.y, k), z: lerp(this.target.z, this.goal.target.z, k) };
      }
      if (this.goal.dist !== undefined) this.dist = lerp(this.dist, this.goal.dist, k);
      if (this.goal.pitch !== undefined) this.pitch = lerp(this.pitch, this.goal.pitch, k);
      this.dist = Math.max(this.minDist, Math.min(this.maxDist, this.dist));
      this.pitch = Math.max(-0.92, Math.min(0.92, this.pitch));
      const doneT = !this.goal.target || len(sub(this.target, this.goal.target)) < 1;
      const doneD = this.goal.dist === undefined || Math.abs(this.dist - this.goal.dist) < 1;
      if (doneT && doneD) this.goal = null;
    }
    if (this.autoRotate && !this.reduceMotion && !this.pointers.size && this.time - this.idleSince > 3.5) {
      this.yaw += dt * 0.045;
    }
    // hover / dimming targets
    const focusId = this.hoverNode || this.selectedNode;
    const neighbors = new Set<string>();
    if (focusId) {
      neighbors.add(focusId);
      for (const er of this.edges) {
        if (!this.edgeVisible(er)) continue;
        if (er.e.source === focusId) neighbors.add(er.e.target);
        if (er.e.target === focusId) neighbors.add(er.e.source);
      }
    }
    const usePath = this.pathNodes.size > 0;
    const k = 1 - Math.pow(0.0008, dt);
    for (const r of this.nodes) {
      const isHover = r.n.id === this.hoverNode;
      const sel = r.n.id === this.selectedNode;
      r.scale = lerp(r.scale, isHover ? 1.45 : sel ? 1.25 : 1, k);
      let dim = 1;
      if (this.hoverNode) dim = neighbors.has(r.n.id) ? 1 : 0.16;
      else if (usePath) dim = this.pathNodes.has(r.n.id) ? 1 : 0.28;
      else if (this.selectedNode) dim = neighbors.has(r.n.id) ? 1 : 0.35;
      else if (this.focusSet.size) dim = this.focusSet.has(r.n.id) ? 1 : 0.3;
      if (!this.nodeVisible(r)) dim = 0;
      r.dim = lerp(r.dim, dim, k);
      for (let i = 0; i < 3; i++) r.color[i] = lerp(r.color[i], r.target[i], 1 - Math.pow(0.02, dt));
    }
    for (const er of this.edges) {
      let dim = 1;
      const touchesFocus = focusId && (er.e.source === focusId || er.e.target === focusId);
      if (this.hoverNode) dim = touchesFocus ? 1 : 0.07;
      else if (usePath) dim = this.pathEdges.has(er.e.id) ? 1 : 0.12;
      else if (this.selectedNode) dim = touchesFocus ? 1 : 0.25;
      else if (this.focusSet.size) dim = this.activeEdges.has(er.e.id) || (this.focusSet.has(er.e.source) && this.focusSet.has(er.e.target)) ? 1 : 0.35;
      if (er.e.id === this.hoverEdge || er.e.id === this.selectedEdge) dim = 1.4;
      if (!this.edgeVisible(er)) dim = 0;
      er.dim = lerp(er.dim, dim, k);
    }
    for (const d of this.dust) {
      d.p = add(d.p, mul(d.v, dt * this.speed));
    }
    this.waves = this.waves.filter((w) => this.time - w.t0 < w.dur);
  }

  private draw() {
    const { ctx, W, H } = this;
    if (W < 2 || H < 2) return;
    // During orbit/pinch, drop DPR & heavy FX so large PF graphs stay interactive (avoids black freeze).
    const interacting = this.pointers.size > 0;
    const dprDraw = interacting ? Math.min(this.dpr, 1.25) : this.dpr;
    ctx.setTransform(dprDraw, 0, 0, dprDraw, 0, 0);
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";
    ctx.setLineDash([]);
    const rad = Math.max(W, H) * 0.8;
    const bg = ctx.createRadialGradient(W * 0.5, H * 0.45, 0, W * 0.5, H * 0.5, Math.max(8, rad));
    bg.addColorStop(0, "#0B1226");
    bg.addColorStop(0.55, "#060A17");
    bg.addColorStop(1, "#03050C");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);
    this.updateCamera();

    ctx.globalCompositeOperation = "lighter";
    if (!interacting) {
      this.drawNebula();
      this.drawStars();
    } else {
      // Lightweight star field while dragging
      this.drawStars();
    }

    // project nodes
    let visible = 0;
    for (const r of this.nodes) {
      r.proj = this.project(r.pos);
      if (r.proj.ok) visible += 1;
    }
    // If the camera is buried inside a dense hub, almost nothing projects → pull out immediately.
    // Skip while an intentional fly-to is in progress (avoids yanking mid-focus).
    if (
      !this.goal
      && !this.pointers.size
      && this.nodes.length > 30
      && visible < Math.max(4, this.nodes.length * 0.02)
    ) {
      this.goal = { target: { x: 0, y: 0, z: 0 }, dist: this.fitDist(), pitch: 0.2, slow: false };
    }

    this.drawEdges();
    if (!interacting) this.drawWaves();
    this.drawNodes();
    if (!interacting) this.drawEdgeLabels();
    ctx.globalCompositeOperation = "source-over";
  }

  private drawNebula() {
    const { ctx, W, H } = this;
    const blobs: [number, number, number, string, number][] = [
      [0.22, 0.3, 0.55, "#2A3F9E", 0.10],
      [0.8, 0.72, 0.5, "#5B2A8C", 0.09],
      [0.62, 0.18, 0.35, "#0F6E8C", 0.07],
    ];
    for (const [fx, fy, fr, col, a] of blobs) {
      const px = W * fx + Math.sin(this.yaw) * 40;
      const py = H * fy + Math.sin(this.pitch) * 30;
      const g = ctx.createRadialGradient(px, py, 0, px, py, Math.max(W, H) * fr);
      const c = hexToRgb(col);
      g.addColorStop(0, rgba(c, a));
      g.addColorStop(1, rgba(c, 0));
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
    }
  }

  private drawStars() {
    const { ctx } = this;
    for (const s of this.stars) {
      const z = dot(s.d, mul(this.fwd, -1)) * -1;
      if (z <= 0.05) continue;
      const sx = this.W / 2 + (dot(s.d, this.right) / z) * this.focal * 0.9;
      const sy = this.H / 2 - (dot(s.d, this.up) / z) * this.focal * 0.9;
      if (sx < -2 || sy < -2 || sx > this.W + 2 || sy > this.H + 2) continue;
      const tw = this.reduceMotion ? 1 : 0.65 + 0.35 * Math.sin(this.time * 1.3 + s.tw);
      const a = (0.15 + s.m * 0.75) * tw;
      const size = 0.5 + s.m * 1.4;
      ctx.fillStyle = `rgba(200,215,255,${a.toFixed(3)})`;
      ctx.fillRect(sx, sy, size, size);
    }
    for (const d of this.dust) {
      const p = this.project(d.p);
      if (!p.ok) continue;
      const a = 0.05 + d.m * 0.12;
      ctx.fillStyle = `rgba(150,180,255,${a.toFixed(3)})`;
      const sz = Math.max(0.6, p.s * 2.2);
      ctx.fillRect(p.sx, p.sy, sz, sz);
    }
  }

  private drawEdges() {
    const { ctx } = this;
    const flowSpeed = 0.12 * this.speed;
    for (const er of this.edges) {
      const pa = er.a.proj, pb = er.b.proj;
      if (!pa.ok || !pb.ok || er.dim < 0.01) { er.pts = undefined; continue; }
      const mx = (pa.sx + pb.sx) / 2, my = (pa.sy + pb.sy) / 2;
      const dx = pb.sx - pa.sx, dy = pb.sy - pa.sy;
      const L = Math.hypot(dx, dy) || 1;
      const nx = -dy / L, ny = dx / L;
      const bendPx = er.bend * L;
      // trim ends so lines meet the glow edge, not the center
      const ra = er.a.n.display_size * 3.4 * pa.s * er.a.scale;
      const rb = er.b.n.display_size * 3.4 * pb.s * er.b.scale;
      const cx = mx + nx * bendPx, cy = my + ny * bendPx;
      const x0 = pa.sx + (dx / L) * ra, y0 = pa.sy + (dy / L) * ra;
      const x1 = pb.sx - (dx / L) * rb, y1 = pb.sy - (dy / L) * rb;
      const s = (pa.s + pb.s) / 2;
      if (![x0, y0, cx, cy, x1, y1, s].every(Number.isFinite)) { er.pts = undefined; continue; }
      er.pts = { x0, y0, cx, cy, x1, y1, s };

      const startAt = this.edgeStart.get(er.e.id) ?? this.time - 10;
      const prog = this.activeEdges.has(er.e.id) ? Math.max(0, Math.min(1, (this.time - startAt) / (this.travel / this.speed))) : 0;
      const active = this.activeEdges.has(er.e.id) && prog > 0;
      const travelling = active && prog < 1;
      const inPath = this.pathEdges.has(er.e.id);
      const reference = !!this.usedEdges && !this.usedEdges.has(er.e.id);
      const baseCol = hexToRgb(EDGE_COLORS[er.e.relationship_type] || "#8899BB");
      const contract = er.e.impact_channel === "contract";
      let col = baseCol;
      if (active) col = er.e.impact_channel === "financial" || er.e.impact_channel === "equity" ? hexToRgb("#F2C14E") : hexToRgb("#FF8A3D");
      const historical = (er.e as { layer?: string }).layer === "historical"
        || ["repaid", "historical", "terminated", "HISTORICAL_ONLY", "FULLY_REPAID"].includes(
          (er.e as { exposure_status?: string; relationship_status?: string }).exposure_status
          || (er.e as { relationship_status?: string }).relationship_status
          || "",
        );
      const alpha = Math.min(1, (active ? 0.85 : inPath ? 0.75 : reference ? 0.1 : historical ? 0.12 : contract ? 0.16 : 0.32) * er.dim);
      const width = Math.max(0.6, (active ? 2.1 : inPath ? 1.7 : reference ? 0.7 : historical ? 0.75 : 1) * Math.min(1.6, s * 1.2));
      const dashed = historical || er.e.source_status !== "VERIFIED";
      ctx.setLineDash(reference ? [2, 6] : historical ? [4, 7] : contract ? [1.5, 5] : dashed ? [6, 5] : []);
      ctx.lineDashOffset = dashed ? -this.time * 14 * this.speed : 0;
      if (travelling) {
        // the not-yet-reached part stays a faint guide; the reached part is drawn bright up to the light head
        ctx.strokeStyle = rgba(baseCol, 0.16 * er.dim);
        ctx.lineWidth = Math.max(0.6, width * 0.6);
        ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo(cx, cy, x1, y1); ctx.stroke();
        ctx.setLineDash([]);
        for (const [w, a2] of [[width, alpha], [width * 4, alpha * 0.25]] as [number, number][]) {
          ctx.strokeStyle = rgba(col, a2);
          ctx.lineWidth = w;
          ctx.beginPath();
          const N = 28;
          for (let i = 0; i <= N; i++) {
            const pt = quadAt(er.pts, (i / N) * prog);
            if (i === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
          }
          ctx.stroke();
        }
      } else {
        ctx.strokeStyle = rgba(col, alpha);
        ctx.lineWidth = width;
        ctx.beginPath();
        ctx.moveTo(x0, y0);
        ctx.quadraticCurveTo(cx, cy, x1, y1);
        ctx.stroke();
        if (active || inPath) {
          ctx.setLineDash([]);
          ctx.strokeStyle = rgba(col, alpha * 0.25);
          ctx.lineWidth = width * 4;
          ctx.beginPath();
          ctx.moveTo(x0, y0);
          ctx.quadraticCurveTo(cx, cy, x1, y1);
          ctx.stroke();
        }
      }
      ctx.setLineDash([]);

      // arrowhead (shock direction)
      if (er.dim > 0.2 && !contract && !reference && !travelling) {
        const t = 0.84;
        const p = quadAt(er.pts, t), q = quadAt(er.pts, t - 0.04);
        const ang = Math.atan2(p.y - q.y, p.x - q.x);
        const sz = Math.max(3, 6 * Math.min(1.4, s * 1.2));
        ctx.fillStyle = rgba(col, alpha * 1.1);
        ctx.beginPath();
        ctx.moveTo(p.x + Math.cos(ang) * sz, p.y + Math.sin(ang) * sz);
        ctx.lineTo(p.x + Math.cos(ang + 2.5) * sz, p.y + Math.sin(ang + 2.5) * sz);
        ctx.lineTo(p.x + Math.cos(ang - 2.5) * sz, p.y + Math.sin(ang - 2.5) * sz);
        ctx.closePath();
        ctx.fill();
      }

      // particles: faint idle flow, bright comets on active edges
      if (this.reduceMotion) continue;
      if (travelling) {
        // one bright head with a long tail: the moment the shock moves along this relationship
        for (let tr = 0; tr < 14; tr++) {
          const tt = prog - tr * 0.022;
          if (tt < 0) break;
          const p = quadAt(er.pts, tt);
          const r0 = Math.max(1.6, (5.2 - tr * 0.33) * Math.min(1.5, s * 1.3));
          const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r0 * 3.2);
          g.addColorStop(0, rgba([255, 255, 255], (1 - tr * 0.07) * er.dim));
          g.addColorStop(0.35, rgba(col, (0.9 - tr * 0.06) * er.dim));
          g.addColorStop(1, rgba(col, 0));
          ctx.fillStyle = g;
          ctx.beginPath();
          ctx.arc(p.x, p.y, r0 * 3.2, 0, Math.PI * 2);
          ctx.fill();
        }
      } else if (active) {
        const age = this.time - startAt;
        const n = 3;
        for (let i = 0; i < n; i++) {
          const t = ((age * 0.26 * this.speed) + i / n) % 1;
          for (let tr = 0; tr < 6; tr++) {
            const tt = t - tr * 0.018;
            if (tt < 0) continue;
            const p = quadAt(er.pts, tt);
            const r0 = Math.max(1.2, (3.2 - tr * 0.45) * Math.min(1.5, s * 1.3));
            const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r0 * 3);
            g.addColorStop(0, rgba([255, 255, 255], (0.9 - tr * 0.14) * er.dim));
            g.addColorStop(0.35, rgba(col, (0.8 - tr * 0.12) * er.dim));
            g.addColorStop(1, rgba(col, 0));
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.arc(p.x, p.y, r0 * 3, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      } else if (!contract && !reference && er.dim > 0.3) {
        const t = (this.time * flowSpeed + er.seed) % 1;
        const p = quadAt(er.pts, t);
        ctx.fillStyle = rgba(baseCol, 0.55 * er.dim);
        ctx.beginPath();
        ctx.arc(p.x, p.y, Math.max(0.8, 1.5 * s), 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  /** Edge labels only on path / hover / selection — never flood all active shock edges. */
  private drawEdgeLabels() {
    const { ctx } = this;
    ctx.globalCompositeOperation = "source-over";
    for (const er of this.edges) {
      if (!er.pts || er.dim < 0.3) continue;
      const show = this.pathEdges.has(er.e.id) || er.e.id === this.hoverEdge || er.e.id === this.selectedEdge;
      if (!show) continue;
      const text = er.e.impact_label || er.e.label;
      if (!text) continue;
      const p = quadAt(er.pts, 0.5);
      const fs = Math.max(10, Math.min(12.5, 10.5 * Math.sqrt(er.pts.s * 1.6)));
      ctx.font = `600 ${fs}px Pretendard, Inter, "Noto Sans KR", "Malgun Gothic", system-ui, sans-serif`;
      const w = ctx.measureText(text).width;
      const active = this.activeEdges.has(er.e.id);
      const col = active ? (er.e.impact_channel === "financial" ? "242,193,78" : "255,176,120") : "200,214,240";
      ctx.fillStyle = "rgba(5,8,18,0.86)";
      roundRect(ctx, p.x - w / 2 - 7, p.y - fs / 2 - 4, w + 14, fs + 8, 9);
      ctx.fill();
      ctx.strokeStyle = `rgba(${col},0.6)`;
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = `rgba(${col},1)`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text, p.x, p.y + 0.5);
    }
    ctx.globalCompositeOperation = "lighter";
  }

  private drawWaves() {
    const { ctx } = this;
    for (const w of this.waves) {
      const p = w.node.proj;
      if (!p.ok) continue;
      const age = (this.time - w.t0) / w.dur;
      for (let ring = 0; ring < 3; ring++) {
        const a = age - ring * 0.12;
        if (a <= 0 || a >= 1) continue;
        const R = (40 + a * 520) * p.s;
        ctx.strokeStyle = rgba(w.color, (1 - a) * 0.55);
        ctx.lineWidth = Math.max(1, 3 * (1 - a));
        ctx.beginPath();
        ctx.ellipse(p.sx, p.sy, R, R * 0.92, 0, 0, Math.PI * 2);
        ctx.stroke();
        const g = ctx.createRadialGradient(p.sx, p.sy, R * 0.7, p.sx, p.sy, R);
        g.addColorStop(0, rgba(w.color, 0));
        g.addColorStop(1, rgba(w.color, (1 - a) * 0.12));
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, R, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  private drawNodes() {
    const { ctx } = this;
    const order = this.nodes.filter((r) => r.proj.ok && r.dim > 0.02).sort((a, b) => b.proj.z - a.proj.z);
    for (const r of order) {
      const p = r.proj;
      const st = r.visual.status;
      const rank = STRESS_RANK[st] || 0;
      const visInt = r.visual.intensity;
      const R = r.n.display_size * 3.4 * p.s * r.scale * (rank >= 4 ? 1.06 : 1);
      const alertState = rank >= 3;
      const shake = !this.reduceMotion && rank >= 3
        ? (rank >= 4 ? 1.8 : 0.9) * Math.sin(this.time * (rank >= 4 ? 18 : 10) + r.pos.x)
        : 0;
      const sx = p.sx + shake;
      const sy = p.sy + shake * 0.6;
      const pulse = this.reduceMotion ? 1 : alertState ? 0.78 + 0.22 * Math.sin(this.time * 5.5) : 0.9 + 0.1 * Math.sin(this.time * 1.4 + r.pos.x);
      const graded = st === "assumed";
      // Prefer continuous financial intensity so +100bp and +300bp differ inside the same band.
      const intensity = typeof visInt === "number" && visInt > 0
        ? visInt
        : st === "normal" ? 0.75 : st === "potential" || st === "insufficient" ? 0.45 : st === "contract_party" ? 0.95
          : st === "mk_na" ? 0.3 : MARKET(st) ? 1.05 : rank >= 1 ? 0.7 + rank * 0.22 : 1.25;
      const glowR = R * (3.2 + (alertState ? 0.8 + rank * 0.35 : 0)) * pulse;
      const a = r.dim;
      // outer glow (additive)
      const g = ctx.createRadialGradient(sx, sy, 0, sx, sy, glowR);
      g.addColorStop(0, rgba(r.color, 0.55 * a * intensity));
      g.addColorStop(0.25, rgba(r.color, 0.22 * a * intensity));
      g.addColorStop(1, rgba(r.color, 0));
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(sx, sy, glowR, 0, Math.PI * 2);
      ctx.fill();
      // diffraction spikes on the big ones
      if (r.n.display_size >= 8 || r.n.id === this.hoverNode) {
        ctx.strokeStyle = rgba(r.color, 0.25 * a);
        ctx.lineWidth = 1;
        const L = R * 3.4;
        ctx.beginPath();
        ctx.moveTo(sx - L, sy); ctx.lineTo(sx + L, sy);
        ctx.moveTo(sx, sy - L); ctx.lineTo(sx, sy + L);
        ctx.stroke();
      }
      // core
      ctx.globalCompositeOperation = "source-over";
      const core = ctx.createRadialGradient(sx - R * 0.25, sy - R * 0.3, 0, sx, sy, R);
      core.addColorStop(0, rgba([255, 255, 255], 0.95 * a));
      core.addColorStop(0.45, rgba(r.color, 0.95 * a));
      core.addColorStop(1, rgba(r.color.map((c) => c * 0.35) as [number, number, number], 0.95 * a));
      ctx.fillStyle = core;
      ctx.beginPath();
      ctx.arc(sx, sy, R, 0, Math.PI * 2);
      ctx.fill();

      // Surface cracks / fragments driven by stress rank (financially gated statuses).
      if (rank >= 2 && !MARKET(st)) {
        this.drawPlanetDamage(r, sx, sy, R, rank, a);
      }

      // status rings
      if (st === "contract_party" || graded || st === "potential" || st === "insufficient" || st === "shock_origin" || rank >= 1) {
        const ringCol = st === "potential" || st === "insufficient" ? hexToRgb("#9AA8C6") : r.color;
        ctx.strokeStyle = rgba(ringCol, (st === "potential" || st === "insufficient" ? 0.6 : 0.9) * a);
        ctx.lineWidth = rank >= 3 ? 2.2 : rank >= 1 || st === "shock_origin" ? 2 : 1.4;
        ctx.setLineDash(st === "contract_party" || st === "potential" || st === "insufficient" ? [3, 3] : []);
        ctx.beginPath();
        ctx.arc(sx, sy, R * 1.55, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
      }
      if (r.n.is_demo) {
        ctx.strokeStyle = rgba(hexToRgb("#FF7FC3"), 0.5 * a);
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 3]);
        ctx.beginPath();
        ctx.arc(sx, sy, R * 1.25, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
      }
      if (r.n.id === this.selectedNode) {
        ctx.strokeStyle = rgba([235, 242, 255], 0.9);
        ctx.lineWidth = 1.5;
        ctx.setLineDash([R * 0.5, R * 0.35]);
        ctx.lineDashOffset = -this.time * 20;
        ctx.beginPath();
        ctx.arc(sx, sy, R * 2.1, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
      }
      // Zoom-dependent labels: abbreviate at low zoom; full name on hover/selection.
      // While orbiting, only selected/hover labels — mass fillText on 300+ nodes freezes the canvas.
      const zoomRaw = Math.sqrt(Math.max(0.15, Number.isFinite(p.s) ? p.s : 0.15));
      const zoom = Number.isFinite(zoomRaw) ? zoomRaw : 0.4;
      const focus = r.n.id === this.hoverNode || r.n.id === this.selectedNode;
      const interacting = this.pointers.size > 0;
      const showName = interacting
        ? focus
        : focus || zoom >= 0.55 || (r.n.display_size || 0) >= 8 || (st !== "normal" && zoom >= 0.4);
      const fs = Math.max(9, Math.min(15, (focus ? 12 : 10) * zoom * 1.15)) || 11;
      if (!Number.isFinite(sx) || !Number.isFinite(sy) || !Number.isFinite(R) || R <= 0) continue;
      ctx.font = `600 ${fs}px Pretendard, Inter, "Noto Sans KR", "Malgun Gothic", "Apple SD Gothic Neo", system-ui, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      const labA = Math.min(1, a * (focus || (r.n.display_size || 0) >= 7 || st !== "normal" ? 1 : 0.72));
      ctx.fillStyle = `rgba(226,234,250,${(0.92 * labA).toFixed(3)})`;
      if (showName) {
        const ko = (r.n.name_ko || "").trim();
        const full = (ko && /[가-힣]/.test(ko)) ? ko : String(r.n.name || r.n.id || "");
        const lab = (focus || zoom >= 0.85) ? full
          : full.length > 6 ? `${full.slice(0, 4)}…` : full;
        if (lab) ctx.fillText(lab, sx, sy + R * 1.7 + 3);
      }
      // Compact stress badge only (short Korean) — never long mechanism text on canvas
      const vlabel = typeof r.visual.label === "string" ? r.visual.label : "";
      if (!interacting && vlabel && (focus || zoom >= 0.5 || (STRESS_RANK[st] || 0) >= 2)) {
        const short = vlabel.length > 8
          ? (st === "stress_critical" ? "심각" : st === "stress_high" ? "높음" : st === "stress_moderate" ? "중간" : vlabel.slice(0, 6))
          : vlabel;
        const bf = Math.max(8.5, fs - 1.5);
        ctx.font = `600 ${bf}px Pretendard, Inter, "Noto Sans KR", "Malgun Gothic", system-ui, sans-serif`;
        const lc = st === "stress_critical" ? "232,93,76" : st === "stress_high" ? "255,107,53" : st === "stress_moderate" ? "255,176,32"
          : st === "contract_party" ? "242,193,78" : st === "assumed" ? "255,196,100" : st === "potential" ? "170,182,210"
          : st === "mk_up" ? "250,130,125" : st === "mk_down" ? "120,170,250" : st === "mk_flat" || st === "mk_na" ? "160,172,195" : "255,176,120";
        const tw = ctx.measureText(short).width;
        if (!Number.isFinite(tw)) continue;
        const by = sy + R * 1.7 + 6 + (showName ? fs : 0);
        ctx.fillStyle = `rgba(6,10,22,${(0.82 * labA).toFixed(3)})`;
        roundRect(ctx, sx - tw / 2 - 6, by - 2, tw + 12, bf + 6, 4);
        ctx.fill();
        ctx.strokeStyle = `rgba(${lc},${(0.55 * labA).toFixed(3)})`;
        ctx.lineWidth = 1;
        ctx.setLineDash(st === "potential" || st === "contract_party" || st === "mk_na" ? [2, 2] : []);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = `rgba(${lc},${(0.98 * labA).toFixed(3)})`;
        ctx.fillText(short, sx, by + 1);
      }
      ctx.globalCompositeOperation = "lighter";
    }
  }

  /** Cracks + optional shatter fragments. Damage scales with stress rank (financially gated). */
  private drawPlanetDamage(r: NodeRT, sx: number, sy: number, R: number, rank: number, a: number) {
    const { ctx } = this;
    const nCracks = rank >= 4 ? 9 : rank >= 3 ? 6 : 3;
    const depth = rank >= 4 ? 0.95 : rank >= 3 ? 0.7 : 0.35;
    const rnd = seeded((r.n.id.charCodeAt(0) * 7919) ^ (rank * 1301));
    ctx.save();
    ctx.globalCompositeOperation = "source-over";
    for (let i = 0; i < nCracks; i++) {
      const ang = rnd() * Math.PI * 2;
      const lenCrack = R * (0.45 + rnd() * 0.5) * depth;
      const wiggle = (rnd() - 0.5) * 0.5;
      ctx.strokeStyle = rgba([20, 12, 18], (0.55 + depth * 0.35) * a);
      ctx.lineWidth = Math.max(1, R * 0.06 * depth);
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(sx + Math.cos(ang) * R * 0.08, sy + Math.sin(ang) * R * 0.08);
      ctx.quadraticCurveTo(
        sx + Math.cos(ang + wiggle) * lenCrack * 0.55,
        sy + Math.sin(ang + wiggle) * lenCrack * 0.55,
        sx + Math.cos(ang) * lenCrack,
        sy + Math.sin(ang) * lenCrack,
      );
      ctx.stroke();
      ctx.strokeStyle = rgba([255, 160, 90], 0.25 * depth * a);
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Dust sparks at high stress
    if (rank >= 3 && !this.reduceMotion) {
      for (let i = 0; i < (rank >= 4 ? 10 : 5); i++) {
        const ang = rnd() * Math.PI * 2;
        const d = R * (0.9 + rnd() * 0.55 + Math.sin(this.time * 3 + i) * 0.08);
        ctx.fillStyle = rgba(r.color, 0.35 * a);
        ctx.beginPath();
        ctx.arc(sx + Math.cos(ang) * d, sy + Math.sin(ang) * d, Math.max(1, R * 0.06), 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Shatter fragments after critical crossing (planet stays selectable / fractured).
    if (r.shatterT !== null && r.frags.length) {
      const age = this.time - r.shatterT;
      const burst = Math.min(1, age / 0.85);
      for (const f of r.frags) {
        f.dist = R * (0.4 + burst * (1.2 + f.size * 2.2));
        const fx = sx + Math.cos(f.ang + f.spin * age) * f.dist;
        const fy = sy + Math.sin(f.ang + f.spin * age) * f.dist;
        const alpha = (1 - Math.min(1, Math.max(0, age - 1.2) / 2.5)) * a;
        if (alpha <= 0.02) continue;
        ctx.fillStyle = rgba(r.color, 0.75 * alpha);
        ctx.beginPath();
        ctx.arc(fx, fy, R * f.size * 0.55, 0, Math.PI * 2);
        ctx.fill();
      }
      // Fractured core outline
      ctx.strokeStyle = rgba([232, 93, 76], 0.7 * a);
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.arc(sx, sy, R * 1.05, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.restore();
  }
}

function quadAt(q: { x0: number; y0: number; cx: number; cy: number; x1: number; y1: number }, t: number) {
  const u = 1 - t;
  return { x: u * u * q.x0 + 2 * u * t * q.cx + t * t * q.x1, y: u * u * q.y0 + 2 * u * t * q.cy + t * t * q.y1 };
}

function distToQuad(x: number, y: number, q: { x0: number; y0: number; cx: number; cy: number; x1: number; y1: number }) {
  let best = Infinity;
  let prev = quadAt(q, 0);
  for (let i = 1; i <= 16; i++) {
    const cur = quadAt(q, i / 16);
    best = Math.min(best, distSeg(x, y, prev.x, prev.y, cur.x, cur.y));
    prev = cur;
  }
  return best;
}

function distSeg(px: number, py: number, ax: number, ay: number, bx: number, by: number) {
  const dx = bx - ax, dy = by - ay;
  const l2 = dx * dx + dy * dy || 1;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / l2));
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
