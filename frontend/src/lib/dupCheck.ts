/** Flags projects whose Korean/English/address names normalize to the same key. Never merges — review only. */
export interface DupGroup { key: string; ids: string[]; names: string[] }

const STRIP = /\(.*?\)|주식회사|㈜|\s|데이터센터|data ?center|idc|\bdc\b|pfv|피에프브이|프로젝트|project/gi;

export function normName(s: string | null | undefined): string {
  return (s || "").toLowerCase().replace(STRIP, "");
}

export function findDuplicateProjects(projects: { id: string; name?: string | null; name_ko?: string | null; address?: string | null }[]): DupGroup[] {
  const g = new Map<string, { ids: Set<string>; names: Set<string> }>();
  for (const p of projects) {
    for (const nm of [p.name_ko, p.name]) {
      const k = normName(nm);
      if (k.length < 3) continue;
      const cur = g.get(k) || { ids: new Set(), names: new Set() };
      cur.ids.add(p.id);
      if (nm) cur.names.add(nm);
      g.set(k, cur);
    }
  }
  return [...g.entries()]
    .filter(([, v]) => v.ids.size > 1)
    .map(([key, v]) => ({ key, ids: [...v.ids], names: [...v.names] }))
    .sort((a, b) => b.ids.length - a.ids.length);
}
