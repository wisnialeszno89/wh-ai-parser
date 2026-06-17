from unittest.mock import (
    MagicMock
)

from app.wh.runtime.wh_agent import (
    WHAgent
)

from app.wh.model.construction_schema import (
    ConstructionSchema
)

from app.wh.model.row import (
    Row
)

from app.wh.model.segment import (
    Segment
)

from app.wh.model.opening import (
    Opening
)


def test_wh_agent():

    agent = (

        WHAgent()

    )

    agent.workflow = (

        MagicMock()

    )

    agent.screenshot_engine = (

        MagicMock()

    )

    agent.screenshot_engine.capture.return_value = (

        "SCREENSHOT"

    )

    agent.workflow.execute.return_value = [

        (100, 200)

    ]

    construction = (

        ConstructionSchema(

            category="window",

            width_mm=2000,

            height_mm=1500,

            rows=[

                Row(

                    segments=[

                        Segment(

                            kind="main",

                            opening=Opening.FIX

                        )

                    ]

                )

            ]

        )

    )

    result = (

        agent.execute(

            construction,

            "templates"

        )

    )

    assert len(

        result

    ) == 1