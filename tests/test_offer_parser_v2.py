from app.knowledge.offer.offer_parser import (
    parse_offer
)


def test_full_offer():

    text = """

1500x1400 FIX RU FIX

antracyt / biały

Veka Softline 82

Ug 0.5

nawiewnik Aereco

"""

    draft = parse_offer(
        text
    )

    assert len(
        draft.constructions
    ) == 1

    assert len(
        draft.colors
    ) == 1

    assert len(
        draft.glasses
    ) == 1

    assert len(
        draft.profiles
    ) == 1

    assert len(
        draft.accessories
    ) == 1

    assert len(
        draft.unknown_items
    ) == 0