from app.knowledge.resolvers.segment_resolver import (
    resolve_segment
)


def test_fix():

    assert (
        resolve_segment(
            {
                "opening": "fixed"
            }
        )
        ==
        "create_fix"
    )


def test_ru():

    assert (
        resolve_segment(
            {
                "opening": "tilt_turn"
            }
        )
        ==
        "create_ru"
    )