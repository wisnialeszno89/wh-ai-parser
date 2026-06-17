from unittest.mock import (
    MagicMock
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.constructions.construction_engine import (
    ConstructionEngine
)

from app.wh.runtime.constructions.executors.construction_executor import (
    ConstructionExecutor
)

from app.wh.runtime.segments.segment import (
    Segment
)

from app.wh.runtime.openings.opening_types import (
    TILT_TURN,
    FIX
)


def test_real_construction():

    schema = ConstructionSchema(

        width=2000,

        height=1500,

        schema="basic_window",

        ratio_x=[0.5],

        segments=[

            Segment(

                opening=TILT_TURN

            ),

            Segment(

                opening=FIX

            )

        ]

    )

    engine = ConstructionEngine()

    construction = engine.build(

        schema

    )

    executor = ConstructionExecutor()

    executor.field_executor = (

        MagicMock()

    )

    executor.mullion_executor = (

        MagicMock()

    )

    executor.transom_executor = (

        MagicMock()

    )

    result = executor.execute(

        construction

    )

    executor.field_executor.execute.assert_called_once()

    executor.mullion_executor.execute.assert_called_once()

    executor.transom_executor.execute.assert_called_once()

    assert result is True