"""Shared state type, paths, and context helpers for the debugging workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "graph.json"
BUG_CONTEXT_PATH = ROOT / "data" / "original-bug-context.json"
PROMPT_DIR = ROOT / "agent" / "prompts"


class DebugState(TypedDict, total=False):
    question: str
    target_node: str
    prompts: dict[str, str]
    graph_summary: dict[str, Any]
    source_context: dict[str, str]
    bug_brief: dict[str, Any]
    evidence: list[str]
    root_cause: str
    fix_plan: list[str]
    llm_used: bool
    llm_model: str
    llm_usage: dict[str, int]
    llm_outputs: dict[str, str]
    verification: str


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text.split()) * 1.33))


def read_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def source_context_for(target_nodes: list[dict[str, Any]]) -> dict[str, str]:
    context = {}
    for node in target_nodes:
        source_file = node.get("source_file")
        if not source_file:
            continue
        path = ROOT / source_file
        if path.exists():
            context[source_file] = path.read_text(encoding="utf-8")
    return context
