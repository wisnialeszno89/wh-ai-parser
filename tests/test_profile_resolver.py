from app.wh.resolvers.profile_resolver import (
    ProfileResolutionStatus,
    ProfileResolver,
)


def test_known_profile_is_resolved():
    result = ProfileResolver().resolve_result(
        "Potrzebuję VEKA Softline 82"
    )

    assert result.status == ProfileResolutionStatus.RESOLVED
    assert result.profile == "VEKA_82"
    assert result.matched_alias == "softline 82"


def test_missing_profile_is_not_found():
    result = ProfileResolver().resolve_result(
        "Potrzebuję okno 1200x1500 DKR"
    )

    assert result.status == ProfileResolutionStatus.NOT_FOUND
    assert result.profile is None


def test_unknown_profile_is_not_found_but_marked_unknown():
    result = ProfileResolver().resolve_result(
        "Potrzebuję VEKA Softline 76"
    )

    assert result.status == ProfileResolutionStatus.UNKNOWN
    assert result.profile is None


def test_legacy_resolve_keeps_existing_contract():
    assert (
        ProfileResolver().resolve(
            "Potrzebuję VEKA Softline 82"
        )
        == "VEKA_82"
    )

    assert (
        ProfileResolver().resolve(
            "Potrzebuję okno 1200x1500 DKR"
        )
        is None
    )
