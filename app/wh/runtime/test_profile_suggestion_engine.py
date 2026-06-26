from app.wh.runtime.construction_offer import (
    ConstructionOffer
)

from app.wh.runtime.profile_suggestion_engine import (
    ProfileSuggestionEngine
)


def test_profile_suggestion_engine():

    offer = (

        ConstructionOffer()

    )

    offer.profile.system = (

        "Softline 82 MD"

    )

    offer.glass.thickness_mm = (

        52

    )

    engine = (

        ProfileSuggestionEngine()

    )

    suggestions = (

        engine.suggest(

            offer

        )

    )

    assert len(

        suggestions

    ) == 1

    assert (

        suggestions[0]

        .code

        ==

        "GLASS_PACKAGE_SUGGESTION"

    )