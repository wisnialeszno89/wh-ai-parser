from app.wh.runtime.vision.sales_analytics import (
    SalesAnalytics
)


class SalesAnalyticsEngine:

    def analyze(

        self,

        brain

    ):

        project_analytics = (

            brain.project_analytics_engine.analyze(

                brain

            )

        )

        return (

            SalesAnalytics(

                total_offers=(

                    project_analytics.total_projects

                ),

                average_execution_time=(

                    project_analytics.average_execution_time

                ),

                average_error_count=(

                    project_analytics.average_error_count

                ),

                success_rate=(

                    project_analytics.success_rate

                )

            )

        )