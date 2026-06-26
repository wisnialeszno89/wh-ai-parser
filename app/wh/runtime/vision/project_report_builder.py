from app.wh.runtime.vision.project_execution_report import (
    ProjectExecutionReport
)


class ProjectReportBuilder:

    def build(

        self,

        brain

    ):

        report = (

            ProjectExecutionReport()

        )

        report.completed_goals = (

            brain.goal_memory.completed.copy()

        )

        report.failed_goals = [

            record.goal

            for record in (

                brain.failure_history.records

            )

        ]

        report.requires_human_review = (

            len(

                report.failed_goals

            )

            >

            0

        )

        total = (

            len(

                report.completed_goals

            )

            +

            len(

                report.failed_goals

            )

        )

        if total > 0:

            report.success_rate = (

                round(

                    100

                    *

                    len(

                        report.completed_goals

                    )

                    /

                    total,

                    2

                )

            )

        return report