"""Rank bug suspects by graph centrality and proximity to a seed node.

This extension (assignment §5.6) consumes the node-link knowledge graph in
``data/graph.json`` and produces a ranked list of "suspect" nodes for a
graph-guided debugging workflow, telling the agent which nodes to inspect first
instead of reading files in arbitrary order. The ranked report is written to
``reports/SUSPECT_RANKING.md``.

Scoring lives in ``suspect_ranking.py`` and rendering in ``suspect_report.py``.
Pure standard library, fully local, no network access.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from suspect_ranking import find_seed_id, load_graph, rank_suspects
from suspect_report import build_markdown

ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "graph.json"
OUTPUT_MD = ROOT / "reports" / "SUSPECT_RANKING.md"

DEFAULT_SEED = "foo()"
DEFAULT_TOP = 10


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Rank graph nodes as bug suspects by degree centrality and "
            "proximity to a seed node, and write a Markdown report."
        )
    )
    parser.add_argument(
        "--seed",
        default=DEFAULT_SEED,
        help=f'Label of the seed node (default: "{DEFAULT_SEED}").',
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP,
        help=f"Number of top suspects to show (default: {DEFAULT_TOP}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point: rank suspects and write the Markdown report."""
    args = parse_args(argv)

    id_to_label, adjacency = load_graph(GRAPH_PATH)

    seed_id = find_seed_id(args.seed, id_to_label)
    if seed_id is None:
        available = "\n".join(f"  - {label}" for label in sorted(set(id_to_label.values())))
        print(
            f'Seed label "{args.seed}" not found in graph.\n'
            f"Available labels:\n{available}"
        )
        return 1

    rows = rank_suspects(id_to_label, adjacency, seed_id)
    markdown = build_markdown(rows, args.seed, args.top)

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(markdown, encoding="utf-8")
    print(f"Wrote suspect ranking for seed '{args.seed}' to {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
