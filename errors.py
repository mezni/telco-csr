
# errors.py


class InferenceError(Exception):
    """A model inference failure with retry metadata."""

    def __init__(
        self,
        message: str,
        *,
        retryable: bool,
        attempts: int,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.attempts = attempts
        self.status_code = status_code

