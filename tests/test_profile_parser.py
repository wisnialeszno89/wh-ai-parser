from app.knowledge.profiles.profile_parser import (
    parse_profile
)


def test_veka():

    profile = parse_profile(

        "Veka Softline 82"

    )

    assert profile.manufacturer == "Veka"


def test_salamander():

    profile = parse_profile(

        "Salamander 82"

    )

    assert profile.manufacturer == "Salamander"


def test_ideal_8000():

    profile = parse_profile(

        "Ideal 8000"

    )

    assert profile.system == "Ideal 8000"


def test_bluevolution():

    profile = parse_profile(

        "BluEvolution 82"

    )

    assert profile.system == "BluEvolution 82"


def test_unknown():

    profile = parse_profile(

        "Kosmiczny profil"

    )

    assert profile is None