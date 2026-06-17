# Before and After

## Before

The original `andela/buggy-python` implementation used a mutable default list:

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

## After

The fixed implementation uses `None` as the default sentinel:

```python
def foo(bar=None):
    if bar is None:
        bar = []
    bar.append("baz")
    return bar
```

Verification:

```text
python -m pytest -q
3 passed
```

