from unittest.mock import (
    MagicMock
)

from app.wh.runtime.schema.construction_schema_factory import (
    ConstructionSchemaFactory
)

from app.wh.runtime.constructions.construction_engine import (
    ConstructionEngine
)

from app.wh.runtime.constructions.executors.construction_executor import (
    ConstructionExecutor
)


def test_real_pattern():

    schema = (

        ConstructionSchemaFactory()

        .create(

            pattern="RU|FIX",

            width=2000,

            height=1500

        )

    )

    construction = (

        ConstructionEngine()

        .build(

            schema

        )

    )

    executor = (

        ConstructionExecutor()

    )

    executor.field_executor = (

        MagicMock()

    )

    executor.mullion_executor = (

        MagicMock()

    )

    executor.transom_executor = (

        MagicMock()

    )

    result = (

        executor.execute(

            construction

        )

    )

    executor.field_executor.execute.assert_called_once()

    executor.mullion_executor.execute.assert_called_once()

    executor.transom_executor.execute.assert_called_once()

    assert result is True