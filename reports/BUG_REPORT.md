# Bug Report

## Selected Repository

Repository: `andela/buggy-python`

Reason for selection: it is intentionally small, Python-only, and designed for
debugging practice. That makes it suitable for demonstrating architectural
reverse engineering and graph-guided context reduction without spending most of
the assignment on environment setup.

## Selected Bug

Mutable default argument in `foo()`.

Original pattern:

```python
def foo(bar=[]):
    bar.append("baz")
    return bar
```

## Expected Behavior

Two independent calls should each return a single-item list:

```python
foo() == ["baz"]
foo() == ["baz"]
```

## Actual Broken Behavior

The second call reuses the list created during function definition and returns a
larger list:

```python
foo() == ["baz", "baz"]
```

## Root Cause

Python default arguments are evaluated once at function definition time. Because
the default value is a mutable list, every call without an explicit `bar` argument
mutates the same list object.

## Applied Fix

The fix is applied in `src/buggy_python/foobar.py`: use `None` as a sentinel and
allocate a new list per implicit call:

```python
def foo(bar=None):
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```

## Regression Test

`tests/test_buggy_python.py` contains:

```python
def test_foo_does_not_share_default_list_between_calls():
    assert foo() == ["baz"]
    assert foo() == ["baz"]
```

The fix is applied in source and the regression test now passes. The original
buggy version is preserved in `data/original-bug-context.json` (and in git
history) as the documented "before":

```text
python -m pytest -q
3 passed
```
