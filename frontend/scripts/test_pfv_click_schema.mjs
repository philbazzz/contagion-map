/**
 * Regression: PFV/DART records must expose array fields DetailPanel/hover read via .length
 * Run: node scripts/test_pfv_click_schema.mjs
 */
import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const net = JSON.parse(readFileSync(join(root, "public/data/pf/network.json"), "utf8"));

function asArr(v) { return Array.isArray(v); }

let fail = 0;
const assert = (c, m) => { if (!c) { console.error("FAIL", m); fail += 1; } };

const pfvs = net.nodes.filter((n) => n.entity_type === "spv" || n.group === "project_finance");
assert(pfvs.length > 20, "expected many PFVs");

for (const n of pfvs) {
  assert(asArr(n.key_drivers), `${n.id} key_drivers`);
  assert(asArr(n.source_ids), `${n.id} source_ids`);
  assert(asArr(n.roles), `${n.id} roles`);
  // Simulate DetailPanel access that previously crashed
  try {
    void n.key_drivers.length;
    void [...n.source_ids];
  } catch (e) {
    assert(false, `${n.id} detail access: ${e.message}`);
  }
}

for (const e of net.edges) {
  assert(asArr(e.roles), `${e.id} roles`);
  assert(asArr(e.source_ids), `${e.id} source_ids`);
  assert(asArr(e.contract_ids), `${e.id} contract_ids`);
  try {
    void e.roles.length;
    void e.contract_ids.length;
  } catch (err) {
    assert(false, `${e.id} hover access: ${err.message}`);
  }
}

// Previously incomplete nodes
for (const id of ["capstone_meta_idc_pfv", "casequare_busan_jangnim_pfv", "camsquare_seori_pfv"]) {
  const n = net.nodes.find((x) => x.id === id);
  assert(n && asArr(n.key_drivers) && asArr(n.source_ids), `${id} patched`);
}

console.log(fail ? `FAILED ${fail}` : `PASS pfvs=${pfvs.length} edges=${net.edges.length}`);
process.exit(fail ? 1 : 0);
