# Token Efficiency

The final token comparison uses the measured local-model report only:
`reports/MEASURED_TOKEN_COMPARISON.md`.

Measured with `gemma4:e2b` through Ollama over 10 runs.

| Workflow | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | 2061.0 | 1315.4 | 3376.4 | 1.0 |
| Graphify-guided | 851.0 | 578.5 | 1429.5 | 0.9 |

Average total-token reduction: `2.36x`.

The naive prompt sends the whole source and tests. The graph-guided prompt sends
the `foo()` graph neighborhood, target file, and preserved original bug snippet.

Reproduction command:

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key ollama --model gemma4:e2b --runs 10
```
