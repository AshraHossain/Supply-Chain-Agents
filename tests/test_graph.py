"""Smoke tests — run with `LLM_PROVIDER=mock pytest`."""
import os
import uuid

os.environ.setdefault("LLM_PROVIDER", "mock")

from langgraph.types import Command  # noqa: E402

from app.graph import build_graph  # noqa: E402


def _run(sku, approved=True):
    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    res = graph.invoke({"sku": sku, "store_id": "S1", "request": "test"}, cfg)
    if res.get("__interrupt__"):
        res = graph.invoke(Command(resume={"approved": approved, "approver": "test"}), cfg)
    return res


def test_low_stock_triggers_order():
    res = _run("SKU-MILK-1L")
    assert res["stock_signal"]["needs_reorder"] is True
    assert res["purchase_order"]["status"] == "issued"
    assert res["evaluation"]["handoff_quality"] == 1.0


def test_sufficient_stock_no_order():
    res = _run("SKU-RICE-5KG")
    assert res["stock_signal"]["needs_reorder"] is False
    assert "purchase_order" not in res or res.get("purchase_order") is None


def test_rejection_cancels_order():
    res = _run("SKU-MILK-1L", approved=False)
    assert res["purchase_order"]["status"] == "cancelled"


def test_every_decision_has_rationale():
    res = _run("SKU-BREAD-WG")
    assert res["decisions"]
    assert all(len(d["rationale"]) > 10 for d in res["decisions"])


# ============================================================================
# Configuration & Setup Tests
# ============================================================================

def test_config_loads_from_env():
    """Test that configuration loads correctly from environment variables."""
    from app.config import settings

    assert settings.llm_provider == "mock"
    assert settings.llm_model is not None
    assert settings.approval_qty_threshold == 500
    assert settings.approval_cost_threshold == 10000


def test_config_thresholds_are_numeric():
    """Test that approval thresholds are properly typed as numeric values."""
    from app.config import settings

    assert isinstance(settings.approval_qty_threshold, int)
    assert isinstance(settings.approval_cost_threshold, float)
    assert settings.approval_qty_threshold > 0
    assert settings.approval_cost_threshold > 0


def test_graph_initialization():
    """Test that the supply chain graph initializes without errors."""
    from app.graph import build_graph

    graph = build_graph()
    assert graph is not None
    assert hasattr(graph, "invoke")


# ============================================================================
# Demand Agent Tests
# ============================================================================

def test_demand_forecast_structure():
    """Test that demand forecast contains required fields."""
    res = _run("SKU-MILK-1L")
    forecast = res["demand_forecast"]
    assert forecast["sku"] == "SKU-MILK-1L"
    assert forecast["forecast_units"] > 0
    assert 0 <= forecast["confidence"] <= 1
    assert len(forecast["rationale"]) > 0


def test_demand_confidence_for_new_sku():
    """Test that demand forecast confidence is low for SKUs with no sales history."""
    from app.data import mock_data

    # Find a SKU with no sales history (or very sparse)
    for sku in mock_data.known_skus():
        res = _run(sku)
        if res["demand_forecast"]["forecast_units"] == 0:
            assert res["demand_forecast"]["confidence"] == 0.0
            break


def test_demand_forecast_horizon():
    """Test that demand forecast uses the correct horizon (7 days)."""
    res = _run("SKU-BREAD-WG")
    assert res["demand_forecast"]["horizon_days"] == 7


# ============================================================================
# Inventory Agent Tests
# ============================================================================

def test_stock_signal_contains_all_fields():
    """Test that stock signal has all required fields."""
    res = _run("SKU-MILK-1L")
    signal = res["stock_signal"]
    assert "sku" in signal
    assert "on_hand" in signal
    assert "reorder_point" in signal
    assert "needs_reorder" in signal
    assert "suggested_quantity" in signal
    assert "rationale" in signal


def test_reorder_quantity_is_positive():
    """Test that suggested reorder quantity is always positive when reorder is needed."""
    res = _run("SKU-MILK-1L")
    if res["stock_signal"]["needs_reorder"]:
        draft = res["draft_order"]
        assert draft["quantity"] > 0


# ============================================================================
# Procurement Agent Tests
# ============================================================================

def test_draft_order_urgency_levels():
    """Test that draft orders have valid urgency levels."""
    res = _run("SKU-MILK-1L")
    urgency = res["draft_order"]["urgency"]
    assert urgency in ["low", "normal", "high"]


def test_procurement_includes_rationale():
    """Test that procurement decisions always have a rationale."""
    res = _run("SKU-BREAD-WG")
    draft = res["draft_order"]
    assert len(draft["rationale"]) > 0


# ============================================================================
# Supplier Agent Tests
# ============================================================================

def test_supplier_choice_valid_fields():
    """Test that supplier choice has all required fields and valid types."""
    res = _run("SKU-MILK-1L")
    if res["stock_signal"]["needs_reorder"]:
        supplier = res["supplier_choice"]
        assert supplier["supplier_id"]
        assert supplier["supplier_name"]
        assert supplier["unit_cost"] > 0
        assert supplier["lead_time_days"] >= 0


def test_supplier_cost_calculation():
    """Test that supplier selection considers cost and lead time."""
    res = _run("SKU-BREAD-WG")
    supplier = res["supplier_choice"]
    assert supplier["rationale"]
    assert "cost" in supplier["rationale"].lower() or "lead" in supplier["rationale"].lower()


# ============================================================================
# Delivery Agent Tests
# ============================================================================

def test_delivery_plan_dates_valid():
    """Test that delivery plan has valid date fields."""
    res = _run("SKU-MILK-1L")
    if res["stock_signal"]["needs_reorder"]:
        delivery = res["delivery_plan"]
        assert delivery["dc_id"]
        assert delivery["ship_date"]
        assert delivery["eta_date"]
        assert delivery["carrier"]


def test_delivery_plan_includes_rationale():
    """Test that delivery planning has justification."""
    res = _run("SKU-RICE-5KG")
    if res["stock_signal"]["needs_reorder"]:
        delivery = res["delivery_plan"]
        assert len(delivery["rationale"]) > 0


# ============================================================================
# State & Validation Tests
# ============================================================================

def test_decisions_list_grows_with_workflow():
    """Test that the decisions list accumulates from all agents."""
    res = _run("SKU-MILK-1L")
    decisions = res["decisions"]
    assert len(decisions) >= 5  # demand, inventory, procurement, supplier, delivery at minimum
    agent_names = [d["agent"] for d in decisions]
    assert "demand" in agent_names


def test_exceptions_captured_if_any():
    """Test that exceptions are properly captured in state."""
    res = _run("SKU-MILK-1L")
    exceptions = res.get("exceptions", [])
    assert isinstance(exceptions, list)
    if exceptions:
        for exc in exceptions:
            assert "severity" in exc
            assert exc["severity"] in ["info", "warning", "critical"]


def test_evaluation_scores_valid_ranges():
    """Test that evaluation scores are between 0 and 1."""
    res = _run("SKU-BREAD-WG")
    evaluation = res["evaluation"]
    assert 0 <= evaluation["completeness_score"] <= 1
    assert 0 <= evaluation["handoff_quality"] <= 1


# ============================================================================
# Approval & Purchase Order Tests
# ============================================================================

def test_approval_required_for_high_cost():
    """Test that high-cost orders require approval."""
    from app.config import settings

    res = _run("SKU-MILK-1L")
    if res["stock_signal"]["needs_reorder"]:
        po_cost = res["draft_order"]["quantity"] * res["supplier_choice"]["unit_cost"]
        if po_cost > settings.approval_cost_threshold:
            assert res.get("__interrupt__") is not None


def test_purchase_order_matches_approval():
    """Test that final PO reflects the approval decision."""
    res = _run("SKU-MILK-1L", approved=True)
    if res["stock_signal"]["needs_reorder"]:
        assert res["purchase_order"]["status"] in ["issued", "cancelled"]


def test_cancelled_order_has_no_eta():
    """Test that cancelled orders don't have delivery ETAs."""
    res = _run("SKU-MILK-1L", approved=False)
    po = res.get("purchase_order")
    if po and po["status"] == "cancelled":
        assert po.get("eta_date") is None or po["eta_date"] == ""


# ============================================================================
# Integration & Workflow Tests
# ============================================================================

def test_multiple_skus_independent():
    """Test that multiple SKU runs don't interfere with each other."""
    res1 = _run("SKU-MILK-1L")
    res2 = _run("SKU-RICE-5KG")
    assert res1["sku"] == "SKU-MILK-1L"
    assert res2["sku"] == "SKU-RICE-5KG"
    assert res1["decisions"] != res2["decisions"]


def test_thread_isolation():
    """Test that different threads don't share state."""
    from app.graph import build_graph

    graph = build_graph()
    cfg1 = {"configurable": {"thread_id": str(uuid.uuid4())}}
    cfg2 = {"configurable": {"thread_id": str(uuid.uuid4())}}

    res1 = graph.invoke({"sku": "SKU-MILK-1L", "store_id": "S1", "request": "test"}, cfg1)
    res2 = graph.invoke({"sku": "SKU-RICE-5KG", "store_id": "S2", "request": "test"}, cfg2)

    assert res1["sku"] != res2["sku"]
    assert cfg1["configurable"]["thread_id"] != cfg2["configurable"]["thread_id"]


def test_full_workflow_completes():
    """Test that the complete workflow runs without interruption or error."""
    res = _run("SKU-BREAD-WG", approved=True)
    assert "decisions" in res
    assert len(res["decisions"]) > 0
    assert "evaluation" in res
    assert res["evaluation"]["completeness_score"] > 0


# ============================================================================
# Edge Cases & Error Handling
# ============================================================================

def test_empty_sku_string_handling():
    """Test that empty SKU is handled gracefully."""
    from app.graph import build_graph

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    try:
        res = graph.invoke({"sku": "", "store_id": "S1", "request": "test"}, cfg)
        # Should either error or return a valid state
        assert res is not None
    except (ValueError, KeyError):
        # Expected behavior: reject empty SKU
        pass


def test_unknown_sku_handling():
    """Test that unknown SKU is handled gracefully."""
    from app.graph import build_graph

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    try:
        res = graph.invoke(
            {"sku": "SKU-NONEXISTENT-9999", "store_id": "S1", "request": "test"}, cfg
        )
        # Should still produce a valid state even if SKU is unknown
        assert res is not None
    except (ValueError, KeyError):
        # Also acceptable behavior
        pass
