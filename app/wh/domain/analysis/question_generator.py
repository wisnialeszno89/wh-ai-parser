from app.wh.domain.analysis.missing_information import (
    MissingInformation
)

from app.wh.domain.analysis.missing_information_item import (
    MissingInformationItem
)

from app.wh.domain.analysis.missing_information_report import (
    MissingInformationReport
)


class QuestionGenerator:

    QUESTIONS = {

        "glazing": (

            100,

            "Please specify the glazing type (Double or Triple)."

        ),

        "security": (

            90,

            "Please specify the required security class."

        ),

        "outside_color": (

            80,

            "Please specify the outside colour."

        ),

        "inside_color": (

            80,

            "Please specify the inside colour."

        ),

        "products": (

            100,

            "Please specify which products should be quoted."

        )

    }

    def generate(

        self,

        missing: MissingInformation

    ) -> MissingInformationReport:

        report = MissingInformationReport()

        for field in missing.fields:

            priority, question = self.QUESTIONS.get(

                field,

                (

                    10,

                    f"Please provide '{field}'."

                )

            )

            report.add(

                MissingInformationItem(

                    field=field,

                    priority=priority,

                    question=question

                )

            )

        report.items.sort(

            key=lambda item: item.priority,

            reverse=True

        )

        return report