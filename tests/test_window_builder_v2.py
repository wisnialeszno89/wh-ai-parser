from app.wh.runtime.window_builder import (
    WindowBuilder
)


def test_window_builder_v2():

    builder = WindowBuilder()

    result = builder.build_window(

        "basic_window"

    )

    assert result is True