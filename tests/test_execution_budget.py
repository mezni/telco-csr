# tests/test_execution_budget.py

import time

import pytest

from execution_budget import (
    BudgetExceededError,
    ExecutionBudget,
)


def test_initial_budget_has_expected_values():
    budget = ExecutionBudget(
        max_requests=3,
        deadline_seconds=10,
    )

    assert budget.requests_used == 0
    assert budget.requests_remaining == 3
    assert 0 < budget.remaining_seconds <= 10


def test_reserve_request_decrements_remaining_budget():
    budget = ExecutionBudget(
        max_requests=2,
        deadline_seconds=10,
    )

    remaining_time = budget.reserve_request()

    assert remaining_time > 0
    assert budget.requests_used == 1
    assert budget.requests_remaining == 1


def test_request_budget_cannot_be_exceeded():
    budget = ExecutionBudget(
        max_requests=1,
        deadline_seconds=10,
    )

    budget.reserve_request()

    with pytest.raises(
        BudgetExceededError,
        match="request budget exhausted",
    ):
        budget.reserve_request()

    assert budget.requests_used == 1


def test_expired_deadline_prevents_request():
    budget = ExecutionBudget(
        max_requests=3,
        deadline_seconds=10,
    )

    # Simulate an operation that has exceeded its deadline.
    budget.started_at = time.monotonic() - 11

    with pytest.raises(
        BudgetExceededError,
        match="deadline exceeded",
    ):
        budget.reserve_request()

    assert budget.requests_used == 0


@pytest.mark.parametrize(
    "max_requests",
    [0, -1, True, 1.5, "3"],
)
def test_invalid_request_budget_is_rejected(max_requests):
    with pytest.raises(ValueError):
        ExecutionBudget(
            max_requests=max_requests,
            deadline_seconds=10,
        )


@pytest.mark.parametrize(
    "deadline",
    [0, -1, float("inf"), float("nan")],
)
def test_invalid_deadline_is_rejected(deadline):
    with pytest.raises(ValueError):
        ExecutionBudget(
            max_requests=3,
            deadline_seconds=deadline,
        )


def test_request_budget_is_shared_between_references():
    budget = ExecutionBudget(
        max_requests=2,
        deadline_seconds=10,
    )

    same_budget = budget
    same_budget.reserve_request()

    assert budget.requests_used == 1
    assert budget.requests_remaining == 1


def test_remaining_time_decreases():
    budget = ExecutionBudget(
        max_requests=3,
        deadline_seconds=10,
    )

    initial_remaining = budget.remaining_seconds
    time.sleep(0.01)
    updated_remaining = budget.remaining_seconds

    assert updated_remaining < initial_remaining
