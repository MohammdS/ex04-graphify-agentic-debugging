"""Compare naive and Graphify-guided LangGraph debugging workflows.

Both workflows use the same local OpenAI-compatible model and the same bug. The
only difference is the context supplied to the investigator/planner nodes:

- naive: full source and tests
- graph_guided: Graphify target node neighborhood and target source
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "graph.json"
BUG_CONTEXT_PATH = ROOT / "data" / "original-bug-context.json"
OUTPUT_JSON = ROOT / "data" / "measured-agent-workflow-comparison.json"
OUTPUT_MD = ROOT / "reports" / "MEASURED_AGENT_WORKFLOW_COMPARISON.md"


@dataclass
class LlmCall:
    node: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    estimated_prompt_tokens: int
    usage_source: str


class WorkflowState(TypedDict, total=False):
    strategy: Literal["naive", "graph_guided"]
    target: str
    question: str
    context: dict[str, Any]
    investigation: str
    plan: str
    verification: str
    calls: list[dict[str, Any]]
    diagnosis_success: bool
    fix_success: bool
    success: bool


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text.split()) * 1.33))


def read_text_files(root: Path) -> dict[str, str]:
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in {".py", ".json"}:
            files[str(path.relative_to(ROOT))] = path.read_text(encoding="utf-8")
    return files


def graph_context(target_label: str) -> dict[str, Any]:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    nodes = graph["nodes"]
    links = graph["links"]
    target_nodes = [node for node in nodes if node.get("label") == target_label]
    target_ids = {node["id"] for node in target_nodes}
    neighbors = [
        edge
        for edge in links
        if edge.get("source") in target_ids or edge.get("target") in target_ids
    ]
    return {
        "target": target_nodes,
        "neighbors": neighbors,
        "target_source": {
            "src/buggy_python/foobar.py": (
                ROOT / "src" / "buggy_python" / "foobar.py"
            ).read_text(encoding="utf-8")
        },
        "original_bug_context": json.loads(BUG_CONTEXT_PATH.read_text(encoding="utf-8")),
    }


def naive_context() -> dict[str, Any]:
    return {
        "source_files": read_text_files(ROOT / "src"),
        "tests": read_text_files(ROOT / "tests"),
        "original_bug_context": json.loads(BUG_CONTEXT_PATH.read_text(encoding="utf-8")),
    }


def evaluate_response(content: str) -> tuple[bool, bool]:
    lowered = content.lower()
    diagnosis_hits = sum(
        term in lowered
        for term in [
            "mutable default",
            "default argument",
            "shared",
            "same list",
            "function definition time",
        ]
    )
    diagnosis_success = diagnosis_hits >= 2
    fix_success = "bar=none" in lowered and (
        "is none" in lowered or "new list" in lowered or "fresh list" in lowered
    )
    return diagnosis_success, fix_success


def call_llm(
    client: Any,
    model: str,
    node: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> tuple[str, LlmCall]:
    print(f"Calling {node}: estimated prompt tokens={estimate_tokens(system_prompt + user_prompt)}", flush=True)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content or ""
    usage = response.usage
    prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
    completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
    total_tokens = getattr(usage, "total_tokens", None) if usage else None
    return content, LlmCall(
        node=node,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_prompt_tokens=estimate_tokens(system_prompt + "\n" + user_prompt),
        usage_source="api_usage" if total_tokens is not None else "estimated_prompt_only",
    )


def make_nodes(client: Any, model: str, max_tokens: int, skip_verifier: bool):
    def context_loader(state: WorkflowState) -> WorkflowState:
        if state["strategy"] == "naive":
            state["context"] = naive_context()
        else:
            state["context"] = graph_context(state.get("target", "foo()"))
        state["calls"] = []
        return state

    def investigator(state: WorkflowState) -> WorkflowState:
        system = "You are the bug investigator in a Python debugging agent workflow."
        instruction = (
            "Identify the root cause. Cite concrete evidence from the supplied context. "
            "Do not propose a broad refactor. Answer in at most 120 words."
        )
        user = json.dumps(
            {
                "strategy": state["strategy"],
                "question": state["question"],
                "instruction": instruction,
                "context": state["context"],
            },
            indent=2,
        )
        content, usage = call_llm(client, model, "bug_investigator", system, user, max_tokens)
        state["investigation"] = content
        state["calls"].append(asdict(usage))
        return state

    def fix_planner(state: WorkflowState) -> WorkflowState:
        system = "You are the fix planner in a Python debugging agent workflow."
        instruction = (
            "Using the investigation, provide the minimal patch plan and the regression "
            "test that proves the bug is fixed. Answer in at most 120 words."
        )
        user = json.dumps(
            {
                "strategy": state["strategy"],
                "question": state["question"],
                "instruction": instruction,
                "investigation": state["investigation"],
                "context": state["context"],
            },
            indent=2,
        )
        content, usage = call_llm(client, model, "fix_planner", system, user, max_tokens)
        state["plan"] = content
        state["calls"].append(asdict(usage))
        diagnosis_success, fix_success = evaluate_response(
            state["investigation"] + "\n" + state["plan"]
        )
        state["diagnosis_success"] = diagnosis_success
        state["fix_success"] = fix_success
        state["success"] = diagnosis_success and fix_success
        return state

    def verifier(state: WorkflowState) -> WorkflowState:
        if skip_verifier:
            state["verification"] = "Skipped by --skip-verifier"
            return state
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        state["verification"] = completed.stdout.strip() or completed.stderr.strip()
        return state

    return context_loader, investigator, fix_planner, verifier


def build_workflow(client: Any, model: str, max_tokens: int, skip_verifier: bool):
    context_loader, investigator, fix_planner, verifier = make_nodes(
        client, model, max_tokens, skip_verifier
    )
    graph = StateGraph(WorkflowState)
    graph.add_node("context_loader", context_loader)
    graph.add_node("bug_investigator", investigator)
    graph.add_node("fix_planner", fix_planner)
    graph.add_node("verifier", verifier)
    graph.set_entry_point("context_loader")
    graph.add_edge("context_loader", "bug_investigator")
    graph.add_edge("bug_investigator", "fix_planner")
    graph.add_edge("fix_planner", "verifier")
    graph.add_edge("verifier", END)
    return graph.compile()


def summarize_usage(result: dict[str, Any]) -> dict[str, Any]:
    calls = result.get("calls", [])
    total = sum(call.get("total_tokens") or call.get("estimated_prompt_tokens") or 0 for call in calls)
    prompt = sum(call.get("prompt_tokens") or call.get("estimated_prompt_tokens") or 0 for call in calls)
    completion = sum(call.get("completion_tokens") or 0 for call in calls)
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "calls": calls,
    }


def write_outputs(model: str, base_url: str | None, naive: dict[str, Any], graph: dict[str, Any]) -> None:
    naive_usage = summarize_usage(naive)
    graph_usage = summarize_usage(graph)
    comparison = {
        "basis": "sum_total_tokens_if_available_else_estimated_prompt_tokens",
        "naive_tokens": naive_usage["total_tokens"],
        "graph_guided_tokens": graph_usage["total_tokens"],
        "reduction": round(naive_usage["total_tokens"] / graph_usage["total_tokens"], 2)
        if graph_usage["total_tokens"]
        else None,
    }
    payload = {
        "model": model,
        "base_url": base_url,
        "naive_workflow": {
            "usage": naive_usage,
            "diagnosis_success": naive.get("diagnosis_success"),
            "fix_success": naive.get("fix_success"),
            "success": naive.get("success"),
            "verification": naive.get("verification"),
            "investigation_preview": naive.get("investigation", "")[:1200],
            "plan_preview": naive.get("plan", "")[:1200],
        },
        "graph_guided_workflow": {
            "usage": graph_usage,
            "diagnosis_success": graph.get("diagnosis_success"),
            "fix_success": graph.get("fix_success"),
            "success": graph.get("success"),
            "verification": graph.get("verification"),
            "investigation_preview": graph.get("investigation", "")[:1200],
            "plan_preview": graph.get("plan", "")[:1200],
        },
        "comparison": comparison,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown = f"""# Measured Agent Workflow Comparison

Model: `{model}`

Base URL: `{base_url or "default OpenAI"}`

| Workflow | Prompt tokens | Completion tokens | Total tokens | Diagnosis success | Fix success | Overall success |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Naive agent workflow | {naive_usage["prompt_tokens"]} | {naive_usage["completion_tokens"]} | {naive_usage["total_tokens"]} | {naive.get("diagnosis_success")} | {naive.get("fix_success")} | {naive.get("success")} |
| Graph-guided agent workflow | {graph_usage["prompt_tokens"]} | {graph_usage["completion_tokens"]} | {graph_usage["total_tokens"]} | {graph.get("diagnosis_success")} | {graph.get("fix_success")} | {graph.get("success")} |

Reduction basis: `{comparison["basis"]}`

Measured reduction: `{comparison["reduction"]}x`

## Naive Investigation Preview

```text
{naive.get("investigation", "")[:1200]}
```

## Graph-Guided Investigation Preview

```text
{graph.get("investigation", "")[:1200]}
```
"""
    OUTPUT_MD.write_text(markdown, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "qwen3:8b"))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL"))
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", "local-ai"))
    parser.add_argument("--target", default="foo()")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout per LLM call in seconds.")
    parser.add_argument("--max-tokens", type=int, default=350, help="Maximum completion tokens per LLM call.")
    parser.add_argument("--skip-verifier", action="store_true", help="Skip pytest inside each compared workflow.")
    args = parser.parse_args()

    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency: openai. Run `python -m pip install -r requirements.txt` first."
        ) from exc

    client = OpenAI(api_key=args.api_key, base_url=args.base_url, timeout=args.timeout)
    workflow = build_workflow(client, args.model, args.max_tokens, args.skip_verifier)
    question = "Why does foo() return a growing list on repeated calls, and what is the minimal fix?"
    print("Running naive agent workflow...", flush=True)
    naive = workflow.invoke({"strategy": "naive", "target": args.target, "question": question})
    print("Running Graphify-guided agent workflow...", flush=True)
    graph = workflow.invoke({"strategy": "graph_guided", "target": args.target, "question": question})
    write_outputs(args.model, args.base_url, naive, graph)
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
