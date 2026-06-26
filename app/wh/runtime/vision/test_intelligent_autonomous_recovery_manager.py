from app.wh.runtime.vision.intelligent_autonomous_recovery_manager import (
    IntelligentAutonomousRecoveryManager
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.gui_state_snapshot import (
    GUIStateSnapshot
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_intelligent_autonomous_recovery_manager():

    brain = (

        ProjectBrain()

    )

    brain.gui_state_history.remember(

        GUIStateSnapshot(

            current_tab="hardware"

        )

    )

    manager = (

        IntelligentAutonomousRecoveryManager()

    )

    result = (

        manager.recover(

            "template_not_found",

            brain

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.recovery_result.strategy

        ==

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        brain.recovery_learning_memory.count()

        ==

        1

    )