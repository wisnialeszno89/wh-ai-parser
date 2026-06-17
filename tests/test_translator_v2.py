from app.wh.runtime.translator import (
    Translator
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)


def test_translator_v2():

    translator = Translator()

    construction = ConstructionSchema(

        width=1500,

        height=1400,

        schema="basic_window"

    )

    actions = translator.translate(

        construction

    )

    assert actions == [

        "frame",

        "sash",

        "glass"

    ]