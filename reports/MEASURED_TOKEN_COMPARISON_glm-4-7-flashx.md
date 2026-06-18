# Measured Token Comparison

Model: `glm-4.7-flashx`

Base URL: `https://api.z.ai/api/paas/v4/`

Runs: `10`

## Average Results

| Run | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | 1672.0 | 954.7 | 2626.7 | 1.0 |
| Graph-guided | 554.0 | 809.4 | 1363.4 | 1.0 |

Average reduction: `1.93x`

## Latest Run

| Run | Prompt tokens | Completion tokens | Total tokens | Estimated prompt tokens | Usage source |
| --- | ---: | ---: | ---: | ---: | --- |
| Naive full-context | 1672 | 776 | 2448 | 650 | api_usage |
| Graph-guided | 554 | 782 | 1336 | 226 | api_usage |

| Run | Diagnosis success | Fix success | Overall success |
| --- | --- | --- | --- |
| Naive full-context | True | True | True |
| Graph-guided | True | True | True |

## Naive Response Preview

```text
**Diagnosis**
The function `foo` uses a mutable default argument (`bar=[]`). In Python, default argument values are evaluated only once when the function is defined, not each time the function is called. Consequently, the same list object is reused across all calls that omit the argument. On the first call, the list is empty, and `"baz"` is appended. On subsequent calls, the list still contains the previous `"baz"` entries, so another `"baz"` is appended, resulting in a growing list.

**Proposed Patch**
```python
def foo(bar=None):
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```
```

## Graph-Guided Response Preview

```text
**Diagnosis**
The function `foo` uses a mutable default argument (`bar=[]`). In Python, default arguments are evaluated only once when the function is defined, creating a single list object shared across all invocations. Each call modifies this shared list, causing it to accumulate elements ("baz") on every execution.

**Proposed Patch**
```python
def foo(bar=None):
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```
```
