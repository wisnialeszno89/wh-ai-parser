from app.knowledge.profiles.profile import (
    Profile
)


def test_profile():

    profile = Profile(

        manufacturer="Veka",

        system="Softline 82"

    )

    assert profile.manufacturer == "Veka"

    assert profile.system == "Softline 82"