from app.wh.runtime.translator import (
    Translator
)


def test_translator():

    translator = Translator()

    actions = translator.translate(

        "basic_window"

    )

    assert actions == [

        "frame",

        "sash",

        "glass"

    ]