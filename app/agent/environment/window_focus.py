"""Small, platform-independent helpers for validating Windows focus observations."""


def is_target_window_focused(
    target_window_handle: int,
    foreground_window_handle: int,
    foreground_root_owner_handle: int,
) -> bool:
    """Return whether the target HWND or one of its owned foreground windows is active."""
    try:
        target = int(target_window_handle)
        foreground = int(foreground_window_handle)
        root_owner = int(foreground_root_owner_handle)
    except (TypeError, ValueError, OverflowError):
        return False

    return target > 0 and (foreground == target or root_owner == target)
