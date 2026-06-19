"""Runtime configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "openrouter").lower()
    llm_model: str = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4.5")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    approval_qty_threshold: int = int(os.getenv("APPROVAL_QTY_THRESHOLD", "500"))
    approval_cost_threshold: float = float(os.getenv("APPROVAL_COST_THRESHOLD", "10000"))


settings = Settings()
