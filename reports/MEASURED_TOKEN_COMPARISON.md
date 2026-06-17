# Measured Token Comparison

Model: `gemma4:e2b`

Base URL: `http://localhost:11434/v1`

Runs: `10`

## Average Results

| Run | Avg prompt tokens | Avg completion tokens | Avg total tokens | Success rate |
| --- | ---: | ---: | ---: | ---: |
| Naive full-context | 2061.0 | 1315.4 | 3376.4 | 1.0 |
| Graph-guided | 851.0 | 578.5 | 1429.5 | 0.9 |

Average reduction: `2.36x`

## Latest Run

| Run | Prompt tokens | Completion tokens | Total tokens | Estimated prompt tokens | Usage source |
| --- | ---: | ---: | ---: | ---: | --- |
| Naive full-context | 2061 | 1312 | 3373 | 732 | api_usage |
| Graph-guided | 851 | 555 | 1406 | 315 | api_usage |

| Run | Diagnosis success | Fix success | Overall success |
| --- | --- | --- | --- |
| Naive full-context | True | True | True |
| Graph-guided | True | True | True |

## Naive Response Preview

```text
**Bug Identification**

The issue stems from using a mutable object (a list) as a default argument in the function definition, which causes that list to be shared across all calls to the function.

**Root Cause**

In Python, default arguments are evaluated only once when the function is defined. If the default argument is a mutable type (like a list or dictionary), subsequent calls to the function that rely on this default will operate on the *same* object instance, leading to cumulative mutations across calls.

*(Note: While the provided `foobar.py` snippet attempts to fix this by checking `if bar is None:`, the classic bug described in the context arises when the default is defined as `bar=[]` without that conditional check.)*

**Minimal Fix**

The fix is to ensure a fresh list is created every time the function is called if no argument is provided. This is achieved by setting the default value to `None` and initializing the list inside the function body only when necessary.

**Fixed Code (`src/buggy_python/foobar.py`)**

```python
def foo(bar=None):
    """Return a list containing a single ``\"baz\"`` item."""

    if bar is None:
        bar = []  # Initialize a new list only w
```

## Graph-Guided Response Preview

```text
**Root Cause:**
The function `foo()` returns a growing list on repeated calls because default arguments in Python are evaluated only once when the function is defined. If the default argument is a mutable object (like a list), subsequent calls reuse and mutate the same list instance.

**Minimal Fix:**
Initialize the default argument to `None` and create a new list inside the function body if no argument was provided.

```python
def foo(bar=None):
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```
```
