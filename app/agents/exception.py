"""Exception agent — catch supplier delays / issues early. One job: flag exceptions."""
from __future__ import annotations

from ..data import mock_data
from ..state import Decision, ExceptionFlag, SupplyChainState


def exception_agent(state: SupplyChainState) -> dict:
    """Rule-based monitor — fast, deterministic, no LLM needed for alerting triggers."""
    flags: list[ExceptionFlag] = []

    supplier = state.get("supplier_choice", {})
    sup_id = supplier.get("supplier_id")
    if sup_id:
        disruption = mock_data.get_disruption(sup_id)
        if disruption:
            flags.append(ExceptionFlag(
                code="SUPPLIER_DISRUPTION", severity="warning",
                message=f"{supplier.get('supplier_name', sup_id)}: {disruption}"))

    lead = supplier.get("lead_time_days", 0)
    urgency = state.get("draft_order", {}).get("urgency")
    if urgency == "high" and lead >= 3:
        flags.append(ExceptionFlag(
            code="SLOW_FULFILMENT", severity="critical",
            message=f"High-urgency order with {lead}d lead time may stock out."))

    if not state.get("supplier_choice", {}).get("supplier_id") or sup_id == "NONE":
        flags.append(ExceptionFlag(
            code="NO_SUPPLIER", severity="critical",
            message="No supplier available for this SKU."))

    summary = (f"{len(flags)} exception(s) flagged." if flags
               else "No exceptions detected.")
    decision = Decision(
        agent="exception",
        summary=summary,
        rationale="; ".join(f"[{f.severity}] {f.message}" for f in flags) or
                  "All upstream signals within normal bounds.",
    )
    return {
        "exceptions": [f.model_dump() for f in flags],
        "decisions": [decision.model_dump()],
    }
