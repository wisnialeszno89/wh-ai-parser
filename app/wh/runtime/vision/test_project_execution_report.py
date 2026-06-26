from app.wh.runtime.vision.project_execution_report import (
    ProjectExecutionReport
)


def test_project_execution_report():

    report = (

        ProjectExecutionReport()

    )

    report.completed_goals.append(

        "enable_rc2"

    )

    report.failed_goals.append(

        "enable_contacts"

    )

    report.requires_human_review = (

        True

    )

    report.success_rate = (

        50.0

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