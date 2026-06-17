from unittest.mock import (
    MagicMock
)

from types import SimpleNamespace

from app.wh.runtime.runtime_coordinator import (
    RuntimeCoordinator
)

from app.wh.runtime.fields.field import (
    Field
)


def test_runtime_coordinator():

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

    coordinator = (

        RuntimeCoordinator()

    )

    coordinator.executor = (

        MagicMock()

    )

    result = (

        coordinator.execute(

            construction

        )

    )

    coordinator.executor.execute.assert_called_once()

    assert result is (

        coordinator.executor

        .execute.return_value

    )