"""Pure policy tests: no Windows, no external model, no customer data."""
import pytest

from app.agent.knowledge.windowhub_decision_policy import (
    Decision, FieldEvidence, CatalogAlternative, decide_field, decide_position_fallback, decision_context,
)
from app.agent.offers.windowhub_salesperson_policy import SalesPosition


def ev(**kwargs):
    return FieldEvidence(observed=True, **kwargs)


def test_explicit_requirement_cannot_be_silently_replaced():
    decision = decide_field("glazing", "3 szyby", ev(available_options=("2 szyby",)), default="2 szyby")
    assert decision.action == Decision.ASK
    assert decision.desired == "3 szyby"
    assert decision.source == "request"


def test_default_only_when_live_catalogue_supports_it():
    assert decide_field("color", None, ev(available_options=("biały",)), default="biały").action == Decision.APPLY
    assert decide_field("color", None, ev(available_options=("antracyt",)), default="biały").action == Decision.ASK


def test_exact_value_kept_without_reclick():
    result = decide_field("hardware", "UR ACTIVPILOT", ev(value="ur activpilot"))
    assert result.action == Decision.KEEP


@pytest.mark.parametrize("evidence,expected", [
    (FieldEvidence(observed=False), Decision.INSPECT),
    (ev(unique_target=False), Decision.INSPECT),
    (ev(exact_document=False), Decision.STOP),
    (ev(editable=False), Decision.ASK),
])
def test_cannot_act_without_authoritative_observation(evidence, expected):
    assert decide_field("width", "1500", evidence).action == expected


def test_inspected_empty_catalogue_requires_clarification():
    assert decide_field("profile", "Veka", ev(available_options=())).action == Decision.ASK


def test_optional_missing_can_be_skipped():
    assert decide_field("handle", None, ev(), required=False).action == Decision.SKIP_OPTIONAL


def test_placeholder_requires_real_dimensions_and_capability():
    item = SalesPosition(width_mm=1500, height_mm=1400)
    assert decide_position_fallback(item, dimensions_verified=True,
                                    placeholder_supported=True,
                                    unverified_or_unavailable=("profile",)) == Decision.PLACEHOLDER
    assert decide_position_fallback(item, dimensions_verified=False,
                                    placeholder_supported=True,
                                    unverified_or_unavailable=("profile",)) == Decision.ASK
    assert decide_position_fallback(item, dimensions_verified=True,
                                    placeholder_supported=False,
                                    unverified_or_unavailable=("profile",)) == Decision.ASK
    assert decide_position_fallback(item, dimensions_verified=True,
                                    placeholder_supported=True,
                                    unverified_or_unavailable=()) == Decision.INSPECT


def test_model_context_never_grants_execution_authority():
    ctx = decision_context()
    assert "readback" in ctx["loop"]
    assert "Do not SAVE" in ctx["approval"]


def test_nearest_option_requires_live_available_and_proven_compatibility():
    options = (
        CatalogAlternative("UR RC2", False, True, "different security level", 1),
        CatalogAlternative("UR ACTIVPILOT", True, True, "approved fallback", 2),
    )
    result = decide_field(
        "hardware", "Unavailable exact fitting",
        ev(available_options=("UR RC2", "UR ACTIVPILOT")),
        alternatives=options,
    )
    assert result.action == Decision.SUBSTITUTE
    assert result.desired == "UR ACTIVPILOT"
    assert result.requested == "Unavailable exact fitting"
    assert result.substitution_requires_review


def test_alternative_cannot_be_used_if_not_live_catalogue_option():
    result = decide_field(
        "profile", "X", ev(available_options=("Z",)),
        alternatives=(CatalogAlternative("Y", True, True, "different profile", 1),),
    )
    assert result.action == Decision.INSPECT


def test_no_unproven_or_equal_ranked_substitution():
    result = decide_field(
        "glazing", "3 panes", ev(available_options=("2 panes",)),
        alternatives=(CatalogAlternative("2 panes", False, True, "not verified", 1),),
    )
    assert result.action == Decision.ASK
    tie = (
        CatalogAlternative("A", True, True, "alt1", 1),
        CatalogAlternative("B", True, True, "alt2", 1),
    )
    assert decide_field(
        "profile", "Original", ev(available_options=("A", "B")),
        alternatives=tie,
    ).action == Decision.ASK
