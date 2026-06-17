from app.knowledge.offer.unknown_item import (
    UnknownItem
)


def test_unknown_item():

    item = UnknownItem(

        source_text=

            "dziwny parapet z komorą"

    )

    assert (

        item.source_text

        ==

        "dziwny parapet z komorą"

    )