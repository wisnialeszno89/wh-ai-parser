from app.wh.runtime.vision.product_knowledge.profile_repository import (
    ProfileRepository
)


def test_profile_repository():

    repo = (

        ProfileRepository()

    )

    profiles = (

        repo.find_matching(

            security="RC2",

            glazing="Triple"

        )

    )

    assert len(

        profiles

    ) == 1

    assert (

        profiles[0]["system"]

        ==

        "Softline 82 MD"

    )