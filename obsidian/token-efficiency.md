# Token Efficiency

The token comparison is measured on two models and kept side by side:
`reports/MEASURED_TOKEN_COMPARISON.md`.

Metrics (hw1 §5.5): tokens consumed, files/units read, investigation rounds, and
success rate.

| Model | Workflow | Avg prompt tokens | Avg completion tokens | Avg total tokens | Files read | Rounds | Success rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gemma3:4b` (local, 10 runs) | Naive full-context | 1914.0 | 790.0 | 2704.0 | 6 | 1 | 0.9 |
| `gemma3:4b` (local, 10 runs) | Graphify-guided | 683.0 | 558.2 | 1241.2 | 1 | 1 | 1.0 |
| `glm-4.7-flashx` (z.ai, 10 runs) | Naive full-context | 1672.0 | 1024.3 | 2696.3 | 6 | 1 | 1.0 |
| `glm-4.7-flashx` (z.ai, 10 runs) | Graphify-guided | 554.0 | 788.3 | 1342.3 | 1 | 1 | 0.9 |

Average total-token reduction: `gemma3:4b` **2.18x**, `glm-4.7-flashx` **2.01x**.

The naive prompt sends the whole source and tests. The graph-guided prompt sends
only the `foo()` graph neighborhood and the preserved broken target file, so the
model still sees the bug even though `src/buggy_python/foobar.py` is now fixed.

Reproduction commands:

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key ollama --model gemma3:4b --runs 10
python agent\compare_token_usage.py --base-url https://api.z.ai/api/paas/v4/ --model glm-4.7-flashx --runs 10
```

See [[before-after]] for the actual code fix and [[agent-workflow]] for the
LLM-driven debugging graph.
