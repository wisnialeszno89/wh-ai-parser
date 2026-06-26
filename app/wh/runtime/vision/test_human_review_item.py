from app.wh.runtime.vision.human_review_item import (
    HumanReviewItem
)


def test_human_review_item():

    item = (

        HumanReviewItem(

            goal="enable_contacts",

            reason="dialog_not_found"

        )

    )

    assert (

        item.goal

        ==

        "enable_contacts"

    )

    assert (

        item.reason

        ==

        "dialog_not_found"

    )