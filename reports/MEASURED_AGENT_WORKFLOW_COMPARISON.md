# Measured Agent Workflow Comparison

Model: `gemma4:e2b`

Base URL: `http://localhost:11434/v1`

| Workflow | Prompt tokens | Completion tokens | Total tokens | Diagnosis success | Fix success | Overall success |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Naive agent workflow | 4182 | 1600 | 5782 | False | False | False |
| Graph-guided agent workflow | 1765 | 1346 | 3111 | True | True | True |

Reduction basis: `sum_total_tokens_if_available_else_estimated_prompt_tokens`

Measured reduction: `1.86x`

## Naive Investigation Preview

```text

```

## Graph-Guided Investigation Preview

```text
The growing list issue stems from using mutable default arguments in Python. When a default argument is a mutable
```
