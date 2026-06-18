import pytest

from buggy_python import (
    average_paid_loans,
    calculate_paid_loans,
    calculate_unpaid_loans,
    foo,
    lambda_array,
    read_file,
)


def test_original_expected_outputs():
    lambdas = lambda_array()
    json_file = read_file()

    assert lambdas[0](10) == 10
    assert lambdas[9](10) == 19
    assert len(json_file["loans"]) == 15
    assert calculate_unpaid_loans(json_file) == 11062
    assert calculate_paid_loans(json_file) == pytest.approx(29493.85304)
    assert average_paid_loans(json_file) == pytest.approx(2681.2593672727276)


def test_foo_does_not_share_default_list_between_calls():
    # Regression test for the fixed mutable-default-argument bug.
    assert foo() == ["baz"]
    assert foo() == ["baz"]


def test_foo_accepts_explicit_list_when_caller_wants_mutation():
    values = ["existing"]

    assert foo(values) == ["existing", "baz"]
    assert values == ["existing", "baz"]
