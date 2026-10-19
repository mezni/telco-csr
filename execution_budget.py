# execution_budget.py

import time
from dataclasses import dataclass, field


class BudgetExceededError(Exception):
    """Raised when a request or time budget is exhausted."""


@dataclass
class ExecutionBudget:
    max_requests: int
    deadline_seconds: float
    requests_used: int = 0
    started_at: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_requests, bool)
            or not isinstance(self.max_requests, int)
            or self.max_requests < 1
        ):
            raise ValueError("max_requests must be a positive integer.")

        import math

        if not isinstance(self.deadline_seconds, (int, float)) or isinstance(
            self.deadline_seconds, bool
        ):
            raise ValueError("deadline_seconds must be positive.")

        if math.isinf(self.deadline_seconds) or math.isnan(self.deadline_seconds):
            raise ValueError("deadline_seconds must be positive.")

        if self.deadline_seconds <= 0:
            raise ValueError("deadline_seconds must be positive.")

    @property
    def remaining_seconds(self) -> float:
        elapsed = time.monotonic() - self.started_at
        return max(0.0, self.deadline_seconds - elapsed)

    @property
    def requests_remaining(self) -> int:
        return max(0, self.max_requests - self.requests_used)

    def reserve_request(self) -> float:
        """Reserve one provider request and return its time allowance."""
        remaining_time = self.remaining_seconds

        if remaining_time <= 0:
            raise BudgetExceededError("Execution deadline exceeded.")

        if self.requests_remaining <= 0:
            raise BudgetExceededError("Provider request budget exhausted.")

        self.requests_used += 1
        return remaining_time
