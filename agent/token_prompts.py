"""Prompt construction for the naive-vs-graph token comparison.

Builds the two prompts that are sent to the model: a naive prompt with the full
project source, and a graph-guided prompt with only the target node's graph
neighborhood plus the target source. Both substitute the preserved buggy
``foobar.py`` so the model always has a real bug to diagnose.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "graph.json"
BUG_CONTEXT_PATH = ROOT / "data" / "original-bug-context.json"


def buggy_foobar_source() -> str:
    """Return the preserved original buggy foobar.py source for the experiment."""
    data = json.loads(BUG_CONTEXT_PATH.read_text(encoding="utf-8"))
    return data["original_source"]


def estimate_tokens(text: str) -> int:
    """Simple fallback estimate when a local server omits usage accounting."""
    return max(1, round(len(text.split()) * 1.33))


def slug(model: str) -> str:
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
