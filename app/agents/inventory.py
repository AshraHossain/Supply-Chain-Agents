"""Inventory agent — Check Stock. One job: turn the forecast into a stock signal."""
from __future__ import annotations

from ..data import mock_data
from ..llm import get_client
from ..state import Decision, StockSignal, SupplyChainState

SAFETY_FACTOR = 1.15  # 15% safety buffer
SYSTEM = (
    "You are the Inventory agent. Your only job is to compare on-hand stock and the "
    "reorder point against forecast demand, and decide whether a reorder is needed "
    "and for how many units. Read live stock first; never assume."
)


def inventory_agent(state: SupplyChainState) -> dict:
    sku = state["sku"]
    inv = mock_data.get_inventory(sku)
    forecast = state.get("demand_forecast", {}).get("forecast_units", 0)

    on_hand = inv["on_hand"]
    reorder_point = inv["reorder_point"]
    target = int(round(forecast * SAFETY_FACTOR))
    needs = on_hand < reorder_point or on_hand < forecast
    qty = max(0, target - on_hand) if needs else 0

    context = {
        "sku": sku, "on_hand": on_hand, "reorder_point": reorder_point,
        "forecast_units": forecast, "safety_factor": SAFETY_FACTOR,
    }
    fallback = {
        "sku": sku,
        "on_hand": on_hand,
        "reorder_point": reorder_point,
        "needs_reorder": needs,
        "suggested_quantity": qty,
        "rationale": (
            f"On-hand {on_hand} vs reorder point {reorder_point} and forecast {forecast}. "
            + (f"Below threshold -> order {qty} to reach target {target} (incl. "
               f"{int((SAFETY_FACTOR-1)*100)}% safety)." if needs
               else "Stock sufficient; no reorder.")
        ),
    }

    result: StockSignal = get_client().decide(StockSignal, SYSTEM, context, fallback)
    decision = Decision(
        agent="inventory",
        summary=("Reorder needed: " + str(result.suggested_quantity) + " units")
        if result.needs_reorder else "Stock sufficient; no reorder.",
        rationale=result.rationale,
    )
    return {"stock_signal": result.model_dump(), "decisions": [decision.model_dump()]}
