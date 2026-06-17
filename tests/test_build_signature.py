from app.knowledge.signatures.build_signature import (
    build_signature
)


def test_fix_ru_fix():

    segments = [

        {
            "opening": "fixed"
        },

        {
            "opening": "tilt_turn"
        },

        {
            "opening": "fixed"
        }
    ]

    assert (

        build_signature(
            segments
        )

        ==

        "FIX|RU|FIX"
    )