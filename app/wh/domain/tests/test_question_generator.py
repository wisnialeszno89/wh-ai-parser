from app.wh.domain.analysis.missing_information import (
    MissingInformation
)

from app.wh.domain.analysis.question_generator import (
    QuestionGenerator
)


def test_question_generator():

    missing = MissingInformation()

    missing.add("glazing")

    missing.add("security")

    report = (

        QuestionGenerator().generate(

            missing

        )

    )

    assert len(report.items) == 2

    assert report.items[0].priority >= report.items[1].priority

    assert "glazing" in report.items[0].field

    assert "Please" in report.items[0].question