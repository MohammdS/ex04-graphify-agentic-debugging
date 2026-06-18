# Measured Token Comparison

Model: `glm-4.7-flashx`

Base URL: `https://api.z.ai/api/paas/v4/`

Runs: `10`

## Average Results

| Run | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | 1672.0 | 987.9 | 2659.9 | 1.0 |
| Graph-guided | 554.0 | 826.8 | 1380.8 | 1.0 |

Average reduction: `1.93x`

## Latest Run

| Run | Prompt tokens | Completion tokens | Total tokens | Estimated prompt tokens | Usage source |
| --- | ---: | ---: | ---: | ---: | --- |
| Naive full-context | 1672 | 1125 | 2797 | 650 | api_usage |
| Graph-guided | 554 | 829 | 1383 | 226 | api_usage |

| Run | Diagnosis success | Fix success | Overall success |
| --- | --- | --- | --- |
| Naive full-context | True | True | True |
| Graph-guided | True | True | True |

## Naive Response Preview

```text
**Diagnosis**

The function `foo` uses a **mutable default argument** (`bar=[]`). In Python, default argument values are evaluated only once when the function is defined, not every time the function is called. This creates a shared list instance in memory that persists across all calls to `foo`. When `bar.append("baz")` is executed, it modifies this shared list. Subsequent calls append to the already modified list, causing it to grow.

**Proposed Patch**

Change the default argument to `None` and initialize the list inside the function body to ensure a fresh list is created for each call.

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
The function uses a mutable default argument (`bar=[]`). In Python, default arguments are evaluated only once when the function is defined, not every time it is called. Consequently, the same list object persists across all invocations. When `bar.append("baz")` executes, it modifies this shared list, causing subsequent calls to return the accumulated data.

**Proposed Patch**
```python
def foo(bar=None):
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```
```
