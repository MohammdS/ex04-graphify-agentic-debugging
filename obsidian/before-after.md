# Broken Code and Applied Fix

## Before (preserved snapshot)

The original repository shipped the mutable default list bug. This snapshot is
preserved in `data/original-bug-context.json` and is what the agent and the token
experiment diagnose against:

```python
def foo(bar=[]):
    bar.append("baz")
    return bar
```

Repeated calls shared state:

```python
foo()  # ["baz"]
foo()  # ["baz", "baz"]
```

## After (applied in source)

The fix is applied in `src/buggy_python/foobar.py` using `None` as the sentinel:

```python
def foo(bar=None):
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```

The before/after is provable from version control: the "before" lives in
`data/original-bug-context.json` and in the git history; the "after" is the
current `src/buggy_python/foobar.py`.

## Verification

The regression test is no longer expected-failing — it now passes:

```text
python -m pytest -q
3 passed
```
