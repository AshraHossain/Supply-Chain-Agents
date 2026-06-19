"""FastAPI service exposing the supply chain agent graph."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from langgraph.types import Command
from pydantic import BaseModel

from .config import settings
from .data import mock_data
from .graph import graph

app = FastAPI(title="Supply Chain AI Agent System", version="0.1.0")


class RunRequest(BaseModel):
    sku: str
    store_id: str = "STORE-001"
    request: str = "Routine replenishment check."


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    approver: str = "human"
    reason: str | None = None


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _extract_interrupt(result: dict[str, Any]):
    intr = result.get("__interrupt__")
    if not intr:
        return None
    item = intr[0]
    return getattr(item, "value", item)


def _shape(thread_id: str, result: dict[str, Any]) -> dict:
    interrupt = _extract_interrupt(result)
    if interrupt is not None:
        return {"thread_id": thread_id, "status": "awaiting_approval",
                "approval_request": interrupt}
    return {
        "thread_id": thread_id,
        "status": "completed",
        "purchase_order": result.get("purchase_order"),
        "evaluation": result.get("evaluation"),
        "exceptions": result.get("exceptions", []),
        "decisions": result.get("decisions", []),
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model}


@app.get("/skus")
def skus() -> dict:
    return {"skus": mock_data.known_skus()}


@app.post("/run")
def run(req: RunRequest) -> dict:
    thread_id = str(uuid.uuid4())
    result = graph.invoke(req.model_dump(), _config(thread_id))
    return _shape(thread_id, result)


@app.post("/approve")
def approve(req: ApprovalRequest) -> dict:
    payload = {"approved": req.approved, "approver": req.approver, "reason": req.reason}
    try:
        result = graph.invoke(Command(resume=payload), _config(req.thread_id))
    except Exception as exc:  # unknown / already-completed thread
        raise HTTPException(status_code=404,
                            detail=f"No paused run for thread_id={req.thread_id}: {exc}")
    return _shape(req.thread_id, result)
