"""Enrich profiles.json with verified public financial metrics (no fabrication)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "backend" / "data"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save(name: str, obj: dict) -> None:
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def m(
    id_: str,
    label: str,
    value_usd_m: float | None,
    display: str | None,
    period: str,
    status: str,
    source_ids: list[str],
    note: str | None = None,
) -> dict:
    row = {
        "id": id_,
        "label": label,
        "value_usd_m": value_usd_m,
        "display": display,
        "period": period,
        "status": status,
        "source_ids": source_ids,
    }
    if note:
        row["note"] = note
    return row


NEW_SOURCES = [
    {
        "id": "S_NVDA_FY26_PR",
        "title": "NVIDIA Announces Financial Results for Fourth Quarter and Fiscal 2026",
        "publisher": "NVIDIA / SEC exhibit",
        "date": "2026-02-25",
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000019/q4fy26pr.htm",
        "used_for": "NVIDIA FY2026 GAAP revenue, operating income, cash, debt, FCF",
        "kind": "sec_exhibit",
    },
    {
        "id": "S_MSFT_FY25",
        "title": "Microsoft FY2025 Q4 financial statements / Annual Report",
        "publisher": "Microsoft Investor Relations",
        "date": "2025-07",
        "url": "https://www.microsoft.com/en-us/investor/earnings/fy-2025-q4/balance-sheets",
        "used_for": "Microsoft FY2025 revenue, operating income, cash, debt, OCF",
        "kind": "ir",
    },
    {
        "id": "S_MSFT_10K_FY25",
        "title": "Microsoft Corporation Form 10-K (year ended June 30, 2025)",
        "publisher": "SEC EDGAR",
        "date": "2025-07",
        "url": "https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm",
        "used_for": "Microsoft FY2025 consolidated financials",
        "kind": "10-K",
    },
    {
        "id": "S_TSMC_FY25",
        "title": "TSMC 4Q25 Management Report / 2025 consolidated results",
        "publisher": "TSMC Investor Relations",
        "date": "2026-01",
        "url": "https://investor.tsmc.com/english/quarterly-results",
        "used_for": "TSMC 2025 revenue USD, operating income, CAPEX",
        "kind": "ir",
    },
    {
        "id": "S_TSMC_6K_FY25",
        "title": "TSMC Board approved 2025 financial statements (Form 6-K)",
        "publisher": "SEC EDGAR",
        "date": "2026-02-10",
        "url": "https://www.sec.gov/Archives/edgar/data/1046179/000104617926000017/tsm-boardx20260210x6k.htm",
        "used_for": "TSMC 2025 NT$ revenue and net income board approval",
        "kind": "6-K",
    },
    {
        "id": "S_ORCL_FY25",
        "title": "Oracle Announces Fiscal 2025 Fourth Quarter and Fiscal Full Year Financial Results",
        "publisher": "Oracle Investor Relations",
        "date": "2025-06",
        "url": "https://investor.oracle.com/investor-news/news-details/2025/Oracle-Announces-Fiscal-2025-Fourth-Quarter-and-Fiscal-Full-Year-Financial-Results/default.aspx",
        "used_for": "Oracle FY2025 revenue, operating income, OCF, borrowings",
        "kind": "ir",
    },
    {
        "id": "S_AMZN_FY25",
        "title": "Amazon.com Announces Fourth Quarter / Full Year 2025 Results",
        "publisher": "Amazon / SEC exhibit",
        "date": "2026-02",
        "url": "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000002/amzn-20251231xex991.htm",
        "used_for": "Amazon 2025 net sales, AWS, operating income",
        "kind": "sec_exhibit",
    },
    {
        "id": "S_SKH_FY25",
        "title": "SK hynix Announces FY25 Financial Results",
        "publisher": "SK hynix Newsroom",
        "date": "2026-01-28",
        "url": "https://news.skhynix.com/en/sk-hynix-announces-fy25-financial-results/",
        "used_for": "SK hynix FY2025 KRW revenue and operating profit",
        "kind": "ir",
    },
    {
        "id": "S_SMSN_FY25",
        "title": "Samsung Electronics Announces Fourth Quarter and FY 2025 Results",
        "publisher": "Samsung Global Newsroom / IR",
        "date": "2026-01",
        "url": "https://news.samsung.com/global/samsung-electronics-announces-fourth-quarter-and-fy-2025-results",
        "used_for": "Samsung Electronics 2025 consolidated revenue and operating profit",
        "kind": "ir",
    },
    {
        "id": "S_SMSN_SOI_FY25",
        "title": "Samsung Electronics Consolidated Statements of Profit or Loss 2025",
        "publisher": "Samsung IR PDF",
        "date": "2026-01",
        "url": "https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_con_quarter04_soi.pdf",
        "used_for": "Samsung 2025 KRW/USD revenue and operating profit",
        "kind": "ir",
    },
    {
        "id": "S_META_FY25",
        "title": "Meta Reports Fourth Quarter and Full Year 2025 Results",
        "publisher": "Meta Investor Relations",
        "date": "2026-01-28",
        "url": "https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Fourth-Quarter-and-Full-Year-2025-Results/default.aspx",
        "used_for": "Meta FY2025 revenue and operating income",
        "kind": "ir",
    },
    {
        "id": "S_EQIX_FY25",
        "title": "Equinix Reports Fourth Quarter and Full Year 2025 Results",
        "publisher": "Equinix / SEC",
        "date": "2026-02-11",
        "url": "https://www.sec.gov/Archives/edgar/data/1101239/000110123926000030/february112026pressrelease-.htm",
        "used_for": "Equinix 2025 revenue, operating income, AFFO, interest expense",
        "kind": "sec_exhibit",
    },
]

PROFILES = {
    "nvidia": {
        "as_of": "2026-01-25",
        "period_label": "FY2026 (year ended Jan 25, 2026)",
        "currency": "USD",
        "unit": "million",
        "overview": (
            "Fabless AI/accelerated computing designer. GPUs/SoCs manufactured via foundries "
            "(TSMC, Samsung) and memory partners (SK hynix, Micron, Samsung); sold to CSPs, OEMs, ODMs."
        ),
        "metrics": [
            m("revenue", "Revenue (GAAP)", 215938, "$215.9B", "FY2026", "VERIFIED", ["S_NVDA_FY26_PR", "S_NVDA_FY26"]),
            m("operating_income", "Operating income (GAAP)", 130387, "$130.4B", "FY2026", "VERIFIED", ["S_NVDA_FY26_PR"]),
            m("ocf", "Operating cash flow", 102718, "$102.7B", "FY2026", "VERIFIED", ["S_NVDA_FY26_PR"], "CFO commentary / non-GAAP FCF bridge"),
            m("fcf", "Free cash flow (company-defined)", 96575, "$96.6B", "FY2026", "VERIFIED", ["S_NVDA_FY26_PR"], "OCF − PPE/intangibles purchases − principal payments on PPE/intangibles"),
            m("cash", "Cash and cash equivalents", 10605, "$10.6B", "2026-01-25", "VERIFIED", ["S_NVDA_FY26_PR"]),
            m("long_term_debt", "Long-term debt", 7469, "$7.5B", "2026-01-25", "VERIFIED", ["S_NVDA_FY26_PR"]),
            m("interest_expense", "Interest expense", 259, "$259M", "FY2026", "VERIFIED", ["S_NVDA_FY26_PR"]),
            m("capex_ppe", "Purchases of PPE and intangibles", 6042, "$6.0B", "FY2026", "VERIFIED", ["S_NVDA_FY26_PR"]),
            m("ebitda", "EBITDA", None, "Not separately highlighted as primary KPI in FY26 PR", "FY2026", "UNKNOWN", ["S_NVDA_FY26_PR"], "Unavailable as a company-emphasized GAAP line in the cited exhibit"),
        ],
        "financing_notes": [
            "Investment-grade public equity (NVDA); modest long-term debt vs cash generation.",
            "AI-cycle exposure is primarily customer CAPEX and supply/capacity commitments, not CoreWeave-style DDTLs.",
            "Places non-cancellable component orders / deposits to secure capacity (10-K).",
        ],
        "risk_factors": [
            "Customer concentration among large CSPs/OEMs",
            "Foundry and CoWoS / advanced packaging capacity",
            "Export controls / geopolitics (Taiwan supply chain)",
            "Competition (AMD, custom ASICs)",
            "Interest-rate shock: direct floating-debt path is limited vs cash flow; secondary path is customer financing stress",
        ],
        "missing": [
            "Instrument-level floating-rate debt schedule comparable to CoreWeave 10-Q Note 10",
            "Named USD value of individual hyperscaler purchase agreements",
        ],
        "source_ids": ["S_NVDA_FY26_PR", "S_NVDA_FY26", "S_NVDA_10K_FY26"],
    },
    "microsoft": {
        "as_of": "2025-06-30",
        "period_label": "FY2025 (year ended June 30, 2025)",
        "currency": "USD",
        "unit": "million",
        "overview": (
            "Hyperscale cloud (Azure), productivity, and AI platform. Strategic investor in and cloud provider to OpenAI; "
            "major NVIDIA GPU customer for Azure AI infrastructure."
        ),
        "metrics": [
            m("revenue", "Revenue", 281724, "$281.7B", "FY2025", "VERIFIED", ["S_MSFT_FY25", "S_MSFT_10K_FY25"]),
            m("operating_income", "Operating income", 128528, "$128.5B", "FY2025", "VERIFIED", ["S_MSFT_FY25"]),
            m("intelligent_cloud_rev", "Intelligent Cloud revenue", 106265, "$106.3B", "FY2025", "VERIFIED", ["S_MSFT_FY25"]),
            m("ocf", "Operating cash flow", 136162, "$136.2B", "FY2025", "VERIFIED", ["S_MSFT_FY25"]),
            m("cash_st_investments", "Cash + short-term investments", 94565, "$94.6B", "2025-06-30", "VERIFIED", ["S_MSFT_FY25"]),
            m("cash", "Cash and cash equivalents", 30242, "$30.2B", "2025-06-30", "VERIFIED", ["S_MSFT_FY25"]),
            m("total_debt", "Long-term debt (incl. current)", 43151, "$43.2B", "2025-06-30", "VERIFIED", ["S_MSFT_FY25"], "Current LT debt $3.0B + LT debt $40.2B; commercial paper $0"),
            m("ppe", "Property and equipment, net", 204966, "$205.0B", "2025-06-30", "VERIFIED", ["S_MSFT_FY25"]),
            m("openai_azure_commit", "OpenAI incremental Azure commitment", 250000, "$250B", "2025-10 agreement", "VERIFIED", ["S_MSFT_OAI_2025", "S_MSFT_10K_OAI"]),
            m("openai_funding_commit", "Cumulative OpenAI funding commitments", 13000, "$13B", "through recapitalization", "VERIFIED", ["S_MSFT_10K_OAI"]),
            m("fcf", "Free cash flow", None, "Not restated as a single GAAP line here", "FY2025", "UNKNOWN", ["S_MSFT_FY25"], "Compute from OCF − capex using 10-K cash flow details if needed"),
        ],
        "financing_notes": [
            "Investment-grade public company with large fixed-rate senior notes program.",
            "OpenAI stake accounted under equity method ($13B cumulative funding commitments).",
            "AI CAPEX visible in rising PPE; refinancing risk is limited relative to OCF but rate rises still affect new issuance.",
        ],
        "risk_factors": [
            "AI CAPEX intensity and power availability",
            "OpenAI partnership economics / competitive cloud shift",
            "Regulatory scrutiny of large AI partnerships",
            "Customer/supplier concentration in GPU and foundry ecosystem (indirect)",
        ],
        "missing": [
            "Full bond-by-bond maturity table in this dataset",
            "Floating vs fixed share of total debt by instrument",
        ],
        "source_ids": ["S_MSFT_FY25", "S_MSFT_10K_FY25", "S_MSFT_OAI_2025", "S_MSFT_10K_OAI", "S_MSFT_FY26Q1"],
    },
    "amazon": {
        "as_of": "2025-12-31",
        "period_label": "FY2025 (year ended Dec 31, 2025)",
        "currency": "USD",
        "unit": "million",
        "overview": (
            "AWS hyperscaler plus retail/advertising. Multi-year NVIDIA GPU deployments alongside custom Trainium silicon."
        ),
        "metrics": [
            m("revenue", "Net sales (consolidated)", 716924, "$716.9B", "FY2025", "VERIFIED", ["S_AMZN_FY25"]),
            m("aws_revenue", "AWS net sales", 128725, "$128.7B", "FY2025", "VERIFIED", ["S_AMZN_FY25"]),
            m("operating_income", "Operating income (consolidated)", 79975, "$80.0B", "FY2025", "VERIFIED", ["S_AMZN_FY25"]),
            m("aws_operating_income", "AWS operating income", 45606, "$45.6B", "FY2025", "VERIFIED", ["S_AMZN_FY25"]),
            m("gpu_commit_units", "NVIDIA GPUs (announced deployments)", None, "~1M (2026–27) + ~2M (2027–28)", "2026 announcements", "VERIFIED", ["S_AWS_NVDA_1M", "S_AWS_NVDA_2M"], "Unit counts disclosed; USD not disclosed"),
            m("total_debt_face", "Long-term debt face (incl. current)", 68800, "~$68.8B face", "2025-12-31", "VERIFIED", ["S_AMZN_FY25"], "Primarily fixed-rate unsecured senior notes per Item 7A commentary"),
            m("cash", "Cash and cash equivalents", None, "See 10-K balance sheet", "2025-12-31", "UNKNOWN", ["S_AMZN_FY25"], "Exact cash line not mirrored from secondary summary in this pass"),
            m("ebitda", "EBITDA", None, "Not used as primary AWS KPI here", "FY2025", "UNKNOWN", ["S_AMZN_FY25"]),
        ],
        "financing_notes": [
            "Investment-grade; AWS CAPEX funded at Amazon parent level.",
            "Debt predominantly fixed-rate senior notes — rate shock hits refinancing/new issuance more than floating coupons.",
        ],
        "risk_factors": [
            "AI CAPEX / power",
            "Custom silicon vs GPU mix",
            "Cloud competition",
            "Indirect: supplier (NVIDIA) and foundry (TSMC via NVIDIA) concentration",
        ],
        "missing": [
            "USD value of NVIDIA purchase agreements",
            "Cash and marketable securities exact line in this profile (see 10-K)",
        ],
        "source_ids": ["S_AMZN_FY25", "S_AWS_NVDA_1M", "S_AWS_NVDA_2M"],
    },
    "oracle": {
        "as_of": "2025-05-31",
        "period_label": "FY2025 (year ended May 31, 2025)",
        "currency": "USD",
        "unit": "million",
        "overview": (
            "Enterprise software and OCI cloud. Expanding NVIDIA GPU supercluster capacity; competes with and partners across AI cloud."
        ),
        "metrics": [
            m("revenue", "Total revenues", 57399, "$57.4B", "FY2025", "VERIFIED", ["S_ORCL_FY25"]),
            m("cloud_support_rev", "Cloud services and license support", 44029, "$44.0B", "FY2025", "VERIFIED", ["S_ORCL_FY25"]),
            m("operating_income", "Operating income", 17678, "$17.7B", "FY2025", "VERIFIED", ["S_ORCL_FY25"]),
            m("interest_expense", "Interest expense", 3578, "$3.6B", "FY2025", "VERIFIED", ["S_ORCL_FY25"]),
            m("ocf", "Operating cash flow", 20800, "$20.8B", "FY2025", "VERIFIED", ["S_ORCL_FY25"]),
            m("borrowings", "Notes payable and other borrowings", 92600, "~$92.6B", "FY2025 YE", "VERIFIED", ["S_ORCL_FY25"], "Current + non-current notes/borrowings per FY results release"),
            m("fcf", "Free cash flow", None, "Not restated as single figure here", "FY2025", "UNKNOWN", ["S_ORCL_FY25"]),
            m("cash", "Cash and cash equivalents", None, "See FY25 balance sheet in release", "FY2025 YE", "UNKNOWN", ["S_ORCL_FY25"]),
        ],
        "financing_notes": [
            "Material notes payable / borrowings relative to peers — interest expense is a first-order sensitivity channel.",
            "Cloud infrastructure growth funds AI GPU cluster buildout (NVIDIA relationship).",
        ],
        "risk_factors": [
            "High absolute debt / interest expense vs AI CAPEX race",
            "Cloud competition (AWS, Azure, Google)",
            "Customer concentration",
            "GPU supply and data-center power",
        ],
        "missing": [
            "Complete instrument maturity schedule in this dataset",
            "Floating vs fixed mix by facility",
        ],
        "source_ids": ["S_ORCL_FY25", "S_ORCL_NV"],
    },
    "tsmc": {
        "as_of": "2025-12-31",
        "period_label": "CY2025 consolidated",
        "currency": "USD/NTD",
        "unit": "mixed",
        "overview": (
            "World's leading pure-play foundry. Customers are fabless designers (NVIDIA, AMD, Apple, Broadcom, etc.). "
            "Does not publicly name customers in financials."
        ),
        "metrics": [
            m("revenue_usd", "Net revenue (USD)", 122420, "$122.4B", "CY2025", "VERIFIED", ["S_TSMC_FY25", "S_TSMC_6K_FY25"]),
            m("revenue_ntd", "Net revenue (NT$)", None, "NT$3,809.05B", "CY2025", "VERIFIED", ["S_TSMC_FY25", "S_TSMC_6K_FY25"]),
            m("operating_income_ntd", "Operating income (NT$)", None, "NT$1,936.09B", "CY2025", "VERIFIED", ["S_TSMC_FY25"]),
            m("operating_margin", "Operating margin", None, "50.8%", "CY2025", "VERIFIED", ["S_TSMC_FY25"]),
            m("capex_usd", "Capital expenditures (USD)", 40900, "$40.9B", "CY2025", "VERIFIED", ["S_TSMC_FY25"]),
            m("capex_guide_2026", "2026 CAPEX guidance", None, "$52–56B", "CY2026 guide", "VERIFIED", ["S_TSMC_FY25"]),
            m("customers", "Customers served", None, "534 customers / 12,682 products", "CY2025", "VERIFIED", ["S_TSMC_FY25"]),
            m("top10_rev_share", "Top-10 customers revenue share", None, "High concentration (press commentary)", "various", "INFERRED", ["S_TSMC_NV_CNBC"], "Named customer mix not disclosed by TSMC"),
            m("debt", "Total debt", None, "See TSMC consolidated balance sheet", "CY2025", "UNKNOWN", ["S_TSMC_FY25"]),
            m("fcf", "Free cash flow", None, "~NT$1T (management commentary)", "CY2025", "INFERRED", ["S_TSMC_FY25"], "Transcript: OCF ~NT$2.3T, CAPEX ~NT$1.3T"),
        ],
        "financing_notes": [
            "Large multi-year CAPEX; ASML tools are critical-path equipment suppliers.",
            "Rate shock transmission is mainly via industry CAPEX cycle and customer demand, not CoreWeave-like floating DDTLs.",
        ],
        "risk_factors": [
            "Geopolitical / Taiwan",
            "Customer concentration (unnamed but high top-10 share)",
            "Advanced packaging capacity",
            "CAPEX intensity and equipment lead times (ASML)",
        ],
        "missing": [
            "Named customer revenue breakdown",
            "USD debt instrument table in this dataset",
        ],
        "source_ids": ["S_TSMC_FY25", "S_TSMC_6K_FY25", "S_TSMC_NV_CNBC", "S_ASML_TSMC"],
    },
    "sk_hynix": {
        "as_of": "2025-12-31",
        "period_label": "FY2025 (K-IFRS)",
        "currency": "KRW",
        "unit": "billion KRW (display)",
        "overview": (
            "HBM / DRAM leader; named NVIDIA memory supplier in NVIDIA 10-K. AI memory cycle is primary earnings driver."
        ),
        "metrics": [
            m("revenue_krw", "Revenue", None, "KRW 97.1467T (~$68.3B press FX)", "FY2025", "VERIFIED", ["S_SKH_FY25"], "USD conversion is press FX, not company-reported USD primary"),
            m("operating_profit_krw", "Operating profit", None, "KRW 47.2063T", "FY2025", "VERIFIED", ["S_SKH_FY25"]),
            m("operating_margin", "Operating margin", None, "49%", "FY2025", "VERIFIED", ["S_SKH_FY25"]),
            m("net_income_krw", "Net income", None, "KRW 42.9479T", "FY2025", "VERIFIED", ["S_SKH_FY25"]),
            m("customer_a", "Single external customer >10% revenue", None, "KRW 23.26T (Customer A)", "FY2025", "VERIFIED", ["S_SKH_FY25"], "Name not disclosed; consistent with NVIDIA concentration narrative but not proven by name in filing"),
            m("ebitda", "EBITDA", None, "Not primary KPI in FY25 release", "FY2025", "UNKNOWN", ["S_SKH_FY25"]),
            m("total_debt", "Total debt (USD)", None, "See KRW balance sheet", "FY2025", "UNKNOWN", ["S_SKH_FY25"]),
        ],
        "financing_notes": [
            "Korean chaebol financing; detailed KRW debt schedule not mirrored in this USD-centric dataset.",
            "FX and USD liabilities create interest/FX sensitivity distinct from SOFR floating AI-cloud loans.",
        ],
        "risk_factors": [
            "HBM CAPEX",
            "Customer concentration (AI GPUs / Customer A)",
            "FX",
            "Competition with Samsung memory",
        ],
        "missing": [
            "USD debt instrument table",
            "Named identity of Customer A",
        ],
        "source_ids": ["S_SKH_FY25", "S_NVDA_10K_FY26"],
    },
    "samsung": {
        "as_of": "2025-12-31",
        "period_label": "FY2025 consolidated",
        "currency": "KRW/USD",
        "unit": "mixed",
        "overview": (
            "Foundry + HBM/memory (DS) plus DX devices. Named in NVIDIA 10-K as wafer foundry and memory supplier."
        ),
        "metrics": [
            m("revenue", "Revenue (consolidated)", 234622, "$234.6B (IR USD column)", "FY2025", "VERIFIED", ["S_SMSN_SOI_FY25", "S_SMSN_FY25"], "KRW 333.6T; USD from Samsung IR convenience translation"),
            m("operating_profit", "Operating profit", 30664, "$30.7B (IR USD column)", "FY2025", "VERIFIED", ["S_SMSN_SOI_FY25", "S_SMSN_FY25"], "KRW 43.6T"),
            m("ds_revenue", "DS Division sales", None, "KRW 130.1T", "FY2025", "VERIFIED", ["S_SMSN_FY25"]),
            m("memory_revenue", "Memory sales", None, "KRW 104.1T", "FY2025", "VERIFIED", ["S_SMSN_FY25"]),
            m("debt", "Total debt", None, "See consolidated balance sheet", "FY2025", "UNKNOWN", ["S_SMSN_SOI_FY25"]),
            m("fcf", "Free cash flow", None, "Not restated here", "FY2025", "UNKNOWN", ["S_SMSN_FY25"]),
        ],
        "financing_notes": [
            "Large diversified balance sheet; instrument-level data not fully ported.",
            "AI exposure via memory/HBM and foundry; DX dilutes pure AI-infra sensitivity.",
        ],
        "risk_factors": [
            "Foundry share vs TSMC",
            "HBM competition with SK hynix",
            "Consumer device cyclicality (DX)",
            "Geopolitics / export controls",
        ],
        "missing": [
            "USD debt instrument table",
            "Foundry vs memory profit split in this profile",
        ],
        "source_ids": ["S_SMSN_FY25", "S_SMSN_SOI_FY25", "S_NVDA_10K_FY26"],
    },
    "meta": {
        "as_of": "2025-12-31",
        "period_label": "FY2025 (year ended Dec 31, 2025)",
        "currency": "USD",
        "unit": "million",
        "overview": (
            "Family of Apps advertising platform with Reality Labs; large AI infrastructure / NVIDIA GPU buyer for training and inference."
        ),
        "metrics": [
            m("revenue", "Revenue", 200966, "$201.0B", "FY2025", "VERIFIED", ["S_META_FY25"]),
            m("operating_income", "Income from operations", 83276, "$83.3B", "FY2025", "VERIFIED", ["S_META_FY25"]),
            m("advertising_rev", "Advertising revenue", 196175, "$196.2B", "FY2025", "VERIFIED", ["S_META_FY25"]),
            m("reality_labs_op_loss", "Reality Labs operating loss", -19193, "$(19.2)B", "FY2025", "VERIFIED", ["S_META_FY25"]),
            m("capex", "CapEx incl. finance-lease principal", 72220, "$72.2B", "FY2025", "VERIFIED", ["S_META_FY25"], "Company-defined CapEx including finance-lease principal payments"),
            m("debt", "Total debt", None, "See Meta 10-K balance sheet", "FY2025", "UNKNOWN", ["S_META_FY25"]),
            m("fcf", "Free cash flow", None, "See cash flow statement", "FY2025", "UNKNOWN", ["S_META_FY25"]),
        ],
        "financing_notes": [
            "Primarily equity-funded with investment-grade access; AI CapEx is the dominant cash use.",
            "Rate shock: more relevant via CapEx financing cost and advertising cycle than floating AI-cloud DDTLs.",
        ],
        "risk_factors": [
            "AI CapEx intensity",
            "Advertising cyclicality",
            "Reality Labs losses",
            "GPU / power supply constraints",
        ],
        "missing": [
            "Debt maturity schedule in this dataset",
            "Named GPU contract USD amounts",
        ],
        "source_ids": ["S_META_FY25"],
    },
    "equinix": {
        "as_of": "2025-12-31",
        "period_label": "FY2025",
        "currency": "USD",
        "unit": "million",
        "overview": (
            "Global colocation / interconnection REIT. Provides data-center capacity used by cloud and enterprise customers; "
            "buys cooling/power infrastructure from suppliers such as Vertiv."
        ),
        "metrics": [
            m("revenue", "Revenues", 9217, "$9.2B", "FY2025", "VERIFIED", ["S_EQIX_FY25"]),
            m("operating_income", "Income from operations", 1848, "$1.85B", "FY2025", "VERIFIED", ["S_EQIX_FY25"]),
            m("adj_ebitda", "Adjusted EBITDA", 4530, "$4.53B", "FY2025", "VERIFIED", ["S_EQIX_FY25"], "Non-GAAP; margin 49%"),
            m("affo", "AFFO", 3761, "$3.76B", "FY2025", "VERIFIED", ["S_EQIX_FY25"], "Non-GAAP REIT metric"),
            m("interest_expense", "Interest expense", 527, "$527M", "FY2025", "VERIFIED", ["S_EQIX_FY25"]),
            m("total_debt", "Total debt principal", None, "See 10-K debt note (~$21B+ senior notes program)", "FY2025", "INFERRED", ["S_EQIX_FY25"], "Exact principal table not fully copied; REIT has material fixed-rate senior notes"),
        ],
        "financing_notes": [
            "REIT capital structure with material senior notes — refinancing/new issuance sensitive to rates.",
            "xScale JV capital plans amplify growth CAPEX needs.",
        ],
        "risk_factors": [
            "Interest expense / refinancing",
            "Power and land availability",
            "Customer concentration among hyperscalers (general industry)",
            "Construction cost inflation",
        ],
        "missing": [
            "Full debt maturity schedule by instrument in this dataset",
            "Named hyperscaler lease USD amounts",
        ],
        "source_ids": ["S_EQIX_FY25"],
    },
    "coreweave": {
        "as_of": "2026-06-30",
        "period_label": "10-Q Q2 2026",
        "currency": "USD",
        "unit": "million",
        "overview": (
            "Specialized AI cloud. Detailed debt instruments, maturities, and floating SOFR exposure already modeled in financials.json."
        ),
        "metrics": [
            m("total_principal", "Total debt principal", 35551, "$35.6B", "2026-06-30", "VERIFIED", ["S_10Q2"]),
            m("cash", "Cash and cash equivalents", 5524, "$5.5B", "2026-06-30", "VERIFIED", ["S_10Q2"]),
            m("ocf_6m", "Operating cash flow (6M)", 3663, "$3.7B", "H1 2026", "VERIFIED", ["S_10Q2"]),
            m("capex_6m", "CAPEX (6M)", 14117, "$14.1B", "H1 2026", "VERIFIED", ["S_10Q2"]),
            m("rpo", "Remaining performance obligations", 103700, "$103.7B", "2026-06-30", "VERIFIED", ["S_10Q2"]),
            m("interest_exp_6m", "Interest expense after capitalization (6M)", 985, "$985M", "H1 2026", "VERIFIED", ["S_10Q2"]),
            m("revenue", "Annual revenue", None, "See latest 10-K/10-Q income statement", "various", "UNKNOWN", ["S_10Q2"], "Full-year revenue not duplicated here; use filings"),
        ],
        "financing_notes": [
            "See financials.json instruments (DDTLs, notes, convertibles) — primary quantified rate-shock borrower in Shock mode.",
            "High floating-rate / SOFR exposure relative to hyperscaler peers.",
        ],
        "risk_factors": [
            "Customer concentration",
            "Refinancing / floating SOFR debt",
            "GPU CAPEX",
            "Interest-rate and credit-spread sensitivity",
        ],
        "missing": [],
        "source_ids": ["S_10Q2"],
    },
}


def main() -> None:
    sources = load("sources.json")
    existing = {s["id"] for s in sources["sources"]}
    added_src = 0
    for s in NEW_SOURCES:
        if s["id"] not in existing:
            sources["sources"].append(s)
            added_src += 1
    save("sources.json", sources)

    profiles_doc = {
        "meta": {
            "as_of": "2026-10-20",
            "note": "Comparable company dossiers from SEC/IR. Missing fields stay explicit (UNKNOWN).",
            "research_pass": "enrich_company_profiles.py",
        },
        "profiles": PROFILES,
    }
    save("profiles.json", profiles_doc)
    print(f"profiles {len(PROFILES)}; new_sources {added_src}; total_sources {len(sources['sources'])}")


if __name__ == "__main__":
    main()
