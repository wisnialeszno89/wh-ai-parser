from app.knowledge.catalog.load_patterns import (
    load_pattern
)


def test_fix_ru_fix():

    pattern = load_pattern(
        "FIX|RU|FIX"
    )

    assert pattern

    assert (

        pattern["signature"]

        ==

        "FIX|RU|FIX"
    )