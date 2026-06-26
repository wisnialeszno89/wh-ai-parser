from app.wh.runtime.vision.project_analytics import (
    ProjectAnalytics
)


class ProjectAnalyticsEngine:

    def analyze(

        self,

        brain

    ):

        projects = (

            brain.project_execution_history.projects

        )

        total_projects = (

            len(

                projects

            )

        )

        successful_projects = (

            sum(

                1

                for p in projects

                if p.success

            )

        )

        failed_projects = (

            total_projects

            -

            successful_projects

        )

        if total_projects == 0:

            success_rate = 0.0

            average_execution_time = 0.0

            average_error_count = 0.0

        else:

            success_rate = (

                successful_projects

                /

                total_projects

            )

            average_execution_time = (

                sum(

                    p.execution_time_seconds

                    for p in projects

                )

                /

                total_projects

            )

            average_error_count = (

                sum(

                    p.error_count

                    for p in projects

                )

                /

                total_projects

            )

        return (

            ProjectAnalytics(

                total_projects=total_projects,

                successful_projects=successful_projects,

                failed_projects=failed_projects,

                success_rate=success_rate,

                average_execution_time=average_execution_time,

                average_error_count=average_error_count

            )

        )