"""Supplier agent — Pick Supplier. One job: choose the best supplier for the order."""
from __future__ import annotations

from ..data import mock_data
from ..llm import get_client
from ..state import Decision, SupplierChoice, SupplyChainState

SYSTEM = (
    "You are the Supplier agent. Your only job is to pick the best supplier for a "
    "draft order, balancing unit cost, lead time, and reliability. Every supplier "
    "choice needs a rationale."
)


def _score(s: dict, urgency: str) -> float:
    # Lower is better. Urgent orders weight lead time more heavily.
    lead_weight = 0.5 if urgency == "high" else 0.25
    return s["unit_cost"] + lead_weight * s["lead_time_days"] + (1 - s["reliability"])


def supplier_agent(state: SupplyChainState) -> dict:
    sku = state["sku"]
    order = state.get("draft_order", {})
    urgency = order.get("urgency", "normal")
    candidates = mock_data.get_suppliers(sku)

    best = min(candidates, key=lambda s: _score(s, urgency)) if candidates else None
    context = {"sku": sku, "urgency": urgency, "candidates": candidates}

    if best is None:
        fallback = {
            "supplier_id": "NONE", "supplier_name": "No supplier available",
            "unit_cost": 0.0, "lead_time_days": 0,
            "rationale": "No supplier in catalog for this SKU.",
        }
    else:
        fallback = {
            "supplier_id": best["supplier_id"],
            "supplier_name": best["supplier_name"],
            "unit_cost": best["unit_cost"],
            "lead_time_days": best["lead_time_days"],
            "rationale": (
                f"Selected {best['supplier_name']}: cost ${best['unit_cost']:.2f}/unit, "
                f"lead {best['lead_time_days']}d, reliability {best['reliability']:.0%} "
                f"— best blended score for {urgency} urgency."
            ),
        }

    result: SupplierChoice = get_client().decide(SupplierChoice, SYSTEM, context, fallback)
    decision = Decision(
        agent="supplier",
        summary=f"Supplier: {result.supplier_name} "
                f"(${result.unit_cost:.2f}/unit, {result.lead_time_days}d lead).",
        rationale=result.rationale,
    )
    return {"supplier_choice": result.model_dump(), "decisions": [decision.model_dump()]}
