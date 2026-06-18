# Measured Token Comparison

This report compares naive full-context prompting against Graphify-guided
prompting, measured on **two** OpenAI-compatible models so the result is not tied
to a single backend. Both models are kept side by side; neither overwrites the
other.

In both runs the model is given the **preserved buggy `foo()` source** (from
`data/original-bug-context.json`) so it always has a real bug to diagnose, even
though the live source has since been fixed.

## Side-by-Side Averages

| Model | Backend | Runs | Workflow | Avg prompt | Avg completion | Avg total | Success |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| `gemma3:4b` | Ollama (local) | 10 | Naive full-context | 1914.0 | 790.0 | 2704.0 | 0.9 |
| `gemma3:4b` | Ollama (local) | 10 | Graphify-guided | 683.0 | 558.2 | 1241.2 | 1.0 |
| `glm-4.7-flashx` | z.ai (cloud) | 10 | Naive full-context | 1672.0 | 987.9 | 2659.9 | 1.0 |
| `glm-4.7-flashx` | z.ai (cloud) | 10 | Graphify-guided | 554.0 | 826.8 | 1380.8 | 1.0 |

| Model | Avg total-token reduction (naive / graph) |
| --- | ---: |
| `gemma3:4b` | 2.18x |
| `glm-4.7-flashx` | 1.93x |

Both models show the same direction: the graph-guided prompt uses far fewer
prompt tokens (gemma3:4b 683 vs 1914; glm-4.7-flashx 554 vs 1672) and reaches the
correct diagnosis and fix at an equal or higher success rate, while sending only
the `foo()` graph neighborhood plus the target source instead of the whole tree.
Across the 10 GLM iterations the prompt-token counts are perfectly flat (naive
1672, graph 554) because the prompts are fixed; only completion length varies.

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
