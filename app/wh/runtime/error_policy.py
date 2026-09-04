from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorAction(str, Enum):
    RETRY = "retry"
    ACKNOWLEDGE = "acknowledge"
    SKIP = "skip"
    STOP = "stop"


class ErrorSeverity(str, Enum):
    RECOVERABLE = "recoverable"
    RETRYABLE = "retryable"
    SKIPPABLE = "skippable"
    FATAL = "fatal"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ErrorPolicyDecision:
    code: str
    severity: ErrorSeverity
    action: ErrorAction
    message: str


_ERROR_POLICIES: dict[str, tuple[ErrorSeverity, ErrorAction]] = {
    "DIMENSION_TOO_LARGE": (ErrorSeverity.SKIPPABLE, ErrorAction.SKIP),
    "DIMENSION_TOO_SMALL": (ErrorSeverity.SKIPPABLE, ErrorAction.SKIP),
    "GLASS_NOT_ALLOWED": (ErrorSeverity.SKIPPABLE, ErrorAction.SKIP),
    "HARDWARE_NOT_ALLOWED": (ErrorSeverity.SKIPPABLE, ErrorAction.SKIP),
    "ELEMENT_NOT_COMPATIBLE": (ErrorSeverity.SKIPPABLE, ErrorAction.SKIP),
    "MISSING_DEPENDENCY": (ErrorSeverity.RETRYABLE, ErrorAction.RETRY),
    "INVALID_POSITION": (ErrorSeverity.SKIPPABLE, ErrorAction.SKIP),
    "INVALID_OPERATION": (ErrorSeverity.SKIPPABLE, ErrorAction.SKIP),
    "UNKNOWN_ERROR": (ErrorSeverity.FATAL, ErrorAction.STOP),
}


class WindowHubErrorPolicy:
    """Deterministic handling policy for known WindowHub messages."""

    def classify(self, code: str, message: str = "") -> ErrorPolicyDecision:
        normalized = code.strip().upper()
        severity, action = _ERROR_POLICIES.get(
            normalized,
            (ErrorSeverity.UNKNOWN, ErrorAction.STOP),
        )
        return ErrorPolicyDecision(
            code=normalized,
            severity=severity,
            action=action,
            message=message,
        )
