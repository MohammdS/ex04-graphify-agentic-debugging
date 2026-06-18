"""Default argument example from the selected buggy repository."""


def foo(bar=None):
    """Return a list containing ``"baz"``.

    Fix for the original mutable-default-argument bug: the default is ``None``
    and a fresh list is allocated on each implicit call, so repeated calls no
    longer share state. Callers that pass an explicit list still mutate it.
    """

    if bar is None:
        bar = []
    bar.append("baz")
    return bar
