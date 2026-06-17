from app.wh.runtime.query.query_model import (
    QueryModel
)


def test_query_model():

    query = QueryModel(

        width=2000,

        height=1500,

        pattern="RU|FIX",

        profile="Veka Softline 82",

        glass="3 szyby"

    )

    assert query.width == 2000

    assert query.height == 1500

    assert query.pattern == "RU|FIX"