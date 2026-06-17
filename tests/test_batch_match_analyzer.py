from app.wh.vision.batch_match_analyzer import (
    BatchMatchAnalyzer
)


def test_batch_match_analyzer():

    analyzer = BatchMatchAnalyzer()

    reports = analyzer.analyze(

        "samples/ui",

        "templates/add_position.png"

    )

    assert len(

        reports

    ) > 0