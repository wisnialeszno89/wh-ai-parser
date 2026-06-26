from app.wh.runtime.construction_normalizer import (
    ConstructionNormalizer
)


def test_construction_normalizer():

    normalizer = (

        ConstructionNormalizer()

    )

    assert (

        normalizer.normalize(

            "ru fix ru"

        )

    ) == (

        "RU+FIX+RU"

    )

    assert (

        normalizer.normalize(

            "RU/FIX/RU"

        )

    ) == (

        "RU+FIX+RU"

    )

    assert (

        normalizer.normalize(

            "ru,fix,ru"

        )

    ) == (

        "RU+FIX+RU"

    )