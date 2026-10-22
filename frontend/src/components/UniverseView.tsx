import { useEffect, useRef, useState } from "react";
import type { NetNode, Network, NodeVisual, QuotesOverview } from "../types";
import { GROUP_COLORS, STATUS_COLORS, Universe } from "../universe/Universe";
import type { Selection } from "../App";
import { GROUP_LABEL, REL_EN, SIM_STATUS_KO, STATUS_KO } from "../lib/format";
import { displayName } from "../lib/displayName";
import { IconKey, IconLayers, IconOrbit, IconTarget } from "./Icons";

const dn = (n?: NetNode | null) => (n ? displayName(n) : "—");

export interface Banner { kicker: string; title: string; lines: string[]; tone: "red" | "orange" | "violet" }

interface Props {
  hidden: boolean;
  net: Network;
  mode: "network" | "market" | "shock";
  staged: boolean;
  focusIds: string[];
  focusKey: string;
  quotesDemo: boolean;
  quotes: QuotesOverview | null;
  origin: string;
  visuals: Record<string, NodeVisual> | null;
  activeEdges: string[];
  usedEdges: string[] | null;
  banner: Banner | null;
  idleLabel: string;
  selection: Selection;
  highlight: { nodes: string[]; edges: string[] };
  hasRun: boolean;
  hiddenCats: string[];
  onToggleCat: (c: string) => void;
  hiddenGroups: string[];
  speed: number;
  resetKey: string;
  /** When true, node selection does not fly the camera (preserves zoom/pan). */
  preserveCameraOnSelect?: boolean;
  /** Explicit locate (search): always fly camera + pin visibility. seq bumps cancel stale requests. */
  locateRequest?: { id: string; seq: number } | null;
  /** Node ids force-visible despite category filters (search pin). */
  pinnedNodeIds?: string[];
  onSelectNode: (id: string) => void;
  onSelectEdge: (id: string) => void;
  onSelectNone: () => void;
  nodeMap: Map<string, NetNode>;
}

type Hover = { kind: "node" | "edge"; id: string; x: number; y: number } | null;

const LAYERS = [
  { id: "financial", label: "금융 계약 · 지분", color: "#F2C14E" },
  { id: "supply", label: "공급망", color: "#B39DFF" },
  { id: "customer", label: "고객 · 약정", color: "#6FA8FF" },
  { id: "facility", label: "데이터센터 임차", color: "#86E3A6" },
];
const LEGEND_GROUPS = [
  "ai_infra", "financial", "customer", "semiconductor", "server", "datacenter", "project_finance",
  "kr_construction", "kr_trust", "kr_savings", "kr_cooperative", "kr_bank", "kr_securities", "kr_am", "kr_insurance", "kr_operator",
];
const LEGEND_STATUS = ["stress_normal", "stress_moderate", "stress_high", "stress_critical", "contract_party", "potential", "insufficient"];

export function UniverseView(p: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const uRef = useRef<Universe | null>(null);
  const cbRef = useRef(p);
  cbRef.current = p;
  const [hover, setHover] = useState<Hover>(null);
  const [autoRotate, setAutoRotate] = useState(false);
  const [pop, setPop] = useState<"layers" | "legend" | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const u = new Universe(canvasRef.current, {
      // Universe already gates callbacks to id-change only; keep React state in sync without xy thrash.
      onHoverNode: (id, x, y) => setHover((h) => {
        if (!id) return h?.kind === "node" ? null : h;
        if (h?.kind === "node" && h.id === id) return h;
        return { kind: "node", id, x, y };
      }),
      onHoverEdge: (id, x, y) => setHover((h) => {
        if (!id) return h?.kind === "edge" ? null : h;
        if (h?.kind === "edge" && h.id === id) return h;
        return { kind: "edge", id, x, y };
      }),
      onSelectNode: (id) => { setPop(null); cbRef.current.onSelectNode(id); },
      onSelectEdge: (id) => { setPop(null); cbRef.current.onSelectEdge(id); },
      onSelectNone: () => { setPop(null); cbRef.current.onSelectNone(); },
    });
    uRef.current = u;
    const ro = new ResizeObserver(() => u.resize());
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => { ro.disconnect(); u.destroy(); uRef.current = null; };
  }, []);

  // Relayout only when topology/origin actually changes — avoid black freezes from redundant 300+ node layouts.
  const netSig = `${p.origin}|${p.net.nodes.length}|${p.net.edges.length}|${p.net.nodes.map((n) => n.id).join(",")}|${p.net.edges.map((e) => e.id).join(",")}`;
  const prevNetSig = useRef("");
  useEffect(() => {
    const u = uRef.current;
    if (!u) return;
    const topoChanged = prevNetSig.current !== netSig;
    prevNetSig.current = netSig;
    u.setData(p.net.nodes, p.net.edges, p.origin);
    // Only re-frame camera when the graph topology actually changes — not on every selection/HMR payload.
    if (topoChanged) u.resetView();
  }, [netSig]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { uRef.current?.setSimState(p.visuals, p.activeEdges, "financial", "", p.staged); }, [p.visuals, p.activeEdges, p.staged]);
  // Shock View playback: frame the entities of the current stage (camera moves slowly, never re-lays out the map)
  useEffect(() => { if (p.focusKey && !p.selection) uRef.current?.focusNodes(p.focusIds); }, [p.focusKey]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { uRef.current?.setUsedEdges(p.usedEdges); }, [p.usedEdges]);
  useEffect(() => {
    const u = uRef.current;
    if (!u) return;
    const nodeId = p.selection?.kind === "node" ? p.selection.id : null;
    u.setSelection(nodeId, p.selection?.kind === "edge" ? p.selection.id : null);
    // PFV/SPC map clicks: keep zoom/pan. Search locate uses locateRequest instead.
    if (nodeId && !p.preserveCameraOnSelect && !p.locateRequest?.id) u.focusNode(nodeId);
  }, [p.selection, p.preserveCameraOnSelect, p.locateRequest?.id]);
  // Search / explicit locate — always frame the target (even for high-degree PFV/SPC).
  const locateSeq = p.locateRequest?.seq ?? 0;
  const locateId = p.locateRequest?.id ?? null;
  useEffect(() => {
    const u = uRef.current;
    if (!u || !locateId || !locateSeq) return;
    u.setPinnedVisible([locateId, ...(p.pinnedNodeIds || [])]);
    u.setSelection(locateId, null);
    u.focusNode(locateId, { preferTarget: true });
  }, [locateSeq, locateId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    uRef.current?.setPinnedVisible([
      ...(p.pinnedNodeIds || []),
      ...(locateId ? [locateId] : []),
      ...(p.selection?.kind === "node" ? [p.selection.id] : []),
    ].filter(Boolean));
  }, [p.pinnedNodeIds, locateId, p.selection]);
  useEffect(() => { uRef.current?.resetView(); }, [p.resetKey]);
  useEffect(() => { uRef.current?.setHighlightPath(p.highlight.nodes, p.highlight.edges); }, [p.highlight]);
  useEffect(() => { uRef.current?.setFilters(p.hiddenCats, p.hiddenGroups); }, [p.hiddenCats, p.hiddenGroups]);
  useEffect(() => { uRef.current?.setSpeed(p.speed); }, [p.speed]);
  useEffect(() => { uRef.current?.setAutoRotate(autoRotate); }, [autoRotate]);
  useEffect(() => { if (p.hidden) setHover(null); }, [p.hidden]);

  return (
    <div className={`map ${p.hidden ? "is-hidden" : ""}`} ref={wrapRef}>
      <canvas ref={canvasRef} className="map-canvas" role="img"
        aria-label="3D 관계망 지도. 드래그로 회전, 휠로 확대, 노드를 클릭하면 분석 패널이 열립니다." />

      <div className={`readout ${p.banner ? `tone-${p.banner.tone}` : ""}`} aria-live="polite">
        {p.banner ? (
          <>
            <p className="ro-k num">{p.banner.kicker}</p>
            <p className="ro-t">{p.banner.title}</p>
            <ul>{(p.banner.lines || []).slice(0, 3).map((l, i) => <li key={i}>{l}</li>)}</ul>
            {(p.banner.lines || []).length > 3 ? <p className="ro-more">+{(p.banner.lines || []).length - 3} · 우측 Stage Log</p> : null}
          </>
        ) : (
          <>
            <p className="ro-k">{p.mode === "market" ? "MARKET VIEW · 관측 시세" : p.mode === "shock" ? "SHOCK VIEW · 가상 시나리오" : "NETWORK VIEW"}</p>
            <p className="ro-t">{p.idleLabel}</p>
          </>
        )}
      </div>

      <div className="map-tools" role="toolbar" aria-label="지도 도구">
        <button type="button" className="mt" onClick={() => uRef.current?.fitAll()} data-tip="Fit All · 전체 네트워크가 보이도록 줌아웃" aria-label="Fit All · 전체 보기"><IconTarget size={14} /></button>
        <button type="button" className={`mt ${autoRotate ? "is-on" : ""}`} onClick={() => setAutoRotate((a) => !a)} data-tip={`자동 회전 ${autoRotate ? "끄기" : "켜기"}`} aria-pressed={autoRotate} aria-label="자동 회전"><IconOrbit size={14} /></button>
        <button type="button" className="mt" onClick={() => uRef.current?.recoverView()} data-tip="시점 복구 · 카메라가 비었을 때" aria-label="시점 복구">↺</button>
        <span className="mt-sep" />
        <button type="button" className={`mt ${pop === "layers" ? "is-on" : ""}`} onClick={() => setPop((x) => (x === "layers" ? null : "layers"))} data-tip="관계 유형 레이어" aria-expanded={pop === "layers"} aria-label="레이어"><IconLayers size={14} /></button>
        <button type="button" className={`mt ${pop === "legend" ? "is-on" : ""}`} onClick={() => setPop((x) => (x === "legend" ? null : "legend"))} data-tip="범례" aria-expanded={pop === "legend"} aria-label="범례"><IconKey size={14} /></button>
      </div>

      {pop === "layers" ? (
        <div className="pop" role="dialog" aria-label="레이어">
          <p className="lbl">Relationship Layers <span className="lbl-aside">화면 표시만</span></p>
          {LAYERS.map((l) => (
            <label key={l.id} className="chk">
              <input type="checkbox" checked={!p.hiddenCats.includes(l.id)} onChange={() => p.onToggleCat(l.id)} />
              <i style={{ background: l.color }} />{l.label}
            </label>
          ))}
        </div>
      ) : null}
      {pop === "legend" ? (
        <div className="pop" role="dialog" aria-label="범례">
          <p className="lbl">Entity</p>
          <ul className="lg">
            {LEGEND_GROUPS.map((g) => <li key={g}><i style={{ background: GROUP_COLORS[g] }} />{GROUP_LABEL[g]}</li>)}
          </ul>
          <p className="lbl">Relationship</p>
          <ul className="lg lines">
            <li><b className="ln solid" />VERIFIED · 확인된 계약·공시 (실선)</li>
            <li><b className="ln dash" />INFERRED · 추론·섹터 경로 (점선) — 확정 익스포저 아님</li>
          </ul>
          <p className="fine">화살·라벨은 “누가 무엇을 공급·대여·보증·임차하는가”를 나타냅니다. 충격 전달 방향은 상세 패널의 「위험 전이 경로」에 별도 표시합니다. 지리적 인접만으로 관계를 만들지 않습니다.</p>
          {p.mode === "market" ? (
            <>
              <p className="lbl">Market View</p>
              <ul className="lg">
                <li><i style={{ background: STATUS_COLORS.mk_up }} />상승 (전일 대비)</li>
                <li><i style={{ background: STATUS_COLORS.mk_down }} />하락</li>
                <li><i style={{ background: STATUS_COLORS.mk_flat }} />보합</li>
                <li><i style={{ background: STATUS_COLORS.mk_na }} />시세 없음 · 미지원</li>
              </ul>
              <p className="fine">한국 시장 관례(상승 빨강 · 하락 파랑). 관측된 주가이며 시뮬레이션 결과가 아닙니다.</p>
            </>
          ) : null}
          {p.hasRun && p.mode === "shock" ? (
            <>
              <p className="lbl">Shock View</p>
              <ul className="lg">
                {LEGEND_STATUS.map((s) => <li key={s}><i style={{ background: STATUS_COLORS[s] }} />{SIM_STATUS_KO[s]}</li>)}
              </ul>
              <p className="fine">직접 노출만 이자 금액을 표시합니다. 연결만으로 손실을 가정하지 않으며, 부도(빨강)는 사용하지 않습니다.</p>
            </>
          ) : null}
          <p className="fine">노드 크기 = 데이터에 지정한 표시 크기(CoreWeave 기준 관계 중요도). 시가총액·위험도를 뜻하지 않습니다.</p>
        </div>
      ) : null}

      <p className="map-hint">Drag 회전 · Wheel 확대 · Hover 직접 관계 강조 · Click 상세</p>

      {hover && !p.hidden ? <HoverCard hover={hover} p={p} /> : null}
    </div>
  );
}

function HoverCard({ hover, p }: { hover: NonNullable<Hover>; p: Props }) {
  const style = { left: hover.x + 14, top: hover.y + 12 };
  if (hover.kind === "edge") {
    const e = p.net.edges.find((x) => x.id === hover.id);
    if (!e) return null;
    return (
      <div className="hc" style={style}>
        <p className="hc-t">{dn(p.nodeMap.get(e.source))} — {dn(p.nodeMap.get(e.target))}</p>
        <p>{e.label}</p>
        <p className="hc-m">{STATUS_KO[e.source_status]}{(e.roles || []).length ? ` · ${(e.roles || []).slice(0, 2).join(", ")}` : ""}</p>
      </div>
    );
  }
  const n = p.nodeMap.get(hover.id);
  if (!n) return null;
  const v = p.visuals?.[n.id];
  const q = p.quotes?.items.find((x) => x.entity === n.id);
  const hasQ = q && q.price !== null && q.price !== undefined;
  const rels = [...new Set(p.net.edges.filter((e) => (e.source === p.origin && e.target === n.id) || (e.target === p.origin && e.source === n.id))
    .map((e) => REL_EN[e.relationship_type] || e.relationship_type))];
  return (
    <div className="hc" style={style}>
      <p className="hc-t">{dn(n)} <span className="num">{n.listed ? `${n.ticker} · ${n.exchange}` : "비상장"}</span></p>
      {hasQ ? (
        <>
          <p className="hc-krw num">{q!.krw?.value ? `${q!.currency === "KRW" ? "" : "원화 환산 "}${Math.round(q!.krw.value).toLocaleString("ko-KR")}원` : "원화 환산 불가"}</p>
          <p className={`hc-px num ${(q!.change_pct ?? 0) > 0 ? "is-up" : (q!.change_pct ?? 0) < 0 ? "is-down" : ""}`}>
            {q!.currency === "KRW" ? "" : `$${q!.price!.toFixed(2)} · `}{q!.change_pct !== null && q!.change_pct !== undefined ? `${q!.change_pct > 0 ? "+" : q!.change_pct < 0 ? "−" : ""}${Math.abs(q!.change_pct).toFixed(2)}%` : "—"}
          </p>
        </>
      ) : n.listed && p.mode === "market" ? <p className="hc-m">{q?.status_ko || "시세 없음"}</p> : null}
      {n.id !== p.origin ? <p className="hc-m">{dn(p.nodeMap.get(p.origin))} 기준: {rels.length ? rels.join(" / ") : "간접·미연결"}</p> : <p className="hc-m">초점 · {n.role}</p>}
      {v && v.status !== "normal" && (p.mode === "market" || p.mode === "shock") ? (
        <p className={`hc-s st-${v.status}`}>{v.label || (p.mode === "shock" ? SIM_STATUS_KO[v.status] : "")}</p>
      ) : null}
    </div>
  );
}
