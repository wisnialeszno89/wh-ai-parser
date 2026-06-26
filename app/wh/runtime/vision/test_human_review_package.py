from app.wh.runtime.vision.human_review_package import (
    HumanReviewPackage
)

from app.wh.runtime.vision.human_review_item import (
    HumanReviewItem
)


def test_human_review_package():

    package = (

        HumanReviewPackage()

    )

    package.items.append(

        HumanReviewItem(

            goal="enable_contacts",

            reason="dialog_not_found"

        )

    )

    package.top_failure_reason = (

        "dialog_not_found"

    )

    assert (

        len(

            package.items

        )

        ==

        1

    )

    assert (

        package.top_failure_reason

        ==

        "dialog_not_found"

    )