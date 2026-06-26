from app.wh.runtime.construction_project import (
    ConstructionProject
)

from app.wh.runtime.construction_offer import (
    ConstructionOffer
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.project_intelligence_engine import (
    ProjectIntelligenceEngine
)


def test_project_intelligence_engine():

    project = (

        ConstructionProject(

            schema=ConstructionSchema(

                width=1800,

                height=1400,

                schema="RU+FIX+RU"

            ),

            offer=ConstructionOffer()

        )

    )

    project.offer.profile.system = (

        "Softline 82 MD"

    )

    project.offer.glass.thickness_mm = (

        52

    )

    engine = (

        ProjectIntelligenceEngine()

    )

    report = (

        engine.analyze(

            project

        )

    )

    assert (

        report.configuration

        .optimized_offer

        .glass

        .thickness_mm

        ==

        48

    )