from app.wh.runtime.vision.recovery_engine import (
    RecoveryEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_recovery_engine():

    brain = (

        ProjectBrain()

    )

    brain.gui_state.current_dialog = (

        "color"

    )

    engine = (

        RecoveryEngine()

    )

    assert (

        engine.recover(

            brain

        )

        is True

    )

    assert (

        brain.gui_state.current_dialog

        is None

    )