from app.agent.environment.window_focus import is_target_window_focused


def test_exact_foreground_window_is_focused():
    assert is_target_window_focused(410, 410, 410)


def test_owned_foreground_dialog_counts_as_target_window_focused():
    assert is_target_window_focused(410, 990, 410)


def test_unrelated_foreground_window_does_not_count_as_focused():
    assert not is_target_window_focused(410, 990, 770)


def test_invalid_target_handle_never_counts_as_focused():
    assert not is_target_window_focused(0, 0, 0)


def test_invalid_handle_values_fail_closed():
    assert not is_target_window_focused(None, 410, 410)
