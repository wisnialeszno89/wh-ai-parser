import unittest

from app.wh.runtime.controlled_executor import ControlledExecutor
from app.wh.runtime.error_policy import ErrorAction


class ControlledExecutorTests(unittest.TestCase):
    def test_success_does_not_retry(self) -> None:
        calls = 0

        def operation() -> bool:
            nonlocal calls
            calls += 1
            return True

        result = ControlledExecutor().run(operation)

        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 1)
        self.assertEqual(calls, 1)

    def test_retryable_error_retries_once(self) -> None:
        calls = 0

        def operation() -> bool:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("dependency missing")
            return True

        result = ControlledExecutor().run(
            operation,
            error_code=lambda _: "MISSING_DEPENDENCY",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(calls, 2)

    def test_skippable_error_is_not_retried(self) -> None:
        calls = 0

        def operation() -> bool:
            nonlocal calls
            calls += 1
            raise RuntimeError("too large")

        result = ControlledExecutor().run(
            operation,
            error_code=lambda _: "DIMENSION_TOO_LARGE",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.action, ErrorAction.SKIP)
        self.assertEqual(result.attempts, 1)
        self.assertEqual(calls, 1)

    def test_unknown_error_stops_without_retry(self) -> None:
        calls = 0

        def operation() -> bool:
            nonlocal calls
            calls += 1
            raise RuntimeError("new WH error")

        result = ControlledExecutor().run(operation)

        self.assertFalse(result.success)
        self.assertEqual(result.action, ErrorAction.STOP)
        self.assertEqual(result.attempts, 1)
        self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()
