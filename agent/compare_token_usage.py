"""Measure naive vs Graphify-guided LLM token usage.

This script sends two prompts to an OpenAI-compatible local or remote model:

1. Naive: full project source context.
2. Graph-guided: Graphify target node neighborhood plus target source.

It writes machine-readable JSON and a Markdown summary that can be used as
assignment evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "graph.json"
BUG_CONTEXT_PATH = ROOT / "data" / "original-bug-context.json"
OUTPUT_JSON = ROOT / "data" / "measured-token-comparison.json"
OUTPUT_MD = ROOT / "reports" / "MEASURED_TOKEN_COMPARISON.md"


def buggy_foobar_source() -> str:
    """Return the preserved original buggy foobar.py source for the experiment."""
    data = json.loads(BUG_CONTEXT_PATH.read_text(encoding="utf-8"))
    return data["original_source"]


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


def estimate_tokens(text: str) -> int:
    """Simple fallback estimate when a local server omits usage accounting."""

    return max(1, round(len(text.split()) * 1.33))


def _slug(model: str) -> str:
    """Turn a model name into a filesystem-safe slug for output filenames."""
    return re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")


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
    }


def build_naive_prompt(question: str) -> str:
    source_files = read_text_files(ROOT / "src")
    foobar_key = next(
        (key for key in source_files if key.endswith("foobar.py")),
        "src/buggy_python/foobar.py",
    )
    source_files[foobar_key] = buggy_foobar_source()
    return json.dumps(
        {
            "task": question,
            "instruction": (
                "Reverse engineer the project from the supplied full source, "
                "identify the bug, explain the root cause, and suggest a minimal fix. "
                "Do not modify files; return only the diagnosis and proposed patch."
            ),
            "source_files": source_files,
            "tests": read_text_files(ROOT / "tests"),
        },
        indent=2,
    )


def build_graph_prompt(question: str, target_label: str) -> str:
    return json.dumps(
        {
            "task": question,
            "instruction": (
                "Use the graph context first. Inspect only the target source "
                "needed by the graph neighborhood, then identify root cause and "
                "suggest a minimal fix. Do not modify files; return only the "
                "diagnosis and proposed patch."
            ),
            "graph_context": graph_context(target_label),
            "target_source": {
                "src/buggy_python/foobar.py": buggy_foobar_source()
            },
        },
        indent=2,
    )


def call_model(client: Any, model: str, name: str, prompt: str, iteration: int) -> RunResult:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a concise senior Python debugging agent.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or ""
    usage = response.usage
    prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
    completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
    total_tokens = getattr(usage, "total_tokens", None) if usage else None
    diagnosis_success, fix_success, criteria = evaluate_response(content)
    return RunResult(
        iteration=iteration,
        name=name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_prompt_tokens=estimate_tokens(prompt),
        diagnosis_success=diagnosis_success,
        fix_success=fix_success,
        success=diagnosis_success and fix_success,
        success_criteria=criteria,
        response_preview=content[:1200],
        usage_source="api_usage" if total_tokens is not None else "estimated_prompt_only",
    )


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


def write_outputs(
    results: list[RunResult], model: str, base_url: str | None
) -> tuple[Path, Path]:
    naive_results = [result for result in results if result.name == "naive_full_context"]
    graph_results = [result for result in results if result.name == "graph_guided"]
    latest_naive = naive_results[-1]
    latest_graph = graph_results[-1]
    naive_basis_avg = average([
        result.total_tokens or result.estimated_prompt_tokens
        for result in naive_results
    ])
    graph_basis_avg = average([
        result.total_tokens or result.estimated_prompt_tokens
        for result in graph_results
    ])
    payload = {
        "model": model,
        "base_url": base_url,
        "results": [asdict(result) for result in results],
        "averages": {
            "runs": len(naive_results),
            "basis": "average_total_tokens_if_available_else_estimated_prompt_tokens",
            "naive": {
                "prompt_tokens": average([result.prompt_tokens for result in naive_results]),
                "completion_tokens": average([result.completion_tokens for result in naive_results]),
                "total_tokens": average([result.total_tokens for result in naive_results]),
                "basis_tokens": naive_basis_avg,
                "success_rate": success_rate(naive_results),
            },
            "graph_guided": {
                "prompt_tokens": average([result.prompt_tokens for result in graph_results]),
                "completion_tokens": average([result.completion_tokens for result in graph_results]),
                "total_tokens": average([result.total_tokens for result in graph_results]),
                "basis_tokens": graph_basis_avg,
                "success_rate": success_rate(graph_results),
            },
            "reduction": round(naive_basis_avg / graph_basis_avg, 2)
            if naive_basis_avg and graph_basis_avg
            else None,
        },
    }
    out_json = ROOT / "data" / f"measured-token-comparison-{_slug(model)}.json"
    out_md = ROOT / "reports" / f"MEASURED_TOKEN_COMPARISON_{_slug(model)}.md"
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    markdown = f"""# Measured Token Comparison

Model: `{model}`

Base URL: `{base_url or "default OpenAI"}`

Runs: `{len(naive_results)}`

## Average Results

| Run | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | {payload["averages"]["naive"]["prompt_tokens"]} | {payload["averages"]["naive"]["completion_tokens"]} | {payload["averages"]["naive"]["total_tokens"]} | {payload["averages"]["naive"]["success_rate"]} |
| Graph-guided | {payload["averages"]["graph_guided"]["prompt_tokens"]} | {payload["averages"]["graph_guided"]["completion_tokens"]} | {payload["averages"]["graph_guided"]["total_tokens"]} | {payload["averages"]["graph_guided"]["success_rate"]} |

Average reduction: `{payload["averages"]["reduction"]}x`

## Latest Run

| Run | Prompt tokens | Completion tokens | Total tokens | Estimated prompt tokens | Usage source |
| --- | ---: | ---: | ---: | ---: | --- |
| Naive full-context | {latest_naive.prompt_tokens} | {latest_naive.completion_tokens} | {latest_naive.total_tokens} | {latest_naive.estimated_prompt_tokens} | {latest_naive.usage_source} |
| Graph-guided | {latest_graph.prompt_tokens} | {latest_graph.completion_tokens} | {latest_graph.total_tokens} | {latest_graph.estimated_prompt_tokens} | {latest_graph.usage_source} |

| Run | Diagnosis success | Fix success | Overall success |
| --- | --- | --- | --- |
| Naive full-context | {latest_naive.diagnosis_success} | {latest_naive.fix_success} | {latest_naive.success} |
| Graph-guided | {latest_graph.diagnosis_success} | {latest_graph.fix_success} | {latest_graph.success} |

## Naive Response Preview

```text
{latest_naive.response_preview}
```

## Graph-Guided Response Preview

```text
{latest_graph.response_preview}
```
"""
    out_md.write_text(markdown, encoding="utf-8")
    return out_json, out_md


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", "llama3.1"),
        help="Model name served by the local OpenAI-compatible endpoint.",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL"),
        help="OpenAI-compatible base URL, e.g. http://localhost:11434/v1.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY", "local-ai"),
        help="API key. Local servers often accept any non-empty value.",
    )
    parser.add_argument(
        "--target",
        default="foo()",
        help="Graph node label to use for the graph-guided run.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of repeated naive-vs-graph trials to run.",
    )
    args = parser.parse_args()

    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency: openai. Run `python -m pip install -r requirements.txt` first."
        ) from exc

    question = "Why does foo() return a growing list on repeated calls, and what fix should be suggested?"
    client = OpenAI(api_key=args.api_key, base_url=args.base_url)
    results = []
    for iteration in range(1, args.runs + 1):
        print(f"Run {iteration}/{args.runs}: naive_full_context", flush=True)
        results.append(
            call_model(
                client,
                args.model,
                "naive_full_context",
                build_naive_prompt(question),
                iteration,
            )
        )
        print(f"Run {iteration}/{args.runs}: graph_guided", flush=True)
        results.append(
            call_model(
                client,
                args.model,
                "graph_guided",
                build_graph_prompt(question, args.target),
                iteration,
            )
        )
    out_json, out_md = write_outputs(results, args.model, args.base_url)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
