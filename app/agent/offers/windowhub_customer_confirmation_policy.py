"""Safety policy for exceptional salesperson-confirmed customer selection.

Operator attestation is not native/UIA readback. Only after an independently
observed exact-row click plus popup closure, the salesperson may authorize
continuing an *unsaved draft*. Never treat a generic 'tak' as consent.
"""
from __future__ import annotations

from app.agent.offers.windowhub_customer_result_selection import canonical_customer_name


def can_request_customer_attestation(lookup_outcome: str) -> bool:
    return (
        isinstance(lookup_outcome, str)
        and lookup_outcome.startswith("CUSTOMER_CLICKED_BUT_SELECTION_UNVERIFIED_")
        and lookup_outcome.endswith("_popup_closed")
    )


def valid_customer_attestation(
    *,
    typed_name: str,
    expected_name: str,
    stage: str | None,
    original_hwnd: int | None,
    observed_hwnd: int | None,
    observed_customer_value: str | None,
) -> bool:
    """Fail closed on stage/window changes, incorrect readback or partial names."""
    if not (isinstance(original_hwnd, int) and original_hwnd > 0
            and observed_hwnd == original_hwnd and stage == "document_properties"):
        return False
    if not isinstance(typed_name, str) or not typed_name.strip():
        return False
    expected = canonical_customer_name(expected_name)
    if not expected or canonical_customer_name(typed_name) != expected:
        return False
    # An exposed, conflicting value is stronger evidence than an attestation.
    if observed_customer_value is not None and canonical_customer_name(observed_customer_value) != expected:
        return False
    return True
