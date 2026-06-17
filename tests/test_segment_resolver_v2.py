from app.knowledge.resolvers.segment_resolver_v2 import (
    resolve_segment
)


def test_ru_segment():

    semantic = resolve_segment(

        {
            "opening":
                "tilt_turn"
        }

    )

    assert semantic

    assert (

        semantic.operation

        ==

        "create_ru"
    )

    assert (

        semantic.role

        ==

        "sash"
    )