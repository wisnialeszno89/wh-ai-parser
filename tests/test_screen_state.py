from app.wh.runtime.screen_state import (
    ScreenState
)


def test_screen_state():

    assert ScreenState.LIST == "LIST"

    assert ScreenState.POSITION == "POSITION"