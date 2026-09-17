from app.agent.offers.profile_selection import (
    ProfileSelectionResolver,
    ProfileSelectionSource,
)


def test_explicit_profile_takes_precedence():
    result = ProfileSelectionResolver().resolve(
        "Potrzebuję okno 1200x1500 VEKA Softline 82"
    )

    assert result.profile == "VEKA_82"
    assert result.source == ProfileSelectionSource.EXPLICIT


def test_missing_profile_uses_default():
    result = ProfileSelectionResolver().resolve(
        "Potrzebuję okno 1200x1500 DKR"
    )

    assert result.profile == "VEKA_82"
    assert result.source == ProfileSelectionSource.DEFAULT


def test_default_profile_must_exist_in_catalog():
    try:
        ProfileSelectionResolver(
            default_profile="UNKNOWN_PROFILE"
        )
    except ValueError as exc:
        assert "Unknown default profile" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for unknown default profile"
        )


def test_unknown_profile_does_not_use_default():
    result = ProfileSelectionResolver().resolve(
        "Potrzebuję okno 1200x1500 VEKA Softline 76"
    )

    assert result.profile is None
    assert result.source == ProfileSelectionSource.UNKNOWN
    assert "could not be resolved" in result.reason


def test_unknown_profile_does_not_use_default():
    result = ProfileSelectionResolver().resolve(
        "Potrzebuję okno 1200x1500 VEKA Softline 76"
    )

    assert result.profile is None
    assert result.source == ProfileSelectionSource.UNKNOWN
    assert "could not be resolved" in result.reason
