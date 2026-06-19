"""Structured state passed between agents (roadmap step 4: pass structured state)."""
from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field

# --- Structured payloads each agent produces --------------------------------


class Decision(BaseModel):
    """Every agent must explain its decision (roadmap step 6)."""

    agent: str
    summary: str
    rationale: str = Field(..., description="Why this decision was made.")


class DemandForecast(BaseModel):
    sku: str
    horizon_days: int
    forecast_units: int = Field(..., description="Predicted demand over the horizon.")
    confidence: float = Field(..., ge=0, le=1)
    rationale: str


class StockSignal(BaseModel):
    sku: str
    on_hand: int
    reorder_point: int
    needs_reorder: bool
    suggested_quantity: int = Field(..., description="0 if no reorder needed.")
    rationale: str


class DraftOrder(BaseModel):
    sku: str
    quantity: int
    urgency: Literal["low", "normal", "high"]
    rationale: str


class SupplierChoice(BaseModel):
    supplier_id: str
    supplier_name: str
    unit_cost: float
    lead_time_days: int
    rationale: str


class DeliveryPlan(BaseModel):
    dc_id: str
    ship_date: str
    eta_date: str
    carrier: str
    rationale: str


class ExceptionFlag(BaseModel):
    code: str
    severity: Literal["info", "warning", "critical"]
    message: str


class Approval(BaseModel):
    required: bool
    status: Literal["pending", "approved", "rejected", "auto-approved"] = "pending"
    approver: str | None = None
    reason: str | None = None


class Evaluation(BaseModel):
    completeness_score: float = Field(..., ge=0, le=1)
    handoff_quality: float = Field(..., ge=0, le=1)
    notes: str


# --- The graph state --------------------------------------------------------


class SupplyChainState(TypedDict, total=False):
    # Inputs
    sku: str
    store_id: str
    request: str

    # Per-agent structured outputs
    demand_forecast: dict[str, Any]
    stock_signal: dict[str, Any]
    draft_order: dict[str, Any]
    supplier_choice: dict[str, Any]
    delivery_plan: dict[str, Any]
    exceptions: Annotated[list[dict[str, Any]], operator.add]
    approval: dict[str, Any]
    evaluation: dict[str, Any]

    # Audit trail — every decision with its rationale
    decisions: Annotated[list[dict[str, Any]], operator.add]

    # Final result
    purchase_order: dict[str, Any]
