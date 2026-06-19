"""End-to-end CLI demo of the supply chain agent graph.

Usage:
    python run_demo.py                 # runs all known SKUs
    python run_demo.py SKU-BREAD-WG    # run one SKU
    AUTO_APPROVE=0 python run_demo.py  # reject at the approval gate

Set LLM_PROVIDER=mock in your .env to run with no API key.
"""
from __future__ import annotations

import os
import sys
import uuid

from langgraph.types import Command

from app.config import settings
from app.data import mock_data
from app.graph import graph


def _line(char: str = "-") -> None:
    print(char * 72)


def run_one(sku: str) -> None:
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    _line("=")
    print(f"SKU: {sku}   |   provider: {settings.llm_provider}   |   thread: {thread_id[:8]}")
    _line("=")

    result = graph.invoke({"sku": sku, "store_id": "STORE-001",
                           "request": "Routine replenishment check."}, config)

    intr = result.get("__interrupt__")
    if intr:
        req = getattr(intr[0], "value", intr[0])
        print("\n  ⏸  HUMAN APPROVAL REQUIRED")
        print(f"     {req.get('quantity')} x {req.get('sku')} from {req.get('supplier')} "
              f"— est. ${req.get('estimated_cost'):,.2f}")
        for e in req.get("exceptions", []):
            print(f"     ⚠  [{e['severity']}] {e['message']}")
        approve = os.getenv("AUTO_APPROVE", "1") != "0"
        print(f"     -> reviewer decision: {'APPROVE' if approve else 'REJECT'}\n")
        result = graph.invoke(
            Command(resume={"approved": approve, "approver": "demo-manager",
                            "reason": "Demo reviewer decision."}),
            config,
        )

    print("\n  DECISION TRAIL (every decision has a rationale):")
    for d in result.get("decisions", []):
        print(f"   • [{d['agent']:>14}] {d['summary']}")
        print(f"       ↳ {d['rationale']}")

    po = result.get("purchase_order")
    if po:
        print("\n  PURCHASE ORDER:")
        for k, v in po.items():
            print(f"     {k}: {v}")

    ev = result.get("evaluation", {})
    if ev:
        print(f"\n  EVALUATION: completeness {ev.get('completeness_score')}, "
              f"handoff {ev.get('handoff_quality')}")
        print(f"     {ev.get('notes')}")
    print()


def main() -> None:
    targets = sys.argv[1:] or mock_data.known_skus()
    for sku in targets:
        run_one(sku)


if __name__ == "__main__":
    main()
