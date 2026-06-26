from app.wh.runtime.vision.project_report_builder import (
    ProjectReportBuilder
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)

from app.wh.runtime.vision.failure_record import (
    FailureRecord
)


def test_project_report_builder():

    brain = (

        ProjectBrain()

    )

    brain.goal_memory.remember(

        GUIGoal(

            "enable_rc2"

        )

    )

    brain.failure_history.remember(

        FailureRecord(

            goal="enable_contacts",

            reason="dialog_not_found"

        )

    )

    builder = (

        ProjectReportBuilder()

    )

    report = (

        builder.build(

            brain

        )

    )

    assert (

        len(

            report.completed_goals

        )

        ==

        1

    )

    assert (

        len(

            report.failed_goals

        )

        ==

        1

    )

    assert (

        report.requires_human_review

        is True

    )

    assert (

        report.success_rate

        ==

        50.0

    )