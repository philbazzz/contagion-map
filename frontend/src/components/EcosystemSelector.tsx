import { useRef } from "react";
import type { EcosystemId } from "../pf/types";

const OPTIONS: { id: EcosystemId; label: string; sub: string; tip: string }[] = [
  {
    id: "semiconductor",
    label: "AI 반도체",
    sub: "AI SEMICONDUCTOR",
    tip: "CoreWeave 중심 미국 AI 반도체·인프라 생태계",
  },
  {
    id: "datacenter_pf",
    label: "국내 AI 데이터센터 PF",
    sub: "AI DATA CENTER PF",
    tip: "미국 AI 데이터센터 프로젝트금융 → 국내 금융기관·산업으로의 전달 경로",
  },
];

export type LoadState = { state: "idle" | "loading" | "ready" | "error"; message?: string };

/** Ecosystem switch on its own header row so it is never clipped. Arrow keys move between tabs. */
export function EcosystemSelector({ value, onChange, pfLoad }: {
  value: EcosystemId;
  onChange: (id: EcosystemId) => void;
  pfLoad?: LoadState;
}) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const onKey = (i: number) => (e: { key: string; preventDefault: () => void }) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight" && e.key !== "Home" && e.key !== "End") return;
    e.preventDefault();
    const n = OPTIONS.length;
    const j = e.key === "Home" ? 0 : e.key === "End" ? n - 1 : (i + (e.key === "ArrowRight" ? 1 : n - 1)) % n;
    refs.current[j]?.focus();
    onChange(OPTIONS[j].id);
  };
  return (
    <div className="eco-sel" role="tablist" aria-label="생태계 선택">
      <span className="eco-lbl">생태계</span>
      {OPTIONS.map((o, i) => {
        const on = value === o.id;
        const st = o.id === "datacenter_pf" ? pfLoad?.state : "ready";
        return (
          <button
            key={o.id}
            ref={(el) => { refs.current[i] = el; }}
            type="button"
            role="tab"
            aria-selected={on}
            tabIndex={on ? 0 : -1}
            className={`eco-btn ${on ? "is-on" : ""}`}
            data-tip={o.tip}
            onClick={() => onChange(o.id)}
            onKeyDown={onKey(i)}
          >
            <span className="eco-ko">{o.label}</span>
            <span className="eco-en">{o.sub}</span>
            {st === "loading" ? <span className="eco-st">불러오는 중</span> : st === "error" ? <span className="eco-st is-err">불러오기 실패</span> : null}
          </button>
        );
      })}
    </div>
  );
}
