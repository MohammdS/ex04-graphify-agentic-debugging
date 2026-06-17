"""Default argument example from the selected buggy repository."""


def foo(bar=None):
    """Return a list containing a single ``"baz"`` item.

    The original implementation used ``bar=[]``. Python evaluates default
    arguments once at function definition time, so repeated calls reused and
    mutated the same list.
    """

    if bar is None:
        bar = []
    bar.append("baz")
    return bar

