# Samsung Electronics & SK hynix Hub Expansion Report

**As of:** 2026-10-20  
**Scope:** Evidence-first network + dossier expansion (P0–P8). No UI redesign.

---

## Company Coverage

| Metric | Count |
|--------|------:|
| Existing companies (pre-pass) | 69 |
| Newly added companies | 3 |
| **Final total** | **72** |
| Newly added Korean companies | 1 (`jusung_eng`) |

**New entities**

| ID | Name | Exchange | Why added |
|----|------|----------|-----------|
| `qualcomm` | Qualcomm | Nasdaq:QCOM | Samsung FY2025 BR names Qualcomm as DX mobile-AP supplier |
| `tesla` | Tesla | Nasdaq:TSLA | Samsung FY2025 BR foundry backlog USD 16,544M |
| `jusung_eng` | Jusung Engineering | KOSDAQ:036930 | Repeated DART / BR equipment supply to SK hynix |

**Not added (insufficient primary evidence for a direct edge)**

- Wonik IPS ↔ Samsung Taylor fab (prospective / “expected to sign”)
- Hanmi ↔ Samsung TC bonder (discussion press only; no DART award)
- Samsung ↔ ASML named EUR contract amount (ASML 20-F does not name Samsung; Samsung BR materials table does not list ASML)
- MSFT / Meta “custom HBM” rumors
- Industry HBM share forecasts (e.g. “70% of NVIDIA HBM4”)

---

## Relationship Network

| Metric | Count |
|--------|------:|
| Existing relationships (pre-pass) | 91 |
| New relationships this pass | 9 |
| **Final relationships** | **100** |
| New non-CoreWeave relationships | 9 (all) |
| New US–Korea relationships | 6+ (Apple/Alphabet/NVIDIA/Qualcomm/Tesla–Samsung; NVIDIA/ASML–SKH) |

### Degree hubs (after)

| Entity | Before | After |
|--------|-------:|------:|
| Samsung Electronics | 1 | **6** |
| SK hynix | 2 | **6** |
| NVIDIA (reference) | 24 | 26 (new Samsung AI Factory + SKH tech partnership edges) |

### Remaining weakly connected / isolated (unchanged structural gap)

Still **zero-degree** among prior KR infrastructure candidates without named counterparties in filings used here:  
`ls_electric`, `isu_petasys`, `hd_hyundai_electric`, `hyosung_heavy`, `doosan_enerbility`, `samsung_sds`, `kt`, `lg_electronics`.

Degree-1 new nodes (`qualcomm`, `tesla`, `jusung_eng`) are intentional: each exists because of a verified link to a hub.

---

## Samsung Electronics

### Relationships

| Edge ID | Counterpart | Type | Status | Basis |
|---------|-------------|------|--------|-------|
| `sc_samsung_nv` *(existing)* | NVIDIA | SUPPLIER | VERIFIED | NVIDIA 10-K: foundry + memory |
| `sp_nvidia_samsung_aif` | NVIDIA | STRATEGIC_PARTNERSHIP | VERIFIED | NVIDIA IR 2025-10-31 AI Factory / HBM3E·HBM4 |
| `c_apple_samsung` | Apple | CUSTOMER | VERIFIED | Samsung FY2025 BR top-5 customers |
| `c_alphabet_samsung` | Alphabet | CUSTOMER | VERIFIED | Samsung FY2025 BR top-5 customers |
| `s_samsung_qualcomm` | Qualcomm | SUPPLIER | VERIFIED | Samsung BR DX AP purchases |
| `c_tesla_samsung` | Tesla | CUSTOMER | VERIFIED | Samsung BR foundry backlog USD 16,544M |

**Categories covered:** customer (hyperscaler + OEM + auto foundry), supplier (mobile AP), foundry/memory supply to GPU vendor, strategic manufacturing collaboration.

### Important disclosed financials (KRW)

| Item | Value | Source |
|------|-------|--------|
| Revenue | 333.6조 원 | FY2025 BR / IR |
| Operating income | ~43.6조 원 | IR SOI / BR segments |
| DS revenue / OP | 130.1조 / 24.9조 | BR |
| Facility investment | 52.7조 | BR |
| Cash & equivalents | 57.86조 | BR BS |
| Borrowings (ST+LT+bonds) | ~24.06조 | BR BS |
| PPE acquisitions (CFS) | 47.5조 | BR CFS |
| Top-5 customer share | ~15% | BR |
| Tesla foundry backlog | USD 16.544B | BR order book |

### Official sources

- KIND/DART 제57기 사업보고서 (2026-03-10)
- Samsung IR English Business Report PDF
- Samsung / IR earnings releases
- NVIDIA Form 10-K Manufacturing + NVIDIA IR AI Factory PR

---

## SK hynix

### Relationships

| Edge ID | Counterpart | Type | Status | Basis |
|---------|-------------|------|--------|-------|
| `s_nvidia_skh` *(existing)* | NVIDIA | SUPPLIER | VERIFIED | NVIDIA 10-K memory purchases |
| `sp_nvidia_skh_tech` | NVIDIA | STRATEGIC_PARTNERSHIP | VERIFIED | 2026-06 multi-year tech partnership (company statements) |
| `s_hanmi_skh` *(existing, enriched)* | Hanmi Semiconductor | SUPPLIER | VERIFIED | DART TC bonder awards (incl. 2025-05 KRW 428.1억) |
| `s_skh_asml` | ASML | SUPPLIER | VERIFIED | DART EUV acquisition ~KRW 11.95T through 2027-12 |
| `s_skh_jusung` | Jusung Engineering | SUPPLIER | VERIFIED | DART + Jusung BR supply history |
| `sp_skh_tsmc` | TSMC | STRATEGIC_PARTNERSHIP | **INFERRED** | HBM4 base-die / CoWoS industry alignment; **no bilateral contract USD in filings** |

**Categories covered:** HBM/memory customer (NVIDIA), equipment (EUV, TC bonder, ALD/CVD), inferred packaging/foundry alignment with TSMC.

### Important disclosed financials (KRW)

| Item | Value | Source |
|------|-------|--------|
| Revenue | 97.15조 원 | FY2025 IR / CFS |
| Operating income | 47.21조 원 (margin 49%) | IR / CFS |
| Net income | 42.95조 원 | CFS |
| Cash & equivalents | 14.92조 원 | CFS |
| Total borrowings | 22.25조 원 | CFS |
| PPE acquisitions | 27.52조 원 | CFS |
| ASML EUV commitment | ~11.95조 원 | 2026-03-24 disclosure |
| Customer A (>10%) | 23.26조 (name undisclosed) | BR / IR |
| Debt-to-equity | 45.95% | CFS notes |

### Official sources

- SK hynix FY2025 results newsroom + consolidated FS PDF
- DART EUV / ASML acquisition disclosure
- NVIDIA 10-K; Korea Herald / company statements on 2026 tech partnership
- Hanmi DART `rcpNo=20250516800319`; Jusung FY2025 BR

---

## Research Quality

### Filings / IR reviewed

- Samsung Electronics FY2025 business report (KIND/DART) + EN IR PDF + SOI
- SK hynix FY2025 consolidated FS + results release + ASML EUV major-matter disclosure
- NVIDIA FY2026 Form 10-K Manufacturing
- ASML Form 20-F FY2025 (customer concentration unnamed)
- Jusung Engineering FY2025 business report
- Hanmi Semiconductor DART supply contracts (2025)

### Excluded as unverified

- Named NVIDIA HBM4 volume share percentages (press estimates)
- Samsung–Hanmi / Samsung–Wonik “expected” awards
- Undisclosed hyperscaler HBM contracts beyond Samsung’s named top-5 list
- Direct CoreWeave–Samsung / CoreWeave–SK hynix commercial links (still none)

### Financial data gaps

- Samsung: per-customer revenue split; NVIDIA HBM unit economics; ASML tool count/price
- SK hynix: Customer A legal name; TSMC base-die contract value; detailed debt maturity ladder in dossier (available in CFS notes for follow-up)
- Qualcomm / Tesla: counterparty dossiers only (role + disclosed backlog), not full 10-K metric packs

### Companies needing further research

- Isolated KR power/PCB/DC names (need named DART counterparties)
- Samsung SDS, NAVER, KT commercial AI/cloud links beyond NVIDIA partnerships already mapped
- Advanced packaging peers (ASE already appears only via Hanmi→ASE historical contract context — not added as planet without map-relevant edge)

---

## Technical Validation

| Check | Result |
|-------|--------|
| `load_network()` Pydantic integrity | **OK** (72 nodes / 100 edges) |
| `npm run build` (`prepare:static` + vite) | **OK** — `network.json` 72 / 100 |
| New planets in Market ticker map | `qualcomm`, `tesla`, `jusung_eng` in `tickers.ts` + quotes roster |
| Samsung / SK hynix as focal hubs | Degree 6 each; dossiers in `profiles` with KRW metrics |
| Company Dossiers | Updated for `samsung`, `sk_hynix`; light dossiers for new entities |
| Market tab | Observed quotes only (unchanged; new tickers in roster) |
| Shock tab | Unchanged (CoreWeave SOFR-quant path) |
| Planetary viz | No redesign; larger `display_size` for hubs (11) |
| GitHub Pages path | Static `public/data/network.json` regenerated |

### Implementation artifacts

- `scripts/apply_samsung_skh_hubs.py` — idempotent data apply
- `backend/data/{entities,relationships,sources,profiles}.json`
- `frontend/src/lib/tickers.ts`
- This report: `docs/SAMSUNG_SKH_HUB_EXPANSION.md`

---

## Design note

CoreWeave remains an important financed AI-cloud node, but Samsung and SK hynix are now independent exploration hubs with first-degree customers, suppliers, and strategic partners that do **not** route through CoreWeave. Second/third-degree exploration works through existing graph walk (e.g. Samsung → Alphabet → NVIDIA; SK hynix → ASML ← TSMC).
