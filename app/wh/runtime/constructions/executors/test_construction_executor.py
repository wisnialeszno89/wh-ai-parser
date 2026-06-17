from unittest.mock import (
    MagicMock
)

from app.wh.runtime.constructions.executors.construction_executor import (
    ConstructionExecutor
)

from app.wh.runtime.constructions.construction import (
    Construction
)


def test_construction_executor():

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

    construction = Construction()

    result = executor.execute(

        construction

    )

    executor.field_executor.execute.assert_called_once()

    executor.mullion_executor.execute.assert_called_once()

    executor.transom_executor.execute.assert_called_once()

    assert result is True