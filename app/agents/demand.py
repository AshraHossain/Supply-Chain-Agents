"""Demand agent — Predict. One job: forecast demand from POS sales."""
from __future__ import annotations

from statistics import mean

from ..data import mock_data
from ..llm import get_client
from ..state import DemandForecast, Decision, SupplyChainState

HORIZON_DAYS = 7
SYSTEM = (
    "You are the Demand agent in a supermarket supply chain. Your only job is to "
    "forecast unit demand for one SKU over a horizon from recent POS sales. "
    "Account for the weekly weekend uplift visible in the data."
)


def demand_agent(state: SupplyChainState) -> dict:
    sku = state["sku"]
    sales = mock_data.get_pos_sales(sku)

    # Deterministic proposal: mean daily * horizon, rounded up.
    daily = mean(sales[-14:]) if sales else 0
    forecast_units = int(round(daily * HORIZON_DAYS))
    context = {"sku": sku, "recent_pos_sales": sales[-14:], "horizon_days": HORIZON_DAYS}
    fallback = {
        "sku": sku,
        "horizon_days": HORIZON_DAYS,
        "forecast_units": forecast_units,
        "confidence": 0.8 if sales else 0.0,
        "rationale": (
            f"Mean of last 14 days ({daily:.1f} units/day) x {HORIZON_DAYS} days "
            f"= {forecast_units} units."
        ),
    }

    result: DemandForecast = get_client().decide(DemandForecast, SYSTEM, context, fallback)
    decision = Decision(
        agent="demand",
        summary=f"Forecast {result.forecast_units} units over {result.horizon_days}d "
                f"(confidence {result.confidence:.0%}).",
        rationale=result.rationale,
    )
    return {"demand_forecast": result.model_dump(), "decisions": [decision.model_dump()]}
