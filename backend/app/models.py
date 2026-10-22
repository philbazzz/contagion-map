"""Pydantic schemas for the v0.4 dataset and the refinancing request.

Data is split into four files that share entity ids:
  entities.json      — who (company / institution, listing, ticker)
  relationships.json — how they are linked (role, channel, evidence)
  financials.json    — CoreWeave debt instruments and filed metrics
  contracts.json     — customer / backstop / lease contracts (commercial ledger)
  sources.json       — every citation, with date
Amounts are USD million. Rates are percent (9.25 = 9.25%).
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

SourceStatus = Literal["VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"]
Channel = Literal["financial", "equity", "supply_chain", "customer", "facility", "contract"]


class Entity(BaseModel):
    id: str
    name: str
    name_ko: Optional[str] = None
    group: str
    sector: str
    entity_type: str = "company"
    role: str = ""
    description: str = ""
    listed: bool
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    quote_currency: Optional[str] = None
    listing_note: Optional[str] = None
    display_size: float = 6
    source_status: SourceStatus
    source_ids: List[str] = Field(default_factory=list)
    key_drivers: List[str] = Field(default_factory=list)


class Relationship(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    impact_channel: Channel
    label: str
    impact_label: str = ""
    source_status: SourceStatus
    source_ids: List[str] = Field(default_factory=list)
    contract_ids: List[str] = Field(default_factory=list)      # financing instruments (financials.json)
    commercial_ids: List[str] = Field(default_factory=list)    # customer / supply / lease contracts (contracts.json)
    amount_usd_m: Optional[float] = None
    amount_note: str = ""
    roles: List[str] = Field(default_factory=list)
    explanation: str = ""


class Participant(BaseModel):
    entity: str
    roles: List[str]
    status: SourceStatus = "VERIFIED"


class Instrument(BaseModel):
    id: str
    name: str
    kind: Literal["term_loan", "revolver", "senior_notes", "convertible", "vendor_financing", "other_loan"]
    currency: str = "USD"
    principal_usd_m: Optional[float] = None
    principal_as_of: str
    principal_note: str = ""
    commitment_usd_m: Optional[float] = None
    effective_rate_pct: Optional[float] = None
    effective_rate_status: SourceStatus
    rate_type: Literal["fixed", "floating", "unknown"]
    coupon_pct: Optional[float] = None
    spread_pct: Optional[float] = None
    base_rate: Optional[str] = None
    floor_pct: Optional[float] = None
    rate_status: SourceStatus
    rate_note: str = ""
    maturity: Optional[str] = None
    maturity_status: SourceStatus
    borrower: Optional[str] = None
    borrower_status: SourceStatus
    recourse: Optional[bool] = None
    amortization: str = ""
    collateral: str = ""
    customer: Optional[str] = None
    signed: Optional[str] = None
    participants: List[Participant] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)


class CommercialContract(BaseModel):
    """Customer, capacity-backstop and lease contracts, as disclosed. Remaining value is never estimated."""
    id: str
    counterparty: str
    kind: Literal["customer", "backstop", "lease", "supply"]
    title: str
    signed: Optional[str] = None
    value_usd_m: Optional[float] = None
    value_basis: str = ""
    term_end: Optional[str] = None
    term_note: str = ""
    history: List[str] = Field(default_factory=list)
    detail: str = ""
    remaining_note: str = "계약별 잔여 미공시"
    status: SourceStatus
    source_ids: List[str] = Field(default_factory=list)


class Source(BaseModel):
    id: str
    title: str
    publisher: str
    date: str
    url: str
    used_for: str
    kind: str


class RefinancingRequest(BaseModel):
    instrument_id: str
    new_rate_pct: float = Field(..., ge=0, le=40)
    amount_usd_m: Optional[float] = Field(None, gt=0)
    basis: Literal["stated", "effective"] = "stated"
    refi_date: Optional[str] = Field(None, pattern=r"^\d{4}(-\d{2})?$")
    success_ratio: float = Field(1.0, ge=0, le=1)
    fee_pct: float = Field(0.0, ge=0, le=10)
    new_tenor_years: int = Field(5, ge=1, le=15)
    sofr_pct: Optional[float] = Field(None, ge=0, le=20)
    capex_absorption_pct: Optional[float] = Field(None, ge=0, le=100)
    gpu_share_pct: Optional[float] = Field(None, ge=0, le=100)
    compare_rates: Optional[List[float]] = None


class RateShockRequest(BaseModel):
    shock_bp: float = Field(..., ge=-500, le=500)
    benchmark: Literal["sofr", "ust_2y", "ust_10y"] = "sofr"
    sofr_pct: Optional[float] = Field(None, ge=0, le=20)
