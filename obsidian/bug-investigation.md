# Bug Investigation

## Symptom

The original `foo()` function returned a list that grew across repeated calls:

```python
def foo(bar=[]):
    bar.append("baz")
    return bar
```

Expected behavior from the original `main.py` assertions: each call to `foo()`
should return `["baz"]`.

## Graph-Guided Path

1. Start from the Graphify node `foo()`.
2. Read its direct neighborhood: `foobar.py`, `__init__.py`, and rationale node.
3. Load the original broken snapshot from `data/original-bug-context.json`.
4. Confirm that the only package-level impact is the public re-export.
5. Inspect `src/buggy_python/foobar.py`.
6. Patch the default argument and verify with tests.

## Root Cause

Python evaluates default argument values once when the function is defined. A
mutable default list is shared across calls, so `foo()` reused and mutated the
same list.

## Fix

`foo(bar=None)` now creates a fresh list when no caller-provided list exists:

```python
if bar is None:
    bar = []
```

See [[before-after]].
