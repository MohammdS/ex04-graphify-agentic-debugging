# EX04: Graph-Guided Agentic Debugging

This repository is a complete EX04 submission. It reverse engineers a small
unfamiliar Python debugging codebase, generates Graphify artifacts, documents
the architecture in an Obsidian-style vault, fixes one bug, and compares token
usage between naive and graph-guided workflows.

## Selected Repository

Source: `andela/buggy-python`

I selected this repository because it is intentionally small, Python-only, and
contains classic debugging exercises. That keeps the assignment focused on
reverse engineering, graph navigation, root-cause analysis, and measurable
agent workflow design instead of dependency setup.

## Repository Layout

```text
README.md
requirements.txt
pyproject.toml
src/buggy_python/
tests/
agent/
obsidian/
reports/
artifacts/
data/
```

## Bug Fixed

The selected bug is the mutable default argument in `foo()`.

Original broken behavior:

```python
def foo(bar=[]):
    bar.append("baz")
    return bar
```

Because Python evaluates default arguments once, repeated calls reused the same
list. The fix uses `None` as a sentinel:

```python
def foo(bar=None):
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```

## Graphify Outputs

Graphify was run against `src/`:

```powershell
python -m graphify extract src --out . --no-cluster
python -m graphify cluster-only . --graph graphify-out\graph.json --no-label --no-viz
```

Important graph artifacts:

- `data/graph.json`
- `obsidian/index.md`
- `obsidian/hot.md`
- `reports/GRAPH_REPORT.md`

Graph summary:

- 19 nodes
- 31 edges
- 4 communities
- No import cycles

## Agentic Workflow

The graph-guided debugging workflow is implemented with LangGraph in
`agent/workflow.py`.

Workflow stages:

1. `graph_reader` loads `data/graph.json` and extracts the `foo()` neighborhood.
2. `bug_investigator` loads `agent/prompts/bug_investigator.md` and asks an LLM
   to identify the root cause from graph-bounded context.
3. `fix_planner` loads `agent/prompts/fix_planner.md` and asks an LLM for a
   minimal patch and regression-test plan.
4. `verifier` runs `python -m pytest -q`.

Set `OPENAI_API_KEY` to run the investigation and planning steps with an LLM.
`OPENAI_MODEL` is optional. If no API key is present, the workflow marks
`llm_used: false` and uses a local fallback so the repo can still be verified.

## Token Efficiency

The committed token-efficiency evidence is the measured local-model trial in
`reports/MEASURED_TOKEN_COMPARISON.md` and
`data/measured-token-comparison.json`.

Measured with local model `gemma4:e2b` through Ollama over 10 runs:

| Workflow | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | 2061.0 | 1315.4 | 3376.4 | 1.0 |
| Graphify-guided | 851.0 | 578.5 | 1429.5 | 0.9 |

Average total-token reduction: `2.36x`.

To reproduce the measured comparison:

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key ollama --model gemma4:e2b --runs 10
```

The LLM prompts include `data/original-bug-context.json`, which preserves the
pre-fix broken `foo(bar=[])` snippet for honest before/after investigation.

## Diagrams and Vault

The Obsidian vault is under `obsidian/` and starts at `obsidian/index.md`.

Diagram artifacts:

- `artifacts/architecture-diagram.mmd`
- `artifacts/oop-diagram.mmd`
- `artifacts/investigation-flow.mmd`

## Run It

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run tests:

```powershell
python -m pytest -q
```

Run the LangGraph workflow:

```powershell
python agent\workflow.py
```

Run it with an LLM:

```powershell
$env:OPENAI_API_KEY = "your_api_key"
$env:OPENAI_MODEL = "your_model_name"
python agent\workflow.py
```

Expected verification:

```text
3 passed
```
