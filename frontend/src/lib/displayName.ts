import type { NetNode } from "../types";

const HANGUL = /[가-힣]/;

/** Prefer verified Korean Hangul for KR entities; English stays as name_en / alias. */
export function displayName(
  n: Pick<NetNode, "name" | "name_ko" | "id"> & { region?: string | null; country?: string | null; name_en?: string | null },
): string {
  const ko = (n.name_ko || "").trim();
  const primary = (n.name || "").trim();
  const region = (n as { region?: string }).region || (n as { country?: string }).country;
  if (ko && (region === "KR" || HANGUL.test(ko))) return ko;
  if (region === "KR" && HANGUL.test(primary)) return primary;
  if (HANGUL.test(primary) && !HANGUL.test(ko || "")) return primary;
  return primary || ko || n.id;
}

export function searchHaystack(
  n: Pick<NetNode, "name" | "name_ko" | "ticker" | "id"> & { name_en?: string | null },
): string {
  return [n.name, n.name_ko || "", (n as { name_en?: string }).name_en || "", n.ticker || "", n.id]
    .join(" ")
    .toLowerCase();
}

/** Project dossier / list label — Hangul when available. */
export function projectDisplayName(p: { name?: string; name_ko?: string | null; id: string }): string {
  const ko = (p.name_ko || "").trim();
  if (ko && HANGUL.test(ko)) return ko;
  const nm = (p.name || "").trim();
  return nm || p.id;
}
