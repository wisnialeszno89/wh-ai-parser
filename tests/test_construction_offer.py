from app.wh.runtime.construction_offer import (
    ConstructionOffer
)


def test_construction_offer():

    offer = (

        ConstructionOffer()

    )

    offer.color_inside = (

        "anthracite"

    )

    offer.color_outside = (

        "anthracite"

    )

    offer.glass.type = (

        "3glass"

    )

    offer.glass.thickness_mm = (

        48

    )

    offer.glass.swisspacer = (

        True

    )

    offer.security.rc2 = (

        True

    )

    offer.hardware.hidden_hinges = (

        True

    )

    assert offer.color_inside == (

        "anthracite"

    )

    assert offer.glass.type == (

        "3glass"

    )

    assert offer.glass.thickness_mm == 48

    assert offer.glass.swisspacer is True

    assert offer.security.rc2 is True

    assert offer.hardware.hidden_hinges is True