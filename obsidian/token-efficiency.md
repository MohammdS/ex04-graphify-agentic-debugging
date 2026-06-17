# Token Efficiency

The final token comparison uses the measured local-model report only:
`reports/MEASURED_TOKEN_COMPARISON.md`.

Measured with `gemma4:e2b` through Ollama over 10 runs.

| Workflow | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | 1914.0 | 790.0 | 2704.0 | 0.9 |
| Graphify-guided | 683.0 | 558.2 | 1241.2 | 1.0 |

Average total-token reduction: `2.18x`.

The naive prompt sends the whole source and tests. The graph-guided prompt sends
the `foo()` graph neighborhood and the broken target file.

Reproduction command:

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key ollama --model gemma4:e2b --runs 10
```
