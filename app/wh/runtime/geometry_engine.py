from app.wh.runtime.geometry_report import (
    GeometryReport
)


class GeometryEngine:

    def analyze(

        self,

        project

    ):

        report = (

            GeometryReport()

        )

        width = (

            project.schema.width

        )

        height = (

            project.schema.height

        )

        if width > 4000:

            report.problems.append(

                "WIDTH_EXCEEDED"

            )

        if height > 3000:

            report.problems.append(

                "HEIGHT_EXCEEDED"

            )

        return report