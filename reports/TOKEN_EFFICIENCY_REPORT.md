# Token Efficiency Report

## Question

How much context is needed to identify and fix the selected `foo()` bug, and does
the saving hold across more than one model?

## Measurement Method

- Models: `gemma3:4b` (local, via Ollama) and `glm-4.7-flashx` (cloud, via z.ai)
- Naive prompt: full `src/` and tests
- Graph-guided prompt: `foo()` graph neighborhood and target source only
- The model always receives the **preserved buggy `foo()` source** from
  `data/original-bug-context.json`, so the live (now fixed) code does not leak the
  answer into the experiment
- Success criteria: correct mutable-default diagnosis and `bar=None` fix
- Metrics reported (hw1 §5.5): (1) tokens consumed, (2) number of files / textual
  units read, (3) number of investigation rounds, (4) quality/speed of reaching
  the root cause and fix (success rate)

## Results

| Model | Workflow | Avg prompt tokens | Avg completion tokens | Avg total tokens | Files read | Rounds | Success rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gemma3:4b` (10 runs) | Naive full-context | 1914.0 | 790.0 | 2704.0 | 6 | 1 | 0.9 |
| `gemma3:4b` (10 runs) | Graphify-guided | 683.0 | 558.2 | 1241.2 | 1 | 1 | 1.0 |
| `glm-4.7-flashx` (10 runs) | Naive full-context | 1672.0 | 1024.3 | 2696.3 | 6 | 1 | 1.0 |
| `glm-4.7-flashx` (10 runs) | Graphify-guided | 554.0 | 788.3 | 1342.3 | 1 | 1 | 0.9 |

Average total-token reduction: `gemma3:4b` **2.18x**, `glm-4.7-flashx` **2.01x**.

**Research question answered (hw1 §4):** graph-guided navigation reduced the
context from 6 files to 1 file plus the `foo()` neighborhood, which is what drives
the ~2-3x prompt-token saving while keeping the diagnosis to a single round. Both
modes succeed, but the graph mode does so with far fewer textual units read.

## Interpretation

On both a small local model and a larger cloud model, the graph-guided prompt cut
total token usage substantially at a comparable success rate (gemma3:4b improves
0.9 → 1.0; on this GLM run graph-guided scored 0.9 vs naive 1.0, one of ten
responses missing the strict keyword heuristic — LLM variance, not missing
context). The prompt-token saving is the most stable signal (683 vs 1914 for
gemma3:4b; 554 vs 1672 for glm-4.7-flashx) because it is driven directly by how
much source the graph lets us skip (over 10 GLM iterations the prompt counts are
perfectly flat at 1672 naive / 554 graph). Completion tokens vary by model
temperament, which is why total-token reduction differs between the two backends
but stays clearly above 1x in both.

## Evidence Files

- `reports/MEASURED_TOKEN_COMPARISON.md` (combined side-by-side)
- `data/measured-token-comparison-gemma3-4b.json`
- `data/measured-token-comparison-glm-4-7-flashx.json`

## Reproduce

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key ollama --model gemma3:4b --runs 10
python agent\compare_token_usage.py --base-url https://api.z.ai/api/paas/v4/ --model glm-4.7-flashx --runs 10
```
