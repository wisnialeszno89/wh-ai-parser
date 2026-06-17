from unittest.mock import (
    MagicMock
)

from types import (
    SimpleNamespace
)

from app.wh.runtime.automation_engine import (
    AutomationEngine
)


def test_full_automation_engine():

    engine = (

        AutomationEngine()

    )

    engine.runtime = (

        MagicMock()

    )

    engine.runtime.execute.return_value = (

        True

    )

    construction = (

        SimpleNamespace(

            segments=[

                SimpleNamespace(

                    kind="frame"

                ),

                SimpleNamespace(

                    kind="sash"

                )

            ]

        )

    )

    result = (

        engine.execute(

            construction

        )

    )

    assert result is True

    engine.runtime.execute.assert_called_once()