from app.wh.runtime.agent_workflow_v3 import (
    AgentWorkflowV3
)

from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine
)


class WHAgent:

    def __init__(

        self,

        mouse_enabled=False

    ):

        self.workflow = (

            AgentWorkflowV3(

                mouse_enabled=mouse_enabled

            )

        )

        self.screenshot_engine = (

            MSSScreenshotEngine()

        )

    def execute(

        self,

        construction,

        templates_dir

    ):

        screenshot = (

            self.screenshot_engine.capture()

        )

        return (

            self.workflow.execute(

                screenshot,

                templates_dir,

                construction

            )

        )