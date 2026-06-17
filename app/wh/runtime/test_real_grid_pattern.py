from unittest.mock import (
    MagicMock
)

from app.wh.runtime.patterns.pattern_parser import (
    PatternParser
)

from app.wh.runtime.schema.pattern_schema_builder import (
    PatternSchemaBuilder
)

from app.wh.runtime.constructions.construction_engine import (
    ConstructionEngine
)

from app.wh.runtime.constructions.executors.construction_executor import (
    ConstructionExecutor
)


def test_real_grid_pattern():

    rows = (

        PatternParser()

        .parse(

            "RU|FIX/FIX|RU"

        )

    )

    schema = (

        PatternSchemaBuilder()

        .build(

            rows,

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

    assert len(

        construction.fields

    ) == 4

    assert result is True