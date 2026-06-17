from app.knowledge.offer.offer_draft import (
    OfferDraft
)

from app.knowledge.offer.unknown_item import (
    UnknownItem
)


def test_offer_draft():

    draft = OfferDraft(

        constructions=[],

        accessories=[],

        colors=[],

        glasses=[],

        profiles=[],

        unknown_items=[

            UnknownItem(

                source_text=

                    "parapet z komorą"

            )

        ]

    )

    assert len(

        draft.unknown_items

    ) == 1