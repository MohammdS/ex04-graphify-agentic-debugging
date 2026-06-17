"""Default argument example from the selected buggy repository."""


def foo(bar=[]):
    """Return a list containing ``"baz"``.

    This intentionally preserves the original bug for investigation: the
    default list is shared across calls.
    """

    bar.append("baz")
    return bar
