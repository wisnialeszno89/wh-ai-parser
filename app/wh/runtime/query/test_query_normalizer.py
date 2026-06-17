from app.wh.runtime.query.query_normalizer import (
    QueryNormalizer
)


def test_query_normalizer():

    normalizer = QueryNormalizer()

    text = """

    2000 x 1500

    ru + fix

    sl82

    pakiet trzyszybowy

    """

    result = normalizer.normalize(

        text

    )

    assert "2000x1500" in result

    assert "RU|FIX" in result

    assert "VEKA SOFTLINE 82" in result

    assert "3 SZYBY" in result