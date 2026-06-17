from unittest.mock import (
    MagicMock
)

from app.wh.runtime.query.dimension_parser import (
    DimensionParser
)

from app.wh.runtime.query.opening_registry import (
    OpeningRegistry
)

from app.wh.runtime.query.profile_registry import (
    ProfileRegistry
)

from app.wh.runtime.query.glass_registry import (
    GlassRegistry
)

from app.wh.runtime.query.query_model import (
    QueryModel
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


def test_dirty_query_to_runtime():

    text = """

    okno 2000 na 1500

    r+f

    sl82

    pakiet trzyszybowy

    """

    width, height = (

        DimensionParser()

        .parse(

            text

        )

    )

    pattern = (

        OpeningRegistry()

        .resolve(

            "R+F"

        )

    )

    profile = (

        ProfileRegistry()

        .resolve(

            "SL82"

        )

    )

    glass = (

        GlassRegistry()

        .resolve(

            "PAKIET TRZYSZYBOWY"

        )

    )

    query = QueryModel(

        width=width,

        height=height,

        pattern=pattern,

        profile=profile,

        glass=glass

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

    assert query.profile == "VEKA SOFTLINE 82"

    assert query.glass == "3 SZYBY"

    assert len(

        construction.fields

    ) == 2

    executor.field_executor.execute.assert_called_once()

    executor.mullion_executor.execute.assert_called_once()

    executor.transom_executor.execute.assert_called_once()

    assert result is True