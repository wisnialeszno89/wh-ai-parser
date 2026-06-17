from app.wh.runtime.query.query_parser import (
    QueryParser
)


def test_query_parser():

    parser = QueryParser()

    query = parser.parse(

        """

        2000x1500

        RU|FIX

        Veka Softline 82

        3 szyby

        """

    )

    assert query.width == 2000

    assert query.height == 1500

    assert query.pattern == "RU|FIX"

    assert query.profile == "Veka Softline 82"

    assert query.glass == "3 szyby"