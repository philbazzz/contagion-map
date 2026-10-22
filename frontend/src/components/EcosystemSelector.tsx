import type { EcosystemId } from "../pf/types";

const OPTIONS: { id: EcosystemId; label: string; tip: string }[] = [
  {
    id: "semiconductor",
    label: "AI SEMICONDUCTOR",
    tip: "CoreWeave-centered AI semiconductor & infrastructure ecosystem (existing model)",
  },
  {
    id: "datacenter_pf",
    label: "AI DATA CENTER PF",
    tip: "US AI data center project finance → Korean financial & industrial transmission",
  },
];

/** Replaces the global-header US Treasury strip. Rates remain in Market tab / calculations. */
export function EcosystemSelector({ value, onChange }: {
  value: EcosystemId;
  onChange: (id: EcosystemId) => void;
}) {
  return (
    <div className="eco-sel" role="tablist" aria-label="Ecosystem">
      <span className="eco-lbl">Ecosystem</span>
      {OPTIONS.map((o) => (
        <button
          key={o.id}
          type="button"
          role="tab"
          aria-selected={value === o.id}
          className={`eco-btn ${value === o.id ? "is-on" : ""}`}
          data-tip={o.tip}
          onClick={() => onChange(o.id)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
