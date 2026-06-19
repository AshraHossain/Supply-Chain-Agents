"""LangGraph orchestration — the supermarket supply chain as a chain of decisions.

Flow (roadmap "Workflow at a Glance"):
    Predict -> Check Stock -> [Draft Order -> Pick Supplier -> Plan Delivery
    -> Exceptions -> Human Approval -> Execute] -> Evaluate

The bracketed steps only run when a reorder is actually needed. Human approval
is a real LangGraph `interrupt` (roadmap step 5): risky orders pause the graph
until a human resumes it.
"""
from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .agents import (
    delivery_agent,
    demand_agent,
    evaluator_agent,
    exception_agent,
    inventory_agent,
    procurement_agent,
    supplier_agent,
)
from .config import settings
from .state import Approval, Decision, SupplyChainState


def _route_after_inventory(state: SupplyChainState) -> str:
    return "procurement" if state.get("stock_signal", {}).get("needs_reorder") else "evaluator"


def _approval_required(state: SupplyChainState) -> tuple[bool, float, list]:
    order = state.get("draft_order", {})
    supplier = state.get("supplier_choice", {})
    qty = order.get("quantity", 0)
    cost = qty * supplier.get("unit_cost", 0.0)
    criticals = [e for e in state.get("exceptions", []) if e.get("severity") == "critical"]
    required = (
        qty > settings.approval_qty_threshold
        or cost > settings.approval_cost_threshold
        or bool(criticals)
    )
    return required, round(cost, 2), criticals


def human_approval_node(state: SupplyChainState) -> dict:
    """Roadmap step 5 — humans approve risky actions; safe ones auto-approve."""
    required, cost, criticals = _approval_required(state)
    order = state.get("draft_order", {})
    supplier = state.get("supplier_choice", {})

    if not required:
        appr = Approval(required=False, status="auto-approved", approver="system",
                        reason="Within auto-approval policy thresholds; no critical exceptions.")
        decision = Decision(agent="human_approval", summary="Auto-approved (low risk).",
                            rationale=appr.reason)
        return {"approval": appr.model_dump(), "decisions": [decision.model_dump()]}

    # Pause the graph and wait for a human (resumed via Command(resume=...)).
    human = interrupt({
        "type": "approval_request",
        "sku": order.get("sku"),
        "quantity": order.get("quantity"),
        "supplier": supplier.get("supplier_name"),
        "estimated_cost": cost,
        "exceptions": state.get("exceptions", []),
        "question": "Approve this purchase order?",
    })

    if isinstance(human, dict):
        approved = bool(human.get("approved"))
        approver = human.get("approver", "human")
        reason = human.get("reason")
    else:
        approved = bool(human)
        approver, reason = "human", None

    appr = Approval(
        required=True,
        status="approved" if approved else "rejected",
        approver=approver,
        reason=reason or ("Approved by reviewer." if approved else "Rejected by reviewer."),
    )
    decision = Decision(
        agent="human_approval",
        summary=f"{appr.status.capitalize()} by {approver} (est. ${cost:,.2f}).",
        rationale=appr.reason,
    )
    return {"approval": appr.model_dump(), "decisions": [decision.model_dump()]}


def execute_node(state: SupplyChainState) -> dict:
    """Execute — issue the PO if approved, otherwise cancel."""
    appr = state.get("approval", {})
    order = state.get("draft_order", {})
    supplier = state.get("supplier_choice", {})
    plan = state.get("delivery_plan", {})
    approved = appr.get("status") in ("approved", "auto-approved")

    if approved:
        qty = order.get("quantity", 0)
        po = {
            "status": "issued",
            "sku": order.get("sku"),
            "quantity": qty,
            "supplier_id": supplier.get("supplier_id"),
            "supplier_name": supplier.get("supplier_name"),
            "unit_cost": supplier.get("unit_cost"),
            "total_cost": round(qty * supplier.get("unit_cost", 0.0), 2),
            "dc_id": plan.get("dc_id"),
            "eta_date": plan.get("eta_date"),
            "carrier": plan.get("carrier"),
            "approved_by": appr.get("approver"),
        }
        summary = (f"PO issued: {qty} x {po['sku']} from {po['supplier_name']} "
                   f"(${po['total_cost']:,.2f}), ETA {po['eta_date']}.")
        rationale = f"Approval status '{appr.get('status')}' — order released to supplier."
    else:
        po = {"status": "cancelled", "sku": order.get("sku"),
              "reason": appr.get("reason", "Not approved.")}
        summary = "Order cancelled — not approved."
        rationale = appr.get("reason", "Order was rejected at the approval step.")

    decision = Decision(agent="execute", summary=summary, rationale=rationale)
    return {"purchase_order": po, "decisions": [decision.model_dump()]}


def build_graph(checkpointer=None):
    g = StateGraph(SupplyChainState)

    g.add_node("demand", demand_agent)
    g.add_node("inventory", inventory_agent)
    g.add_node("procurement", procurement_agent)
    g.add_node("supplier", supplier_agent)
    g.add_node("delivery", delivery_agent)
    g.add_node("exception", exception_agent)
    g.add_node("human_approval", human_approval_node)
    g.add_node("execute", execute_node)
    g.add_node("evaluator", evaluator_agent)

    g.add_edge(START, "demand")
    g.add_edge("demand", "inventory")
    g.add_conditional_edges("inventory", _route_after_inventory,
                            {"procurement": "procurement", "evaluator": "evaluator"})
    g.add_edge("procurement", "supplier")
    g.add_edge("supplier", "delivery")
    g.add_edge("delivery", "exception")
    g.add_edge("exception", "human_approval")
    g.add_edge("human_approval", "execute")
    g.add_edge("execute", "evaluator")
    g.add_edge("evaluator", END)

    return g.compile(checkpointer=checkpointer or MemorySaver())


# Module-level singleton used by the API.
graph = build_graph()
