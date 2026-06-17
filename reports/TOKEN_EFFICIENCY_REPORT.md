# Token Efficiency Report

## Question

How much context is needed to identify and fix the selected `foo()` bug?

## Measurement Method

The final comparison uses one measured method only:

- Model: `gemma4:e2b`
- Runtime: Ollama OpenAI-compatible endpoint
- Runs: 10
- Naive prompt: full `src/`, tests, and original bug context
- Graph-guided prompt: `foo()` graph neighborhood, target source, and original
  bug context
- Success criteria: correct mutable-default diagnosis and `bar=None` fix

## Results

| Workflow | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | 2061.0 | 1315.4 | 3376.4 | 1.0 |
| Graphify-guided | 851.0 | 578.5 | 1429.5 | 0.9 |

Average total-token reduction: `2.36x`.

## Interpretation

The graph-guided prompt used less than half the average total tokens of the
naive prompt while still solving the bug in 9 of 10 runs. The naive prompt solved
the bug in all 10 runs but paid for substantially more context.

The complete measured output is in:

- `reports/MEASURED_TOKEN_COMPARISON.md`
- `data/measured-token-comparison.json`

To reproduce:

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key ollama --model gemma4:e2b --runs 10
```
