"""Evaluator agent — Evaluate the Workflow (roadmap step 7).

Checks the run for completeness and handoff quality so supplier delays and
broken handoffs are caught early.
"""
from __future__ import annotations

from ..state import Decision, Evaluation, SupplyChainState

_EXPECTED_KEYS = ["demand_forecast", "stock_signal"]
_ORDER_KEYS = ["draft_order", "supplier_choice", "delivery_plan", "approval"]


def evaluator_agent(state: SupplyChainState) -> dict:
    placed_order = bool(state.get("stock_signal", {}).get("needs_reorder"))
    expected = _EXPECTED_KEYS + (_ORDER_KEYS if placed_order else [])
    present = [k for k in expected if state.get(k)]
    completeness = len(present) / len(expected) if expected else 1.0

    # Handoff quality: every decision should carry a non-trivial rationale.
    decisions = state.get("decisions", [])
    with_rationale = [d for d in decisions if len(d.get("rationale", "")) > 15]
    handoff = len(with_rationale) / len(decisions) if decisions else 1.0

    criticals = [e for e in state.get("exceptions", []) if e.get("severity") == "critical"]
    notes = (
        f"{len(present)}/{len(expected)} expected artifacts present; "
        f"{len(with_rationale)}/{len(decisions)} decisions carry a rationale; "
        f"{len(criticals)} critical exception(s)."
    )

    result = Evaluation(
        completeness_score=round(completeness, 2),
        handoff_quality=round(handoff, 2),
        notes=notes,
    )
    decision = Decision(
        agent="evaluator",
        summary=f"Completeness {result.completeness_score:.0%}, "
                f"handoff {result.handoff_quality:.0%}.",
        rationale=result.notes,
    )
    return {"evaluation": result.model_dump(), "decisions": [decision.model_dump()]}
