# Measured Token Comparison

Model: `gemma4:e2b`

Base URL: `http://localhost:11434/v1`

Runs: `10`

## Average Results

| Run | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | 1914.0 | 790.0 | 2704.0 | 0.9 |
| Graph-guided | 683.0 | 558.2 | 1241.2 | 1.0 |

Average reduction: `2.18x`

## Latest Run

| Run | Prompt tokens | Completion tokens | Total tokens | Estimated prompt tokens | Usage source |
| --- | ---: | ---: | ---: | ---: | --- |
| Naive full-context | 1914 | 762 | 2676 | 661 | api_usage |
| Graph-guided | 683 | 560 | 1243 | 237 | api_usage |

| Run | Diagnosis success | Fix success | Overall success |
| --- | --- | --- | --- |
| Naive full-context | True | True | True |
| Graph-guided | True | True | True |

## Naive Response Preview

```text
**Diagnosis:**

The function `foo` exhibits unexpected behavior because it uses a mutable object (a list) as a default argument (`bar=[]`). In Python, default arguments are evaluated once when the function is defined. If the default argument is a mutable type (like a list), subsequent calls omit the argument and reuse the same list object that was modified during previous calls, leading to the list growing indefinitely.

**Root Cause:**
The bug stems from using a mutable default argument (`[]`) in the function definition of `foo` in `src/buggy_python/foobar.py`.

**Proposed Patch (Minimal Fix):**

Modify `src/buggy_python/foobar.py` to initialize a new list if no argument is provided, ensuring each call operates on an independent list.

```python
def foo(bar=None):
    """Return a list containing ``"baz"``."""
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```
```

## Graph-Guided Response Preview

```text
**Diagnosis:**
The function `foo()` returns a growing list because the default argument `bar=[]` creates a mutable list object that is shared across all calls to the function. When `bar.append("baz")` is executed, it modifies this single, shared list object, causing subsequent calls to return lists that have accumulated elements from previous calls.

**Proposed Patch:**
Initialize the default argument to `None` and create a new list inside the function body if no argument is provided.

```python
def foo(bar=None):
    """Return a list containing ``"baz"``."""
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```
```
