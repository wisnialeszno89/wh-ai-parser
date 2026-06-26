from app.wh.runtime.vision.recovery_subsystem import (
    RecoverySubsystem
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_recovery_subsystem():

    brain = (

        ProjectBrain()

    )

    subsystem = (

        RecoverySubsystem(

            brain

        )

    )

    assert (

        subsystem.recovery_knowledge_base

        is not None

    )

    assert (

        subsystem.recovery_strategy_selector

        is not None

    )

    assert (

        subsystem.adaptive_recovery_engine

        is not None

    )

    assert (

        subsystem.adaptive_self_healing_pipeline

        is not None

    )