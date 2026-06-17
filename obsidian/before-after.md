# Broken Code and Suggested Fix

## Broken Code

The repository intentionally preserves the mutable default list bug:

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

## Suggested Fix

The suggested implementation uses `None` as the default sentinel:

```python
def foo(bar=None):
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```

Verification keeps the bug test as expected-failing:

```text
python -m pytest -q
2 passed, 1 xfailed
```
