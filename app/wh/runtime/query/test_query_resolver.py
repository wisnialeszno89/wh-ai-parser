from app.wh.runtime.query.query_resolver import (
    QueryResolver
)


def test_query_resolver():

    resolver = QueryResolver()

    query = resolver.resolve(

        """

        okno 2000 na 1500

        r+f

        sl82

        pakiet trzyszybowy

        """

    )

    assert query.width == 2000

    assert query.height == 1500

    assert query.pattern == "RU|FIX"

    assert query.profile == (

        "VEKA SOFTLINE 82"

    )

    assert query.glass == (

        "3 SZYBY"

    )