from app.wh.runtime.vision.execution_subsystem import (
    ExecutionSubsystem
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_execution_subsystem():

    brain = (

        ProjectBrain()

    )

    subsystem = (

        ExecutionSubsystem(

            brain

        )

    )

    assert (

        subsystem.offer_execution_planner

        is not None

    )

    assert (

        subsystem.intelligent_vision_executor

        is not None

    )

    assert (

        subsystem.offer_execution_pipeline

        is not None

    )

    assert (

        subsystem.execution_verification_pipeline

        is not None

    )

    assert (

        subsystem.self_healing_execution_pipeline

        is not None

    )

    assert (

        subsystem.adaptive_self_healing_pipeline

        is not None

    )