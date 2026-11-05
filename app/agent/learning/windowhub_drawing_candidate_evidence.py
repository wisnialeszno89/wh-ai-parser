"""Read-only Win32 evidence for a detected WindowHub construction rectangle.

This verifies ownership of a candidate pixel using WindowFromPoint + GA_ROOT.
It deliberately does NOT claim any frame/sash/glass identity, dimensions,
or authority to click; a colored patch may be part of the application chrome.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DrawingCandidateEvidence:
    status: str
    point: tuple[int, int] | None
    within_window: bool
    foreground_matches: bool
    root_matches: bool
    reason: str


def check_drawing_candidate_owner(
    *,
    window_rect,
    candidate_rect,
    offer_hwnd: int,
    foreground_hwnd: int,
    hit_root_hwnd: int,
) -> DrawingCandidateEvidence:
    """Pure evidence decision; candidate bounds use captured-window local pixels."""
    if (
        type(offer_hwnd) is not int or offer_hwnd <= 0
        or type(foreground_hwnd) is not int
        or type(hit_root_hwnd) is not int
    ):
        raise ValueError("invalid_window_identity")
    if candidate_rect is None or window_rect is None:
        return DrawingCandidateEvidence("not_observed", None, False, False, False, "no_candidate_rectangle")
    x = int(candidate_rect.x)
    y = int(candidate_rect.y)
    w = int(candidate_rect.width)
    h = int(candidate_rect.height)
    win_w = int(window_rect.width)
    win_h = int(window_rect.height)
    valid = (
        w > 0 and h > 0 and win_w > 0 and win_h > 0
        and x >= 0 and y >= 0 and x + w <= win_w and y + h <= win_h
    )
    point = (int(window_rect.left) + x + w // 2, int(window_rect.top) + y + h // 2) if valid else None
    foreground_matches = foreground_hwnd == offer_hwnd
    root_matches = hit_root_hwnd == offer_hwnd
    if not valid:
        return DrawingCandidateEvidence("rejected", None, False, foreground_matches, root_matches, "candidate_outside_offer_capture")
    if not foreground_matches:
        return DrawingCandidateEvidence("rejected", point, True, False, root_matches, "offer_lost_foreground")
    if not root_matches:
        return DrawingCandidateEvidence("rejected", point, True, True, False, "pixel_owned_by_other_root_window")
    return DrawingCandidateEvidence(
        "owned_pixel_not_component_verified", point, True, True, True,
        "owner_verified_but_shape_and_component_identity_not_verified"
    )


def inspect_win32_candidate_owner(window_rect, candidate_rect, offer_hwnd: int) -> DrawingCandidateEvidence:
    """Native evidence. Exact ctypes signatures avoid Python 3.14 callback issues."""
    import ctypes
    from ctypes import wintypes

    if candidate_rect is None:
        return check_drawing_candidate_owner(
            window_rect=window_rect, candidate_rect=None, offer_hwnd=offer_hwnd,
            foreground_hwnd=0, hit_root_hwnd=0,
        )
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]
    user32.WindowFromPoint.argtypes = [POINT]
    user32.WindowFromPoint.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND

    foreground = int(user32.GetForegroundWindow() or 0)
    x = int(candidate_rect.x)
    y = int(candidate_rect.y)
    w = int(candidate_rect.width)
    h = int(candidate_rect.height)
    valid = (
        w > 0 and h > 0 and x >= 0 and y >= 0
        and x + w <= int(window_rect.width)
        and y + h <= int(window_rect.height)
    )
    hit_root = 0
    if valid:
        point = POINT(int(window_rect.left) + x + w // 2, int(window_rect.top) + y + h // 2)
        hit = user32.WindowFromPoint(point)
        hit_root = int(user32.GetAncestor(hit, 2) or 0) if hit else 0
    return check_drawing_candidate_owner(
        window_rect=window_rect, candidate_rect=candidate_rect,
        offer_hwnd=offer_hwnd, foreground_hwnd=foreground, hit_root_hwnd=hit_root,
    )
