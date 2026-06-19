"""Delivery / DC-planning agent — Plan Delivery. One job: schedule the inbound delivery."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from ..data import mock_data
from ..llm import get_client
from ..state import Decision, DeliveryPlan, SupplyChainState

SYSTEM = (
    "You are the DC Planning / Delivery agent. Your only job is to plan the inbound "
    "delivery: which DC, ship date, ETA, and carrier, using supplier lead time and "
    "the fleet schedule."
)


def _add_days(d: str, n: int) -> str:
    return (datetime.strptime(d, "%Y-%m-%d").date() + timedelta(days=n)).isoformat()


def delivery_agent(state: SupplyChainState) -> dict:
    sku = state["sku"]
    inv = mock_data.get_inventory(sku)
    dc_id = inv.get("dc_id", "DC-UNKNOWN")
    fleet = mock_data.get_fleet(dc_id)
    lead = state.get("supplier_choice", {}).get("lead_time_days", 2)

    ship_date = fleet["next_outbound"]
    eta = _add_days(ship_date, lead)
    context = {"sku": sku, "dc_id": dc_id, "fleet": fleet, "supplier_lead_time_days": lead}
    fallback = {
        "dc_id": dc_id,
        "ship_date": ship_date,
        "eta_date": eta,
        "carrier": fleet["carrier"],
        "rationale": (
            f"Ship from {dc_id} on next outbound {ship_date} via {fleet['carrier']}; "
            f"with {lead}d supplier lead time, ETA {eta}."
        ),
    }

    result: DeliveryPlan = get_client().decide(DeliveryPlan, SYSTEM, context, fallback)
    decision = Decision(
        agent="delivery",
        summary=f"Deliver to {result.dc_id} by {result.eta_date} via {result.carrier}.",
        rationale=result.rationale,
    )
    return {"delivery_plan": result.model_dump(), "decisions": [decision.model_dump()]}
