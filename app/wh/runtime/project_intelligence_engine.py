from app.wh.runtime.project_report import (
    ProjectReport
)

from app.wh.runtime.configuration_engine import (
    ConfigurationEngine
)

from app.wh.runtime.geometry_engine import (
    GeometryEngine
)


class ProjectIntelligenceEngine:

    def __init__(

        self

    ):

        self.configuration_engine = (

            ConfigurationEngine()

        )

        self.geometry_engine = (

            GeometryEngine()

        )

    def analyze(

        self,

        project

    ):

        report = (

            ProjectReport()

        )

        report.configuration = (

            self.configuration_engine.analyze(

                project.offer

            )

        )

        report.geometry = (

            self.geometry_engine.analyze(

                project

            )

        )

        return report