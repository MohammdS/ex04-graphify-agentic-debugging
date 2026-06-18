"""Write the JSON dataset and Markdown summary for the token comparison."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from token_prompts import slug
from token_scoring import RunResult, average, success_rate


ROOT = Path(__file__).resolve().parents[1]


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
    out_json = ROOT / "data" / f"measured-token-comparison-{slug(model)}.json"
    out_md = ROOT / "reports" / f"MEASURED_TOKEN_COMPARISON_{slug(model)}.md"
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    naive_avg = payload["averages"]["naive"]
    graph_avg = payload["averages"]["graph_guided"]
    markdown = f"""# Measured Token Comparison

Model: `{model}`

Base URL: `{base_url or "default OpenAI"}`

Runs: `{len(naive_results)}`

## Average Results

| Run | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | {naive_avg["prompt_tokens"]} | {naive_avg["completion_tokens"]} | {naive_avg["total_tokens"]} | {naive_avg["success_rate"]} |
| Graph-guided | {graph_avg["prompt_tokens"]} | {graph_avg["completion_tokens"]} | {graph_avg["total_tokens"]} | {graph_avg["success_rate"]} |

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
