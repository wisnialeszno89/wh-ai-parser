from app.knowledge.text.build_segments import (
    build_segments
)


def test_fix_ru_fix():

    segments = build_segments(

        "FIX RU FIX"

    )

    assert len(
        segments
    ) == 3


def test_german():

    segments = build_segments(

        "Fest DK Fest"

    )

    assert len(
        segments
    ) == 3


def test_polish():

    segments = build_segments(

        "P FIX"

    )

    assert len(
        segments
    ) == 2