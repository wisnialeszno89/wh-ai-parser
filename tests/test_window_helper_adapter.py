from app.runtime.window_helper.window_helper_adapter import (
    WindowHelperAdapter
)


def test_window_helper_adapter():

    adapter = WindowHelperAdapter()

    adapter.connect()

    assert adapter.connected