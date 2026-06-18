# Architecture Report

## System Overview

The submission extracts a small Python package from `andela/buggy-python` and
turns it into a testable project. The package has three modules:

- `foobar.py`: default-argument behavior and selected preserved bug.
- `io.py`: loan JSON loading and aggregate calculations.
- `loop.py`: lambda factory behavior.

`__init__.py` re-exports the public functions so tests and users can import from
`buggy_python` directly.

## Data Flow

1. `read_file()` loads `loans.json`.
2. `_amounts_by_status()` filters records by `status`.
3. Aggregate functions sum or average filtered amounts.
4. Tests verify the public outputs.

## Bug Impact Boundary

The graph shows `foo()` is contained in `foobar.py` and imported by
`__init__.py`. It does not affect loan calculations or lambda generation. That
allows a narrow suggested patch and a focused regression test.

## Diagrams

- Block diagram: `artifacts/architecture-diagram.mmd`
- Class/module diagram: `artifacts/oop-diagram.mmd`
- Investigation flow: `artifacts/investigation-flow.mmd`

## Extension: Suspect Ranking

`agent/rank_suspects.py` ranks graph nodes by degree centrality plus proximity to
a seed node, so the agent inspects the most likely bug locations first. Output is
`reports/SUSPECT_RANKING.md`.
