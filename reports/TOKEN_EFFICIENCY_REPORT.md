# Token Efficiency Report

## Question

How much context is needed to identify and fix the selected `foo()` bug?

## Measurement Method

- Naive workflow: read every file under `src/` before deciding where the bug is.
- Graphify benchmark: use `python -m graphify benchmark data\graph.json`.
- Targeted LangGraph workflow: send the LLM only the `foo()` node, its direct
  graph neighborhood, and the target source file instead of the whole project.

## Results

| Workflow | Estimated tokens | Reduction vs naive |
| --- | ---: | ---: |
| Naive full source read | 1,266 | 1.0x |
| Graphify average query | 583 | 2.2x |
| Targeted graph-guided LLM agent | 230 | 5.50x |

## Interpretation

The general Graphify query is already smaller than reading the whole source
corpus. The targeted workflow is much smaller because the agent starts from a
specific failing symbol, `foo()`, and uses the graph to pull only its direct
neighbors, current source location, and original broken snippet.

The token savings do not depend on the bug being difficult. The point is that a
graph can bound the investigation before source inspection begins.

When `OPENAI_API_KEY` is configured, `agent/workflow.py` also records provider
token usage in `llm_usage`. The saved comparison remains an estimate so the
submission is reproducible without exposing private API logs.

For local measurement, use:

```powershell
python agent\compare_token_usage.py --base-url http://localhost:11434/v1 --api-key local-ai --model llama3.1
```

That sends one naive full-context prompt and one graph-guided prompt to the same
local OpenAI-compatible model, then writes:

- `data/measured-token-comparison.json`
- `reports/MEASURED_TOKEN_COMPARISON.md`
