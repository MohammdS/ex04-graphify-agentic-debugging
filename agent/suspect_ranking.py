"""Graph loading and suspect scoring for the suspect-ranking extension (§5.6).

A node is a strong place for an agent to start investigating a bug when it is
BOTH highly connected (high degree centrality -> wide blast radius) and close to
a known seed of interest (short BFS distance). These two signals are combined
into a single suspect score.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path


def load_graph(path: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Load the node-link graph and return (id -> label, undirected adjacency)."""
    data = json.loads(path.read_text(encoding="utf-8"))

    id_to_label: dict[str, str] = {}
    for node in data["nodes"]:
        id_to_label[node["id"]] = node["label"]

    adjacency: dict[str, set[str]] = defaultdict(set)
    for link in data["links"]:
        source = link["source"]
        target = link["target"]
        # Treat every edge as undirected (add both directions).
        adjacency[source].add(target)
        adjacency[target].add(source)

    # Ensure isolated nodes still appear with an empty neighbour set.
    for node_id in id_to_label:
        adjacency.setdefault(node_id, set())

    # Convert sets to sorted lists for deterministic output.
    adjacency_list = {node_id: sorted(neighbours) for node_id, neighbours in adjacency.items()}
    return id_to_label, adjacency_list


def bfs_distances(adjacency: dict[str, list[str]], start: str) -> dict[str, int]:
    """Return BFS shortest-path distances (in hops) from ``start`` to every node."""
    distances: dict[str, int] = {start: 0}
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        for neighbour in adjacency[current]:
            if neighbour not in distances:
                distances[neighbour] = distances[current] + 1
                queue.append(neighbour)
    return distances


def find_seed_id(seed_label: str, id_to_label: dict[str, str]) -> str | None:
    """Return the node id whose label matches ``seed_label`` (first match)."""
    for node_id, label in id_to_label.items():
        if label == seed_label:
            return node_id
    return None


def rank_suspects(
    id_to_label: dict[str, str],
    adjacency: dict[str, list[str]],
    seed_id: str,
) -> list[dict[str, object]]:
    """Compute degree centrality, proximity and suspect score for every node."""
    n_nodes = len(id_to_label)
    denom = n_nodes - 1 if n_nodes > 1 else 1
    distances = bfs_distances(adjacency, seed_id)

    rows: list[dict[str, object]] = []
    for node_id, label in id_to_label.items():
        degree = len(adjacency[node_id])
        degree_centrality = degree / denom
        distance = distances.get(node_id)  # None means unreachable.

        if distance is None:
            proximity = 0.0  # 1 / (1 + inf) -> 0
        else:
            proximity = 1.0 / (1.0 + distance)

        score = degree_centrality + proximity
        rows.append(
            {
                "label": label,
                "degree": degree,
                "degree_centrality": degree_centrality,
                "distance": distance,
                "score": score,
            }
        )

    # Rank by score descending; tie-break by degree then label for stability.
    rows.sort(
        key=lambda r: (-r["score"], -r["degree"], r["label"]),
    )
    return rows
