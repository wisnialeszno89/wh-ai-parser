from unittest.mock import (
    MagicMock
)

from types import SimpleNamespace

from app.wh.runtime.construction_pipeline import (
    ConstructionPipeline
)

from app.wh.runtime.actions.action_plan_executor import (
    ActionPlanExecutor
)

from app.wh.runtime.fields.field import (
    Field
)


def test_full_runtime_flow():

    f1 = Field(

        id=1,

        x=500,

        y=300

    )

    f2 = Field(

        id=2,

        x=1000,

        y=300

    )

    construction = (

        SimpleNamespace(

            topology=[

                [

                    f1,

                    f2

                ]

            ]

        )

    )

    pipeline = (

        ConstructionPipeline()

    )

    plan = (

        pipeline.execute(

            construction

        )

    )

    executor = (

        ActionPlanExecutor()

    )

    executor.executor = (

        MagicMock()

    )

    result = (

        executor.execute(

            plan

        )

    )

    assert (

        executor.executor

        .execute_action

        .call_count

        == 1

    )

    assert result is True