from tools.smoke_windowhub_v2_grid_structure import (
    _foreground_relation_matches,
)


def test_foreground_relation_accepts_windowhub_main_window():
    assert _foreground_relation_matches(
        foreground_handle=100,
        foreground_root_handle=100,
        foreground_root_owner_handle=100,
        windowhub_handle=100,
    )


def test_foreground_relation_accepts_owned_popup():
    assert _foreground_relation_matches(
        foreground_handle=200,
        foreground_root_handle=200,
        foreground_root_owner_handle=100,
        windowhub_handle=100,
    )


def test_foreground_relation_accepts_child_of_windowhub_root():
    assert _foreground_relation_matches(
        foreground_handle=300,
        foreground_root_handle=100,
        foreground_root_owner_handle=100,
        windowhub_handle=100,
    )


def test_foreground_relation_rejects_unrelated_application():
    assert not _foreground_relation_matches(
        foreground_handle=400,
        foreground_root_handle=400,
        foreground_root_owner_handle=400,
        windowhub_handle=100,
    )


def test_foreground_relation_rejects_missing_windowhub_handle():
    assert not _foreground_relation_matches(
        foreground_handle=0,
        foreground_root_handle=0,
        foreground_root_owner_handle=0,
        windowhub_handle=0,
    )
