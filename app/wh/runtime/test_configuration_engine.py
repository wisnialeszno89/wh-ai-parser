from app.wh.runtime.construction_offer import (
    ConstructionOffer
)

from app.wh.runtime.configuration_engine import (
    ConfigurationEngine
)


def test_configuration_engine():

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

        ConfigurationEngine()

    )

    report = (

        engine.analyze(

            offer

        )

    )

    assert len(

        report.problems

    ) == 1

    assert len(

        report.suggestions

    ) == 1

    assert (

        report.optimized_offer

        .glass

        .thickness_mm

        ==

        48

    )