"""Measure naive vs Graphify-guided LLM token usage.

This script sends two prompts to an OpenAI-compatible local or remote model:

1. Naive: full project source context.
2. Graph-guided: Graphify target node neighborhood plus target source.

It writes machine-readable JSON and a Markdown summary that can be used as
assignment evidence. Prompt construction lives in ``token_prompts.py``, scoring
in ``token_scoring.py``, and output writing in ``token_report.py``.
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from token_prompts import build_graph_prompt, build_naive_prompt, estimate_tokens
from token_report import write_outputs
from token_scoring import RunResult, evaluate_response


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
