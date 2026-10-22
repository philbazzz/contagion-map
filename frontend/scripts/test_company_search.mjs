/**
 * Company search index against live PF network.json
 * Run: node scripts/test_company_search.mjs
 */
import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const net = JSON.parse(readFileSync(join(root, "public/data/pf/network.json"), "utf8"));

const CORP_SUFFIX = /(?:주식회사|\(주\)|㈜|유한회사|\(유\)|㈘)/gi;
const normalize = (s) => (s || "")
  .toLowerCase()
  .replace(/피에프브이/g, "pfv")
  .replace(/에스피씨/g, "spc")
  .replace(CORP_SUFFIX, "")
  .replace(/[\s\-_.·]/g, "")
  .trim();

function buildIndex(nodes) {
  return nodes.filter((n) => {
    if (n.is_company === false) return false;
    if (n.entity_type === "project" || n.entity_type === "operating_asset" || n.entity_type === "market_aggregate") return false;
    return true;
  }).map((n) => {
    const aliases = [n.name, n.name_ko || "", n.name_en || "", n.ticker || "", n.id].filter(Boolean);
    return { id: n.id, raw: aliases.join(" ").toLowerCase(), norm: normalize(aliases.join(" ")), tokens: aliases.map(normalize).filter(Boolean), label: n.name_ko || n.name };
  });
}

function search(index, query, limit = 40) {
  const q0 = query.trim();
  if (!q0) return [];
  const qRaw = q0.toLowerCase();
  const q = normalize(q0);
  const hits = [];
  for (const row of index) {
    let rank = 99;
    for (const t of row.tokens) {
      if (t === q) rank = Math.min(rank, 0);
      else if (t.startsWith(q) || row.raw.startsWith(qRaw)) rank = Math.min(rank, 1);
      else if (t.includes(q) || row.raw.includes(qRaw) || row.norm.includes(q)) rank = Math.min(rank, 2);
    }
    if (rank < 99) hits.push({ id: row.id, rank, label: row.label });
  }
  hits.sort((a, b) => a.rank - b.rank || a.label.localeCompare(b.label, "ko"));
  return hits.slice(0, limit);
}

const index = buildIndex(net.nodes);
let fail = 0;
const assert = (c, m) => { if (!c) { console.error("FAIL", m); fail += 1; } };

assert(index.length > 200, `index size ${index.length}`);

const cases = [
  ["케이스퀘어데이터센터PFV", "casequare_pfv"],
  ["케이스퀘어", null], // multi
  ["가야피에프브이", "gaya_pfv"],
  ["가야PFV", "gaya_pfv"],
  ["엣지코어", "edgecore_pfv"],
  ["KB증권", "kb_sec"],
  ["coreweave", "coreweave"],
  ["주식회사가야피에프브이", "gaya_pfv"],
  ["zzzz-no-such-corp-999", null],
];

for (const [q, expect] of cases) {
  const hits = search(index, q);
  if (expect === null && q.startsWith("zzz")) {
    assert(hits.length === 0, `${q} should be empty`);
  } else if (expect === null) {
    assert(hits.length >= 2, `${q} should be multi, got ${hits.length}`);
  } else {
    assert(hits.some((h) => h.id === expect), `${q} → missing ${expect}; got ${hits.slice(0, 3).map((h) => h.id)}`);
    if (hits[0]) assert(hits[0].id === expect || hits[0].rank <= 1, `${q} top rank weak: ${hits[0].id}`);
  }
}

// Filter-hidden node still in full index
assert(index.some((r) => r.id === "gaya_pfv"), "gaya in full index");

console.log(fail ? `FAILED ${fail}` : `PASS index=${index.length} nodes=${net.nodes.length}`);
process.exit(fail ? 1 : 0);
