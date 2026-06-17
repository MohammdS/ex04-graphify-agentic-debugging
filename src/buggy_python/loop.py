"""Lambda factory from the selected buggy repository."""


def lambda_array():
    """Return ten lambdas that add their index to a supplied value."""

    return [lambda x, i=i: x + i for i in range(10)]

