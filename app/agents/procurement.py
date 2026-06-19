"""Procurement agent — Draft Order. One job: turn a stock signal into a draft order."""
from __future__ import annotations

from ..llm import get_client
from ..state import Decision, DraftOrder, SupplyChainState

SYSTEM = (
    "You are the Procurement agent. Your only job is to convert a stock signal into a "
    "draft purchase order: SKU, quantity, and urgency. Do not pick a supplier."
)


def procurement_agent(state: SupplyChainState) -> dict:
    sku = state["sku"]
    signal = state.get("stock_signal", {})
    qty = signal.get("suggested_quantity", 0)
    on_hand = signal.get("on_hand", 0)
    reorder_point = signal.get("reorder_point", 1) or 1

    # Urgency from how far below the reorder point we are.
    ratio = on_hand / reorder_point
    urgency = "high" if ratio < 0.5 else "normal" if ratio < 0.9 else "low"

    context = {"sku": sku, "suggested_quantity": qty, "on_hand": on_hand,
               "reorder_point": reorder_point}
    fallback = {
        "sku": sku,
        "quantity": qty,
        "urgency": urgency,
        "rationale": (
            f"Draft order for {qty} units. On-hand is {ratio:.0%} of reorder point, "
            f"so urgency = {urgency}."
        ),
    }

    result: DraftOrder = get_client().decide(DraftOrder, SYSTEM, context, fallback)
    decision = Decision(
        agent="procurement",
        summary=f"Draft order: {result.quantity} x {result.sku} ({result.urgency} urgency).",
        rationale=result.rationale,
    )
    return {"draft_order": result.model_dump(), "decisions": [decision.model_dump()]}
