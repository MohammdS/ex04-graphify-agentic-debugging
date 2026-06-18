"""LangGraph node functions for the graph-guided debugging workflow.

Each node mutates and returns the shared :class:`DebugState`. The graph controls
what context reaches the LLM: ``graph_reader`` bounds the context to the target
node's neighborhood, then the investigator and planner call the model.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from debug_state import (
    BUG_CONTEXT_PATH,
    GRAPH_PATH,
    ROOT,
    DebugState,
    estimate_tokens,
    read_prompt,
    source_context_for,
)
from llm_support import (
    FALLBACK_EVIDENCE,
    FALLBACK_FIX_PLAN,
    FALLBACK_ROOT_CAUSE,
    call_llm,
    merge_usage,
)


def graph_reader(state: DebugState) -> DebugState:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    nodes = graph["nodes"]
    links = graph["links"]
    target = state.get("target_node", "foo()")
    target_nodes = [node for node in nodes if node.get("label") == target]
    target_ids = {node["id"] for node in target_nodes}
    neighbors = [
        edge
        for edge in links
        if edge.get("source") in target_ids or edge.get("target") in target_ids
    ]
    source_context = source_context_for(target_nodes)
    graph_context_tokens = estimate_tokens(json.dumps(target_nodes + neighbors))
    bug_brief = json.loads(BUG_CONTEXT_PATH.read_text(encoding="utf-8"))
    original_source = bug_brief.get("original_source")
    if original_source:
        foobar_key = next(
            (key for key in source_context if key.endswith("foobar.py")),
            "src/buggy_python/foobar.py",
        )
        source_context[foobar_key] = original_source
    source_context_tokens = estimate_tokens(json.dumps(source_context))
    bug_context_tokens = estimate_tokens(json.dumps(bug_brief))
    state["graph_summary"] = {
        "node_count": len(nodes),
        "edge_count": len(links),
        "target": target_nodes,
        "neighbors": neighbors,
        "estimated_graph_tokens": graph_context_tokens,
        "estimated_source_tokens": source_context_tokens,
        "estimated_bug_context_tokens": bug_context_tokens,
        "estimated_context_tokens": graph_context_tokens + source_context_tokens + bug_context_tokens,
    }
    state["source_context"] = source_context
    state["bug_brief"] = bug_brief
    state["prompts"] = {
        "graph_reader": read_prompt("graph_reader.md"),
        "bug_investigator": read_prompt("bug_investigator.md"),
        "fix_planner": read_prompt("fix_planner.md"),
        "verifier": read_prompt("verifier.md"),
    }
    state["llm_used"] = False
    state["llm_model"] = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    state["llm_usage"] = {}
    state["llm_outputs"] = {}
    return state


def bug_investigator(state: DebugState) -> DebugState:
    user_prompt = json.dumps(
        {
            "question": state["question"],
            "graph_summary": state["graph_summary"],
            "bug_brief": state["bug_brief"],
            "source_context": state["source_context"],
            "task": "Identify the root cause and cite graph/source evidence.",
        },
        indent=2,
    )
    llm_output, usage = call_llm(state["prompts"]["bug_investigator"], user_prompt)
    if llm_output and not llm_output.startswith("LLM call failed"):
        state["llm_used"] = True
        state["llm_usage"] = merge_usage(state.get("llm_usage", {}), usage)
        state["llm_outputs"]["bug_investigator"] = llm_output
        state["root_cause"] = llm_output
        state["evidence"] = ["LLM analysis (graph-guided context):", llm_output]
    else:
        state["root_cause"] = FALLBACK_ROOT_CAUSE
        state["evidence"] = list(FALLBACK_EVIDENCE)
    return state


def fix_planner(state: DebugState) -> DebugState:
    user_prompt = json.dumps(
        {
            "question": state["question"],
            "root_cause": state["root_cause"],
            "evidence": state["evidence"],
            "llm_investigation": state["llm_outputs"].get("bug_investigator"),
            "task": "Suggest the minimal code fix and regression test. Do not modify files.",
        },
        indent=2,
    )
    llm_output, usage = call_llm(state["prompts"]["fix_planner"], user_prompt)
    if llm_output and not llm_output.startswith("LLM call failed"):
        state["llm_used"] = True
        state["llm_usage"] = merge_usage(state.get("llm_usage", {}), usage)
        state["llm_outputs"]["fix_planner"] = llm_output
        state["fix_plan"] = [llm_output]
    else:
        state["fix_plan"] = list(FALLBACK_FIX_PLAN)
    return state


def verifier(state: DebugState) -> DebugState:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    state["verification"] = completed.stdout.strip() or completed.stderr.strip()
    return state
