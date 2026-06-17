from app.knowledge.offer.offer_parser import (
    parse_offer
)


def test_offer():

    text = """

1500x1400 FIX RU FIX

nawiewnik Aereco

parapet PVC 200

łącznik 90°

"""

    draft = parse_offer(
        text
    )

    assert len(
        draft.constructions
    ) == 1

    assert len(
        draft.accessories
    ) == 3

    assert len(
        draft.unknown_items
    ) == 0