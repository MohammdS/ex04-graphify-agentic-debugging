# Token Efficiency

The token comparison measures context needed before identifying the bug.

| Workflow | Context strategy | Estimated tokens |
| --- | --- | ---: |
| Naive | Read all source files under `src/` | 1,266 |
| Graphify benchmark | Average graph query context | 583 |
| Targeted LLM agent | `foo()` graph context, target source, and original bug snapshot | 230 |

Graphify benchmark result:

```text
Corpus: 950 words -> ~1,266 tokens
Avg query cost: ~583 tokens
Reduction: 2.2x fewer tokens per query
```

The targeted LangGraph workflow is even smaller because it starts at the
`foo()` graph node and sends the LLM graph-bounded context. If an API key is
configured, the workflow also records actual provider usage in `llm_usage`.

For a local-model measurement, run `agent/compare_token_usage.py`. It creates
`data/measured-token-comparison.json` and
`reports/MEASURED_TOKEN_COMPARISON.md`.
