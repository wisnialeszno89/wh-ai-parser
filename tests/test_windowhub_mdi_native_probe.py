"""No action is permitted by native ancestry diagnostics alone."""
from app.agent.runtime.windowhub_mdi_native_probe import (
    classify_native_candidates,
    native_title_matches,
)


def test_exact_native_mdi_caption_matching():
    assert native_title_matches("OFR/4680-", " OFR/4680- ")
    assert not native_title_matches("OFR/4680-", "OFR/4678-")
    assert not native_title_matches("OFR/4680-", "Document OFR/4680-")
    assert not native_title_matches("", "OFR/4680-")


def test_no_title_only_evidence_does_not_promote_action():
    result = classify_native_candidates(
        selected_document="OFR/4680-",
        candidate_ancestor_titles=(
            ("", "Main Window"),
            ("", "Main Window"),
            ("", "Main Window"),
        ),
    )
    assert result.status == "native_mdi_scope_unresolved"
    assert result.unknown_buttons == 3


def test_multiple_matching_ancestors_are_ambiguous():
    result = classify_native_candidates(
        selected_document="OFR/4680-",
        candidate_ancestor_titles=(
            ("OFR/4680-", "OFR/4680-"),
            ("OFR/4670-",),
        ),
    )
    assert result.status == "native_mdi_scope_unresolved"


def test_single_candidate_still_requires_structural_validation():
    result = classify_native_candidates(
        selected_document="OFR/4680-",
        candidate_ancestor_titles=(
            ("OFR/4670-",),
            ("OFR/4680-",),
            ("OFR/4678-",),
        ),
    )
    assert result.status == "candidate_for_structural_validation"
    assert result.scope_candidates == (
        "unresolved", "matching_mdi_ancestor", "unresolved"
    )
    # Not equivalent to verified UIA-document scope or permission to click.
