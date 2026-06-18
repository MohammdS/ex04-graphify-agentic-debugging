# Research Questions

The five research questions from the assignment (hw1 §4), answered against the
graph and the investigation evidence in this vault.

## 1. What is the real architecture, and what wasn't obvious at first glance?

The `buggy_python` package reads like a flat bag of scripts, but the Graphify
graph splits it into three concerns: `foobar.py` (the `foo()` mutable-default
bug), `io.py` + `loans.json` (file I/O via `read_file()`), and `loop.py`. The
graph is 19 nodes, 31 edges, 4 communities, no import cycles. The non-obvious
part was that the `loans.json` data file clusters with `io.py` rather than being
inert. See [[hot]] and [[architecture]].

## 2. Which components are the most central (God Nodes)?

The suspect-ranking extension ranks: `foo()` (1.167), `__init__.py` (1.000),
`io.py` (0.722), `foobar.py` (0.667), `read_file()` (0.611). `__init__.py` is the
structural hub by degree; `foo()` leads once proximity to the bug seed is added.
See `reports/SUSPECT_RANKING.md`.

## 3. How were the block and OOP schemas extracted?

Both schemas are derived from the Graphify communities and edges, not a folder
listing: the architecture block diagram (`artifacts/architecture-diagram.mmd`)
for module-to-module flow, and the OOP/relationship diagram
(`artifacts/oop-diagram.mmd`). See [[architecture]] and [[oop]].

## 4. How was the bug found, what was the root cause, what steps led there?

The agent's `graph_reader` started from [[hot]] and the `foo()` neighborhood
instead of reading files linearly, surfacing `def foo(bar=[])`. Root cause: a
mutable default argument evaluated once at definition time, so repeated implicit
calls share one list. Fix: the `None`-sentinel form (`bar=None` then
`if bar is None: bar = []`). See [[bug-investigation]] and [[before-after]].

## 5. Graph-guided advantage, token savings, and extensions?

Graph-guidance let the agent read **1 file** (`foobar.py`) plus the `foo()`
neighborhood instead of all **6** source/test files, cutting total tokens
**2.18x** (gemma3:4b) and **2.01x** (glm-4.7-flashx) at comparable success.
The original extension is the centrality + proximity suspect ranking. See
[[token-efficiency]] and [[agent-workflow]].
