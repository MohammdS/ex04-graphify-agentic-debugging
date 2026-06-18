"""Run result type, success scoring, and aggregation for the token comparison."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunResult:
    iteration: int
    name: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    estimated_prompt_tokens: int
    diagnosis_success: bool
    fix_success: bool
    success: bool
    success_criteria: list[str]
    response_preview: str
    usage_source: str


def evaluate_response(content: str) -> tuple[bool, bool, list[str]]:
    lowered = content.lower()
    diagnosis_terms = [
        "mutable default",
        "default argument",
        "shared",
        "same list",
        "function definition time",
    ]
    fix_terms = [
        "bar=none",
        "is none",
        "bar = []",
        "new list",
        "fresh list",
    ]
    diagnosis_hits = [term for term in diagnosis_terms if term in lowered]
    fix_hits = [term for term in fix_terms if term in lowered]
    diagnosis_success = len(diagnosis_hits) >= 2
    fix_success = "bar=none" in lowered and ("is none" in lowered or "new list" in lowered or "fresh list" in lowered)
    criteria = [
        f"diagnosis_terms_found={diagnosis_hits}",
        f"fix_terms_found={fix_hits}",
        "requires mutable/default/shared-list diagnosis and None-sentinel fix",
    ]
    return diagnosis_success, fix_success, criteria


def average(values: list[int | float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 2)


def success_rate(results: list[RunResult]) -> float:
    if not results:
        return 0.0
    return round(sum(1 for result in results if result.success) / len(results), 2)
