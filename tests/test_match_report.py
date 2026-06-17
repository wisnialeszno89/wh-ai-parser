from app.wh.vision.match_report import (
    MatchReport
)


def test_match_report():

    report = MatchReport(

        normal=0.24,

        gray=0.28,

        multiscale=0.81,

        winner="multiscale"

    )

    assert report.winner == "multiscale"

    assert report.multiscale > report.gray

    assert report.gray > report.normal