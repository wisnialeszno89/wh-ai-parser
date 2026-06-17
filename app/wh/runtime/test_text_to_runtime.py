from unittest.mock import (
    MagicMock
)

from app.wh.runtime.schema.construction_schema_factory_v2 import (
    ConstructionSchemaFactoryV2
)

from app.wh.runtime.constructions.construction_engine import (
    ConstructionEngine
)

from app.wh.runtime.constructions.executors.construction_executor import (
    ConstructionExecutor
)


def test_text_to_runtime():

    schema = (

        ConstructionSchemaFactoryV2()

        .create(

            """

            RU|FIX

            FIX|RU

            """,

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

    assert len(

        construction.fields

    ) == 4

    assert len(

        construction.mullions

    ) > 0

    assert len(

        construction.transoms

    ) > 0

    executor.field_executor.execute.assert_called_once()

    executor.mullion_executor.execute.assert_called_once()

    executor.transom_executor.execute.assert_called_once()

    assert result is True