from app.wh.vision.template_competition import (
    TemplateCompetition
)


def test_template_competition():

    competition = (

        TemplateCompetition()

    )

    winner, result = (

        competition.run(

            "samples/ui/wh_screen_06.png",

            "templates"

        )

    )

    assert result.confidence > 0