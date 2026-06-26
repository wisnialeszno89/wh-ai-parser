from app.wh.runtime.profile_reasoning_engine import (
    ProfileReasoningEngine
)

from app.wh.runtime.construction_offer import (
    ConstructionOffer
)


def test_profile_reasoning_engine():

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

        ProfileReasoningEngine()

    )

    problems = (

        engine.validate(

            offer

        )

    )

    assert len(

        problems

    ) == 1

    assert (

        problems[0]

        .code

        ==

        "INVALID_GLASS_PACKAGE"

    )