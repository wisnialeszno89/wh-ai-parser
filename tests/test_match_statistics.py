from app.wh.vision.match_report import (
    MatchReport
)

from app.wh.vision.match_statistics import (
    MatchStatistics
)


def test_match_statistics():

    reports = [

        (

            "screen1",

            MatchReport(

                normal=0.2,

                gray=0.5,

                multiscale=0.3,

                winner="gray"

            )

        ),

        (

            "screen2",

            MatchReport(

                normal=0.3,

                gray=0.4,

                multiscale=0.9,

                winner="multiscale"

            )

        ),

        (

            "screen3",

            MatchReport(

                normal=0.1,

                gray=0.8,

                multiscale=0.5,

                winner="gray"

            )

        )

    ]

    stats = MatchStatistics()

    result = stats.summarize(

        reports

    )

    assert result["gray"] == 2

    assert result["multiscale"] == 1