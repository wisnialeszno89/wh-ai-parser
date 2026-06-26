from app.wh.runtime.vision.rollback_engine import (
    RollbackEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.gui_state_snapshot import (
    GUIStateSnapshot
)


def test_rollback_engine():

    brain = (

        ProjectBrain()

    )

    brain.gui_state_history.remember(

        GUIStateSnapshot(

            current_tab="hardware"

        )

    )

    engine = (

        RollbackEngine()

    )

    result = (

        engine.rollback(

            brain

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.restored_snapshot.current_tab

        ==

        "hardware"

    )