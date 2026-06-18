# Measured Token Comparison

This report compares naive full-context prompting against Graphify-guided
prompting, measured on **two** OpenAI-compatible models so the result is not tied
to a single backend. Both models are kept side by side; neither overwrites the
other.

In both runs the model is given the **preserved buggy `foo()` source** (from
`data/original-bug-context.json`) so it always has a real bug to diagnose, even
though the live source has since been fixed.

## Side-by-Side Averages

The four §5.5 metrics are reported: tokens consumed, files/textual units read,
investigation rounds, and quality (success rate) of reaching the root cause and
fix.

| Model | Backend | Runs | Workflow | Avg prompt | Avg completion | Avg total | Files read | Rounds | Success |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gemma3:4b` | Ollama (local) | 10 | Naive full-context | 1914.0 | 790.0 | 2704.0 | 6 | 1 | 0.9 |
| `gemma3:4b` | Ollama (local) | 10 | Graphify-guided | 683.0 | 558.2 | 1241.2 | 1 | 1 | 1.0 |
| `glm-4.7-flashx` | z.ai (cloud) | 10 | Naive full-context | 1672.0 | 1024.3 | 2696.3 | 6 | 1 | 1.0 |
| `glm-4.7-flashx` | z.ai (cloud) | 10 | Graphify-guided | 554.0 | 788.3 | 1342.3 | 1 | 1 | 0.9 |

Files read: the naive run reads 6 files (`src/buggy_python/{__init__.py,
foobar.py, io.py, loans.json, loop.py}` + `tests/test_buggy_python.py`); the
graph-guided run reads 1 file (`foobar.py`) plus the `foo()` graph neighborhood
(1 target node, 3 edges). Both modes reach the diagnosis in a single
investigation round.

| Model | Avg total-token reduction (naive / graph) |
| --- | ---: |
| `gemma3:4b` | 2.18x |
| `glm-4.7-flashx` | 2.01x |

Both models show the same direction: the graph-guided prompt uses far fewer
prompt tokens (gemma3:4b 683 vs 1914; glm-4.7-flashx 554 vs 1672) and reaches the
correct diagnosis and fix at a comparable success rate, while sending only the
`foo()` graph neighborhood plus the target source instead of the whole tree.
gemma3:4b improves (0.9 → 1.0); on this GLM run graph-guided scored 0.9 vs naive
1.0 because one of the ten graph responses missed the strict diagnosis/fix
keyword heuristic (the model still found the bug) — ordinary LLM variance, not a
context-coverage failure. Across the 10 GLM iterations the prompt-token counts
are perfectly flat (naive 1672, graph 554) because the prompts are fixed; only
completion length varies.

## Raw Evidence

- `data/measured-token-comparison-gemma3-4b.json` (10 runs, local Ollama)
- `data/measured-token-comparison-glm-4-7-flashx.json` (10 runs, z.ai)
- `reports/MEASURED_TOKEN_COMPARISON_glm-4-7-flashx.md` (auto-generated GLM detail)
- `data/measured-token-comparison.json` (canonical copy of the gemma3:4b run)

## Reproduce

Local model (Ollama):

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key ollama --model gemma3:4b --runs 10
```

Cloud model (z.ai GLM, credentials via `.env` / environment, never committed):

```powershell
python agent\compare_token_usage.py --base-url https://api.z.ai/api/paas/v4/ --model glm-4.7-flashx --runs 10
```
