from app.wh.runtime.query.query_preprocessor import (
    QueryPreprocessor
)


def test_query_preprocessor():

    preprocessor = (

        QueryPreprocessor()

    )

    text = """

    pakiet trzyszybowy

    sl82

    r+f

    2000 na 1500

    """

    result = preprocessor.preprocess(

        text

    )

    assert len(

        result

    ) == 4