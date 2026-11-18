"""Pure selection tests for safe cross-application Explorer auto focus."""
from app.agent.runtime.desktop_explorer_focus import select_unique_window


def window(hwnd, process="okna.exe", title="Okna - OFR/4708-",
           visible=True, minimized=False):
    return dict(hwnd=hwnd, process=process, title=title,
                visible=visible, minimized=minimized)


def test_single_matching_application_is_selected():
    assert select_unique_window(
        [window(11), window(22, process="code.exe")], process="Okna.exe"
    ) == (11, "unique_match")


def test_ambiguous_target_fails_closed():
    hwnd, reason = select_unique_window(
        [window(11), window(12)], process="okna.exe"
    )
    assert hwnd is None
    assert reason == "ambiguous_windows_2"


def test_title_filter_can_disambiguate_without_guessing():
    assert select_unique_window(
        [window(11, title="Okna - OFR/4708-"),
         window(12, title="Okna - ZLC/4709-")],
        process="okna.exe", title_contains="OFR/4708-",
    ) == (11, "unique_match")


def test_foreground_is_preferred_if_it_is_exact_match():
    assert select_unique_window(
        [window(11), window(12)], process="okna.exe", foreground_hwnd=12
    ) == (12, "already_foreground_match")


def test_wrong_process_or_minimized_is_not_eligible():
    result = select_unique_window(
        [window(11, process="code.exe"),
         window(12, minimized=True),
         window(13, visible=False)], process="okna.exe"
    )
    assert result == (None, "no_matching_visible_window")


def test_offer_preferred_over_idle_start1_when_explicitly_enabled():
    windows = [
        window(11, title="Okna - Start1"),
        window(12, title="Okna - OFR/4708-"),
    ]
    assert select_unique_window(
        windows, process="okna.exe", prefer_unique_offer=True,
    ) == (12, "unique_offer_over_idle_home")


def test_offer_preference_does_not_override_dialog():
    windows = [
        window(11, title="Wybór okuć: 1"),
        window(12, title="Okna - OFR/4708-"),
    ]
    hwnd, reason = select_unique_window(
        windows, process="okna.exe", prefer_unique_offer=True,
    )
    assert hwnd is None
    assert reason == "ambiguous_windows_2"


def test_offer_preference_does_not_pick_between_two_offers():
    windows = [
        window(11, title="Okna - OFR/4708-"),
        window(12, title="Okna - OFR/4709-"),
    ]
    hwnd, reason = select_unique_window(
        windows, process="okna.exe", prefer_unique_offer=True,
    )
    assert hwnd is None
    assert reason == "ambiguous_windows_2"
