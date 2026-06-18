"""Graph-guided LLM debugging workflow for the EX04 submission.

The graph controls what context is sent to the LLM. When ``OPENAI_API_KEY`` is
set, the investigator and planner nodes call an OpenAI-compatible chat model.
When no key is available, the workflow records that it used the local fallback
so tests and grading can still run.

Node implementations live in ``nodes.py``; LLM helpers in ``llm_support.py``;
the shared state type and context helpers in ``debug_state.py``.
"""

from __future__ import annotations

import json

from langgraph.graph import END, StateGraph

from debug_state import DebugState
from nodes import bug_investigator, fix_planner, graph_reader, verifier


def build_workflow():
    graph = StateGraph(DebugState)
    graph.add_node("graph_reader", graph_reader)
    graph.add_node("bug_investigator", bug_investigator)
    graph.add_node("fix_planner", fix_planner)
    graph.add_node("verifier", verifier)
    graph.set_entry_point("graph_reader")
    graph.add_edge("graph_reader", "bug_investigator")
    graph.add_edge("bug_investigator", "fix_planner")
    graph.add_edge("fix_planner", "verifier")
    graph.add_edge("verifier", END)
    return graph.compile()


def main() -> None:
    result = build_workflow().invoke(
        {
            "question": "Why does foo() return a growing list on repeated calls?",
            "target_node": "foo()",
        }
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
