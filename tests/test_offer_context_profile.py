from app.agent.offers.offer_context import OfferContext
from app.agent.offers.offer_context_merger import OfferContextMerger
from app.agent.offers.profile_selection import ProfileSelectionSource


def test_context_can_store_explicit_profile():
    context = OfferContext(
        raw_request="VEKA Softline 82",
        profile="VEKA_82",
        profile_source=ProfileSelectionSource.EXPLICIT,
    )

    assert context.profile == "VEKA_82"
    assert context.profile_source == ProfileSelectionSource.EXPLICIT


def test_context_can_store_default_profile():
    context = OfferContext(
        raw_request="okno 1200x1500 DKR",
        profile="VEKA_82",
        profile_source=ProfileSelectionSource.DEFAULT,
    )

    assert context.profile == "VEKA_82"
    assert context.profile_source == ProfileSelectionSource.DEFAULT


def test_context_can_store_unknown_profile():
    context = OfferContext(
        raw_request="VEKA Softline 76",
        profile=None,
        profile_source=ProfileSelectionSource.UNKNOWN,
    )

    assert context.profile is None
    assert context.profile_source == ProfileSelectionSource.UNKNOWN


def test_explicit_profile_replaces_default_profile():
    existing = OfferContext(
        raw_request="okno 1200x1500 DKR",
        profile="VEKA_82",
        profile_source=ProfileSelectionSource.DEFAULT,
    )

    update = OfferContext(
        raw_request="jednak VEKA Softline 82",
        profile="VEKA_82",
        profile_source=ProfileSelectionSource.EXPLICIT,
    )

    merged = OfferContextMerger().merge(existing, update)

    assert merged.profile == "VEKA_82"
    assert merged.profile_source == ProfileSelectionSource.EXPLICIT


def test_missing_profile_update_does_not_replace_existing_explicit_profile():
    existing = OfferContext(
        raw_request="VEKA Softline 82",
        profile="VEKA_82",
        profile_source=ProfileSelectionSource.EXPLICIT,
    )

    update = OfferContext(
        raw_request="kolor antracyt",
        profile=None,
        profile_source=ProfileSelectionSource.DEFAULT,
    )

    merged = OfferContextMerger().merge(existing, update)

    assert merged.profile == "VEKA_82"
    assert merged.profile_source == ProfileSelectionSource.EXPLICIT




def test_unknown_profile_change_creates_conflict():
    existing = OfferContext(
        raw_request="VEKA Softline 82",
        profile="VEKA_82",
        profile_source=ProfileSelectionSource.EXPLICIT,
    )

    update = OfferContext(
        raw_request="jednak VEKA Softline 76",
        profile=None,
        profile_source=ProfileSelectionSource.UNKNOWN,
    )

    merged = OfferContextMerger().merge(existing, update)

    assert merged.profile is None
    assert merged.profile_source == ProfileSelectionSource.UNKNOWN
    assert any(
        "profile" in conflict.lower()
        for conflict in merged.conflicts
    )
