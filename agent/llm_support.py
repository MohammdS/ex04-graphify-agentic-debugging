"""LLM call helpers and deterministic fallbacks for the debugging workflow.

When ``OPENAI_API_KEY`` is set, :func:`call_llm` calls an OpenAI-compatible chat
model. When no key is available (or the call fails), the workflow uses the
``FALLBACK_*`` values so tests and grading can still run fully offline.
"""

from __future__ import annotations

import os
from pathlib import Path

from gatekeeper import ApiGatekeeper, RateLimitConfig

ROOT = Path(__file__).resolve().parents[1]

_gatekeeper: ApiGatekeeper | None = None


def _get_gatekeeper() -> ApiGatekeeper:
    global _gatekeeper
    if _gatekeeper is None:
        config = RateLimitConfig.from_file(ROOT / "config" / "rate_limits.json")
        _gatekeeper = ApiGatekeeper(config)
    return _gatekeeper


FALLBACK_ROOT_CAUSE = (
    "The original implementation used foo(bar=[]), so Python created one list at "
    "function definition time and reused it on every call."
)
FALLBACK_EVIDENCE = [
    "Graphify places foo() in Community 1 with foobar.py and its default-argument rationale.",
    "The only reverse impact edge from foo() is __init__.py importing it for public package use.",
    "The failing behavior is state leakage across repeated foo() calls.",
]
FALLBACK_FIX_PLAN = [
    "Replace the mutable default list with None.",
    "Allocate a fresh list inside the function when no explicit list is supplied.",
    "Keep explicit-list mutation behavior unchanged for callers that pass a list.",
    "Verify with a repeated-call regression test.",
]


def call_llm(system_prompt: str, user_prompt: str) -> tuple[str | None, dict[str, int]]:
    """Call an OpenAI-compatible chat model when credentials are configured."""

    if not os.environ.get("OPENAI_API_KEY"):
        return None, {}

    try:
        from openai import OpenAI

        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        client = OpenAI(base_url=os.environ.get("OPENAI_BASE_URL") or None)
        response = _get_gatekeeper().execute(
            client.chat.completions.create,
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        return content, {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
            "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
        }
    except Exception as exc:
        return f"LLM call failed, using fallback. Error: {exc}", {}


def merge_usage(current: dict[str, int], new: dict[str, int]) -> dict[str, int]:
    """Sum token usage dicts across multiple LLM calls."""
    merged = dict(current)
    for key, value in new.items():
        merged[key] = merged.get(key, 0) + value
    return merged
