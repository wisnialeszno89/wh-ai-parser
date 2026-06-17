from unittest.mock import (
    MagicMock
)

from app.wh.model.construction_schema import (
    ConstructionSchema
)

from app.wh.model.opening import (
    Opening
)

from app.wh.model.row import (
    Row
)

from app.wh.model.segment import (
    Segment
)

from app.wh.runtime.agent_workflow_v3 import (
    AgentWorkflowV3
)


def test_agent_workflow_v3():

    workflow = (

        AgentWorkflowV3()

    )

    workflow.executor = (

        MagicMock()

    )

    workflow.executor.execute.return_value = [

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

    result = workflow.execute(

        "screen.png",

        "templates",

        construction

    )

    assert len(

        result

    ) == 1