from app.wh.runtime.construction_offer import (
    ConstructionOffer
)

from app.wh.runtime.profile_optimizer import (
    ProfileOptimizer
)


def test_profile_optimizer():

    offer = (

        ConstructionOffer()

    )

    offer.profile.system = (

        "Softline 82 MD"

    )

    offer.glass.thickness_mm = (

        52

    )

    optimizer = (

        ProfileOptimizer()

    )

    optimized = (

        optimizer.optimize(

            offer

        )

    )

    assert (

        optimized.glass.thickness_mm

        ==

        48

    )