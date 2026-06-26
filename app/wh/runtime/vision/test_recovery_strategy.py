from app.wh.runtime.vision.recovery_strategy import (
    RecoveryStrategy
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_recovery_strategy():

    brain = (

        ProjectBrain()

    )

    brain.gui_state.current_dialog = (

        "glass"

    )

    strategy = (

        RecoveryStrategy()

    )

    assert (

        strategy.recover(

            brain

        )

        is True

    )

    assert (

        brain.gui_state.current_dialog

        is None

    )