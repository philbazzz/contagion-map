/**
 * Small, dependency-free SVG views used in the analysis rail:
 *  - PathFlow      vertical chain CoreWeave → … → entity, each link labelled with its relationship and evidence
 *  - Timeline      contracts on one time axis (signed → maturity / term end), with a "today" marker
 *  - PriceChart    observed closes (local currency or KRW at each date's FX rate)
 *  - ShareBar      100% bar for disclosed splits (RPO timing)
 * Colours come from the CSS tokens so every view matches the terminal theme.
 */
import { useState } from "react";
import type { NetEdge, NetNode, PathResult, QuoteHistory } from "../types";
import { korUsd, usdM } from "../lib/format";
import { displayName } from "../lib/displayName";

// ---------------------------------------------------------------- PathFlow
export function PathFlow({ path, edges, nodeMap, onSelect, onSelectEdge }: {
  path: PathResult; edges: Map<string, NetEdge>; nodeMap: Map<string, NetNode>;
  onSelect: (id: string) => void; onSelectEdge: (id: string) => void;
}) {
  const W = 308, BOX = 30, GAP = 44;
  const H = path.nodes.length * BOX + (path.nodes.length - 1) * GAP;
  return (
    <svg className="viz pathflow" viewBox={`0 0 ${W} ${H}`} width="100%" height={H} role="img"
      aria-label={`관계 경로: ${path.nodes.map((n) => { const x = nodeMap.get(n); return x ? displayName(x) : n; }).join(" → ")}`}>
      {path.nodes.map((id, i) => {
        const y = i * (BOX + GAP);
        const n = nodeMap.get(id);
        const last = i === path.nodes.length - 1;
        return (
          <g key={id}>
            <g className={`pf-node ${i === 0 ? "is-origin" : last ? "is-target" : ""}`} onClick={() => onSelect(id)} style={{ cursor: "pointer" }}>
              <rect x={0.5} y={y + 0.5} width={W - 1} height={BOX - 1} rx={2} />
              <text x={10} y={y + BOX / 2 + 4} className="pf-name">{n ? displayName(n) : id}</text>
              <text x={W - 10} y={y + BOX / 2 + 4} textAnchor="end" className="pf-tk">{n?.listed ? n.ticker : "비상장"}</text>
            </g>
            {!last ? (() => {
              const e = edges.get(path.edges[i]);
              const y0 = y + BOX, y1 = y + BOX + GAP;
              const inferred = e?.source_status !== "VERIFIED";
              return (
                <g className="pf-link" onClick={() => e && onSelectEdge(e.id)} style={{ cursor: "pointer" }}>
                  <line x1={18} y1={y0 + 3} x2={18} y2={y1 - 6} className={inferred ? "pf-l inf" : "pf-l"} />
                  <path d={`M14 ${y1 - 9} L18 ${y1 - 3} L22 ${y1 - 9}`} className="pf-arrow" />
                  <text x={32} y={y0 + GAP / 2 - 2} className="pf-lbl">{e?.label}</text>
                  <text x={32} y={y0 + GAP / 2 + 12} className="pf-sub">
                    {e?.amount_usd_m !== null && e?.amount_usd_m !== undefined ? `${usdM(e.amount_usd_m)} · ` : ""}{e?.source_status}
                  </text>
                </g>
              );
            })() : null}
          </g>
        );
      })}
    </svg>
  );
}

// ---------------------------------------------------------------- Timeline
export interface TimelineRow {
  id: string; label: string; start: string | null; end: string | null; amount: number | null; amountNote?: string;
  sub?: string; tone?: "debt" | "customer" | "lease" | "backstop"; endKnown?: boolean;
}

const toT = (s: string, endOfPeriod = false): number => {
  const [y, m, d] = s.split("-").map(Number);
  if (!m) return y + (endOfPeriod ? 0.999 : 0);
  return y + (m - 1) / 12 + ((d || (endOfPeriod ? 28 : 1)) - 1) / 365;
};

export function Timeline({ rows, today, from = 2023, to = 2034, onSelect, caption }: {
  rows: TimelineRow[]; today: string; from?: number; to?: number; onSelect?: (id: string) => void; caption?: string;
}) {
  const W = 308, L = 0, AX = 16, ROW = 32;
  const H = AX + rows.length * ROW + 14;
  const x = (t: number) => L + ((t - from) / (to - from)) * (W - L);
  const tNow = toT(today);
  const years: number[] = [];
  for (let y = from; y <= to; y += 2) years.push(y);
  return (
    <div className="tl">
      <svg className="viz timeline" viewBox={`0 0 ${W} ${H}`} width="100%" height={H} role="img" aria-label={caption || "계약 타임라인"}>
        {years.map((y) => (
          <g key={y}>
            <line x1={x(y)} x2={x(y)} y1={AX - 4} y2={H} className="tl-grid" />
            {x(y) < W - 24 ? <text x={x(y) + 2} y={10} className="tl-year">{y}</text> : null}
          </g>
        ))}
        <line x1={x(tNow)} x2={x(tNow)} y1={AX - 4} y2={H - 11} className="tl-now" />
        <text x={x(tNow)} y={H - 2} textAnchor="middle" className="tl-now-t">오늘 {today.slice(0, 7)}</text>
        {rows.map((r, i) => {
          const y = AX + i * ROW;
          const s = r.start ? Math.max(from, toT(r.start)) : from;
          const e = r.end ? Math.min(to, toT(r.end, true)) : to;
          const known = r.end !== null && r.endKnown !== false;
          const remaining = r.end ? toT(r.end, true) - tNow : null;
          return (
            <g key={r.id} className={`tl-row tone-${r.tone || "debt"}`} onClick={() => onSelect?.(r.id)} style={{ cursor: onSelect ? "pointer" : "default" }}>
              <title>{`${r.label}${r.amount !== null ? ` · ${korUsd(r.amount)}` : ""}${r.start ? ` · ${r.start} 체결` : ""}${r.end ? ` · ${r.end} 종료` : " · 종료일 미공시"}`}</title>
              <rect x={0} y={y} width={W} height={ROW - 2} className="tl-hit" />
              <text x={2} y={y + 11} className="tl-lbl">{r.label.length > 30 ? `${r.label.slice(0, 29)}…` : r.label}</text>
              <text x={W - 2} y={y + 11} textAnchor="end" className="tl-amt">
                {r.amount !== null ? usdM(r.amount) : r.amountNote || "금액 미공시"}
                <tspan className="tl-rem">{known && remaining !== null ? (remaining > 0 ? `  ${Math.floor(remaining) ? `${Math.floor(remaining)}년 ` : ""}${Math.round((remaining % 1) * 12)}개월` : "  만기 도래") : "  종료 미공시"}</tspan>
              </text>
              <rect x={x(s)} y={y + 17} width={Math.max(2, x(e) - x(s))} height={7} rx={1} className={known ? "tl-bar" : "tl-bar open"} />
            </g>
          );
        })}
      </svg>
      {caption ? <p className="fine">{caption}</p> : null}
    </div>
  );
}

// ---------------------------------------------------------------- PriceChart
export function PriceChart({ data, krw, loading }: { data: QuoteHistory | null; krw: boolean; loading: boolean }) {
  const W = 308, H = 120, P = 6;
  if (loading) return <p className="muted-line">불러오는 중…</p>;
  if (!data) return null;
  const pts = data.points.filter((p) => (krw ? p.krw !== null : true));
  if (pts.length < 2) {
    return <p className="muted-line">{data.status === "not_supported" || data.status === "not_redistributable" ? data.note : `이력 부족 (${pts.length}일) — ${data.note}`}</p>;
  }
  const vals = pts.map((p) => (krw ? (p.krw as number) : p.close));
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const span = hi - lo || 1;
  const xs = (i: number) => P + (i / (pts.length - 1)) * (W - P * 2);
  const ys = (v: number) => P + (1 - (v - lo) / span) * (H - P * 2 - 14);
  const d = vals.map((v, i) => `${i ? "L" : "M"}${xs(i).toFixed(1)} ${ys(v).toFixed(1)}`).join(" ");
  const up = vals[vals.length - 1] >= vals[0];
  const fmt = (v: number) => (krw || data.currency === "KRW" ? `${Math.round(v).toLocaleString("ko-KR")}원` : `$${v.toFixed(2)}`);
  return (
    <div className="pc">
      <svg className={`viz pricechart ${up ? "up" : "down"}`} viewBox={`0 0 ${W} ${H}`} width="100%" height={H} role="img" aria-label="주가 추이">
        <path d={`${d} L${xs(vals.length - 1)} ${H - 14} L${xs(0)} ${H - 14} Z`} className="pc-area" />
        <path d={d} className="pc-line" />
        <text x={P} y={H - 2} className="pc-ax">{pts[0].date}</text>
        <text x={W - P} y={H - 2} textAnchor="end" className="pc-ax">{pts[pts.length - 1].date}</text>
        <text x={W - P} y={ys(hi) + 9} textAnchor="end" className="pc-ax">{fmt(hi)}</text>
        <text x={W - P} y={ys(lo) - 3} textAnchor="end" className="pc-ax">{fmt(lo)}</text>
      </svg>
      <p className="fine">{data.note}{krw && data.currency !== "KRW" ? " 원화 값은 날짜별 한국수출입은행 매매기준율로 환산했습니다." : ""}</p>
    </div>
  );
}

export function PeriodTabs({ value, onChange }: { value: string; onChange: (p: string) => void }) {
  return (
    <span className="seg seg-xs" role="tablist" aria-label="차트 기간">
      {["1D", "1M", "3M", "6M", "1Y"].map((p) => (
        <button key={p} type="button" role="tab" aria-selected={value === p} className={value === p ? "is-on" : ""} onClick={() => onChange(p)}>{p}</button>
      ))}
    </span>
  );
}

// ---------------------------------------------------------------- ShareBar
export function ShareBar({ parts, total }: { parts: { label: string; pct: number }[]; total: number }) {
  const [hover, setHover] = useState<number | null>(null);
  return (
    <div className="sharebar">
      <div className="sb-track">
        {parts.map((p, i) => (
          <i key={p.label} style={{ width: `${p.pct}%` }} className={`sb-${i}`} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
            data-tip={`${p.label}: ${p.pct}% ≈ ${usdM((total * p.pct) / 100)} (공시 비율 × 총액)`} />
        ))}
      </div>
      <ul className="sb-legend">
        {parts.map((p, i) => (
          <li key={p.label} className={hover === i ? "is-on" : ""}><b className={`sb-${i}`} />{p.label}<span className="num">{p.pct}% · {usdM((total * p.pct) / 100)}</span></li>
        ))}
      </ul>
    </div>
  );
}
