/**
 * Normalized company search for Contagion Map (PF + semiconductor).
 * Display names are preserved; matching uses stripped corporate suffixes.
 */
import type { NetNode } from "../types";
import { displayName } from "./displayName";
import { GROUP_LABEL } from "./format";

const CORP_SUFFIX = /(?:주식회사|\(주\)|㈜|유한회사|\(유\)|㈘|합자회사|합명회사|\s+Co\.?\s*Ltd\.?|\s+Inc\.?|\s+Corp\.?|\s+LLC\.?)/gi;

export function normalizeSearchText(s: string): string {
  return (s || "")
    .toLowerCase()
    // Expand common KR corporate abbreviations used in search boxes
    .replace(/피에프브이/g, "pfv")
    .replace(/에스피씨/g, "spc")
    .replace(/피티이/g, "pte")
    .replace(CORP_SUFFIX, "")
    .replace(/[\s\-_.·]/g, "")
    .trim();
}

export type SearchHit = {
  id: string;
  rank: number;
  label: string;
  meta: string;
  group: string;
  groupLabel: string;
};

type Indexed = {
  id: string;
  node: NetNode;
  label: string;
  raw: string;
  norm: string;
  tokens: string[];
};

function indexNode(n: NetNode): Indexed {
  const aliases = [
    n.name,
    n.name_ko || "",
    (n as { name_en?: string }).name_en || "",
    n.ticker || "",
    n.id,
    ...(((n as { aliases?: string[] }).aliases) || []),
  ].filter(Boolean);
  const raw = aliases.join(" ").toLowerCase();
  const norm = normalizeSearchText(aliases.join(" "));
  return {
    id: n.id,
    node: n,
    label: displayName(n),
    raw,
    norm,
    tokens: aliases.map((a) => normalizeSearchText(a)).filter(Boolean),
  };
}

export function buildSearchIndex(nodes: NetNode[]): Indexed[] {
  return nodes
    .filter((n) => {
      if ((n as { is_company?: boolean }).is_company === false) return false;
      if (n.entity_type === "project" || n.entity_type === "operating_asset" || n.entity_type === "market_aggregate") {
        return false;
      }
      return true;
    })
    .map(indexNode);
}

/** Rank: 0 exact · 1 prefix · 2 substring · 3 fuzzy-token. Lower is better. */
export function searchCompanies(index: Indexed[], query: string, limit = 40): SearchHit[] {
  const q0 = query.trim();
  if (!q0) return [];
  const qRaw = q0.toLowerCase();
  const q = normalizeSearchText(q0);
  if (!q && !qRaw) return [];

  const hits: SearchHit[] = [];
  for (const row of index) {
    let rank = 99;
    for (const t of row.tokens) {
      if (!t && !q) continue;
      if (t === q || t === qRaw.replace(/\s/g, "")) rank = Math.min(rank, 0);
      else if (t.startsWith(q) || row.raw.startsWith(qRaw)) rank = Math.min(rank, 1);
      else if (t.includes(q) || row.raw.includes(qRaw) || row.norm.includes(q)) rank = Math.min(rank, 2);
    }
    if (rank === 99 && q.length >= 2 && row.norm.includes(q)) rank = 2;
    if (rank >= 99) continue;
    const region = (row.node as { region?: string }).region;
    const metaParts = [
      GROUP_LABEL[row.node.group] || row.node.group,
      region === "KR" ? "KR" : region || "",
      row.node.ticker || row.node.entity_type || "",
    ].filter(Boolean);
    hits.push({
      id: row.id,
      rank,
      label: row.label,
      meta: metaParts.join(" · "),
      group: row.node.group,
      groupLabel: GROUP_LABEL[row.node.group] || row.node.group,
    });
  }
  hits.sort((a, b) => a.rank - b.rank || a.label.localeCompare(b.label, "ko"));
  return hits.slice(0, limit);
}
