import unittest

from app.wh.runtime.error_policy import (
    ErrorAction,
    ErrorSeverity,
    WindowHubErrorPolicy,
)


class WindowHubErrorPolicyTests(unittest.TestCase):
    def test_known_errors_have_deterministic_actions(self) -> None:
        policy = WindowHubErrorPolicy()

        self.assertEqual(
            policy.classify("DIMENSION_TOO_LARGE").action,
            ErrorAction.SKIP,
        )
        self.assertEqual(
            policy.classify("MISSING_DEPENDENCY").action,
            ErrorAction.RETRY,
        )
        self.assertEqual(
            policy.classify("HARDWARE_NOT_ALLOWED").severity,
            ErrorSeverity.SKIPPABLE,
        )

    def test_unknown_error_stops(self) -> None:
        decision = WindowHubErrorPolicy().classify("something_new")

        self.assertEqual(decision.severity, ErrorSeverity.UNKNOWN)
        self.assertEqual(decision.action, ErrorAction.STOP)

    def test_normalizes_error_code(self) -> None:
        decision = WindowHubErrorPolicy().classify("  glass_not_allowed ")

        self.assertEqual(decision.code, "GLASS_NOT_ALLOWED")
        self.assertEqual(decision.action, ErrorAction.SKIP)


if __name__ == "__main__":
    unittest.main()
