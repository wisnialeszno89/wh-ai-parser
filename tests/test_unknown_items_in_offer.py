from app.knowledge.offer.offer_parser import (
    parse_offer
)


def test_unknown_items():

    text = """

1500x1400 FIX RU FIX

nawiewnik Aereco

dziwny parapet z komorą

"""

    draft = parse_offer(
        text
    )

    assert len(
        draft.constructions
    ) == 1

    assert len(
        draft.accessories
    ) == 1

    assert len(
        draft.unknown_items
    ) == 1

    assert (

        draft.unknown_items[0]
        .source_text

        ==

        "dziwny parapet z komorą"

    )