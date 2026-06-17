from unittest.mock import (
    MagicMock
)

from app.wh.runtime.query.query_normalizer import (
    QueryNormalizer
)

from app.wh.runtime.query.query_parser import (
    QueryParser
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


def test_human_query_to_runtime():

    text = """

    2000 x 1500

    ru + fix

    sl82

    pakiet trzyszybowy

    """

    normalized = (

        QueryNormalizer()

        .normalize(

            text

        )

    )

    query = (

        QueryParser()

        .parse(

            normalized

        )

    )

    schema = (

        ConstructionSchemaFactoryV2()

        .create(

            pattern=query.pattern,

            width=query.width,

            height=query.height

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

    assert query.width == 2000

    assert query.height == 1500

    assert query.pattern == "RU|FIX"

    assert query.profile == (

        "VEKA SOFTLINE 82"

    )

    assert query.glass == (

        "3 SZYBY"

    )

    assert len(

        construction.fields

    ) == 2

    executor.field_executor.execute.assert_called_once()

    executor.mullion_executor.execute.assert_called_once()

    executor.transom_executor.execute.assert_called_once()

    assert result is True