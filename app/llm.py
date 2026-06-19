"""Configurable LLM client with structured output.

Supports four providers via LLM_PROVIDER:
  - openrouter : OpenAI-compatible gateway (OpenRouter), any model it serves
  - anthropic  : langchain-anthropic ChatAnthropic
  - openai     : langchain-openai ChatOpenAI
  - mock       : no API key; returns the deterministic `fallback` proposal

Every agent computes a deterministic proposal from its tools, then asks the LLM
to review it and return a validated structured object (adding judgement +
rationale). In `mock` mode the proposal is returned verbatim, so the whole
graph runs end-to-end with zero credentials — ideal for CI and demos.
"""
from __future__ import annotations

import json
from typing import Type, TypeVar

from pydantic import BaseModel

from .config import settings

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self.model_name = settings.llm_model
        self._model = None
        if self.provider != "mock":
            self._model = self._build_model()

    def _build_model(self):
        if self.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            if not settings.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY is required for provider 'anthropic'.")
            return ChatAnthropic(model=self.model_name, temperature=0,
                                 api_key=settings.anthropic_api_key)
        if self.provider == "openai":
            from langchain_openai import ChatOpenAI

            if not settings.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is required for provider 'openai'.")
            return ChatOpenAI(model=self.model_name, temperature=0,
                              api_key=settings.openai_api_key)
        if self.provider == "openrouter":
            from langchain_openai import ChatOpenAI

            if not settings.openrouter_api_key:
                raise RuntimeError("OPENROUTER_API_KEY is required for provider 'openrouter'.")
            return ChatOpenAI(model=self.model_name, temperature=0,
                              api_key=settings.openrouter_api_key,
                              base_url=settings.openrouter_base_url)
        raise ValueError(f"Unknown LLM_PROVIDER: {self.provider!r}")

    def decide(
        self,
        schema: Type[T],
        system: str,
        context: dict,
        fallback: dict,
    ) -> T:
        """Return a validated `schema` instance.

        `fallback` is a deterministic proposal that must satisfy `schema`.
        In mock mode it is returned as-is; otherwise it primes the LLM.
        """
        if self.provider == "mock":
            return schema(**fallback)

        if self.provider == "openrouter":
            # Broadest compatibility across OpenRouter-hosted models.
            structured = self._model.with_structured_output(schema, method="function_calling")
        else:
            structured = self._model.with_structured_output(schema)
        user = (
            "Tool data (read live, do not invent values):\n"
            f"{json.dumps(context, indent=2)}\n\n"
            "A rule-based proposal has been pre-computed for you:\n"
            f"{json.dumps(fallback, indent=2)}\n\n"
            "Review the proposal against the tool data. Keep it if sound, adjust "
            "if the data warrants, and always fill in a clear, specific rationale."
        )
        return structured.invoke([("system", system), ("human", user)])


_client: LLMClient | None = None


def get_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
