"""Pure intent checks for an unnumbered draft-only user clarification."""
from app.agent.runtime.navimind_live_conversation import (
    explicit_unsaved_draft_only_constraint,
)


def test_user_unnumbered_draft_scope_is_not_an_action_request():
    assert explicit_unsaved_draft_only_constraint(
        "interesuje cie tylko niezapisany dokument bez przypisanego numeru oferty"
    )
    assert explicit_unsaved_draft_only_constraint(
        "Pracuj wyłącznie na roboczej ofercie bez numeru oferty."
    )


def test_scope_intent_does_not_authorize_clicks_or_existing_offer():
    assert not explicit_unsaved_draft_only_constraint(
        "Kliknij wybierz klienta w niezapisanym dokumencie bez numeru oferty"
    )
    assert not explicit_unsaved_draft_only_constraint(
        "Przygotuj nową ofertę dla Top Trans"
    )
    assert not explicit_unsaved_draft_only_constraint(
        "Pracuj na OFR/4830-"
    )
