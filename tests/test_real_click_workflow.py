from unittest.mock import MagicMock

from app.wh.vision.real_click_workflow import (
    RealClickWorkflow
)


def test_real_click_workflow():

    workflow = (

        RealClickWorkflow()

    )

    workflow.mouse = MagicMock()

    result = workflow.click(

        "samples/ui/wh_screen_06.png",

        "templates/add_position.png"

    )

    assert result.confidence > 0

    workflow.mouse.click.assert_called_once()