# Token Efficiency Report

## Question

How much context is needed to identify and fix the selected `foo()` bug?

## Measurement Method

The final comparison uses one measured method only:

- Model: `gemma4:e2b`
- Runtime: Ollama OpenAI-compatible endpoint
- Runs: 10
- Naive prompt: full `src/` and tests
- Graph-guided prompt: `foo()` graph neighborhood and target source
- Success criteria: correct mutable-default diagnosis and `bar=None` fix

## Results

| Workflow | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | 1914.0 | 790.0 | 2704.0 | 0.9 |
| Graphify-guided | 683.0 | 558.2 | 1241.2 | 1.0 |

Average total-token reduction: `2.18x`.

## Interpretation

The graph-guided prompt used less than half the average total tokens of the
naive prompt while solving the bug in all 10 runs. The naive prompt solved the
bug in 9 of 10 runs and paid for substantially more context.

The complete measured output is in:

- `reports/MEASURED_TOKEN_COMPARISON.md`
- `data/measured-token-comparison.json`

To reproduce:

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key ollama --model gemma4:e2b --runs 10
```
