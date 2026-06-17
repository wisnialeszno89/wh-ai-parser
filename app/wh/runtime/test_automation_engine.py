from unittest.mock import (
    MagicMock
)

from types import (
    SimpleNamespace
)

from app.wh.runtime.automation_engine import (
    AutomationEngine
)


def test_automation_engine():

    engine = (

        AutomationEngine()

    )

    engine.planner = (

        MagicMock()

    )

    engine.runtime = (

        MagicMock()

    )

    construction = (

        SimpleNamespace()

    )

    engine.planner.plan.return_value = [

        "action1",

        "action2"

    ]

    engine.runtime.execute.return_value = (

        True

    )

    result = (

        engine.execute(

            construction

        )

    )

    assert result is True

    engine.planner.plan.assert_called_once_with(

        construction

    )

    engine.runtime.execute.assert_called_once()