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

| Workflow | Estimated tokens | Reduction vs naive |
| --- | ---: | ---: |
| Naive full source read | 1,266 | 1.0x |
| Graphify average query | 583 | 2.2x |
| Targeted graph-guided LLM agent | 230 | 5.50x |

Details are in `reports/TOKEN_EFFICIENCY_REPORT.md` and
`data/token-comparison.json`.

The LLM workflow also reads `data/original-bug-context.json`, which preserves the
pre-fix broken `foo(bar=[])` snippet for honest before/after investigation.

To measure real token usage on a local model, run:

```powershell
.\scripts\run_local_comparison.ps1 -Model qwen3:8b
```

For a 10-run average:

```powershell
.\scripts\run_local_comparison.ps1 -Model qwen3:8b -Runs 10
```

Or call the Python script directly:

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key local-ai --model llama3.1
```

This writes `data/measured-token-comparison.json` and
`reports/MEASURED_TOKEN_COMPARISON.md`. Setup notes are in
`reports/LOCAL_AI_TOKEN_MEASUREMENT.md`. The measured report records token usage
and whether each response found the correct root cause and `bar=None` fix.

For a stronger workflow-level comparison, run two LangGraph workflows against
the same local model:

```powershell
python agent\compare_agent_workflows.py --base-url http://localhost:11434/v1 --api-key ollama --model qwen3:8b
```

This writes `data/measured-agent-workflow-comparison.json` and
`reports/MEASURED_AGENT_WORKFLOW_COMPARISON.md`.

For slower local models, use:

```powershell
.\scripts\run_local_comparison.ps1 -Mode workflow -Model qwen3:8b -MaxTokens 120 -Timeout 120 -SkipVerifier
```

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
