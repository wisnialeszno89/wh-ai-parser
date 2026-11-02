from __future__ import annotations

import ctypes

import pytest

from tools.diagnose_windowhub_win32_children import _hwnd_value


def test_hwnd_value_accepts_python_integer():
    assert _hwnd_value(0x12345678) == 0x12345678


def test_hwnd_value_accepts_none_as_null_handle():
    assert _hwnd_value(None) == 0


def test_hwnd_value_accepts_ctypes_void_pointer():
    value = 0x123456789ABC
    assert _hwnd_value(ctypes.c_void_p(value)) == value


def test_hwnd_value_accepts_ctypes_scalar_with_integer_value():
    value = 0x12345678
    assert _hwnd_value(ctypes.c_size_t(value)) == value


def test_hwnd_value_accepts_native_pointer_bytes():
    value = 0x123456789ABC
    raw = value.to_bytes(ctypes.sizeof(ctypes.c_void_p), byteorder=__import__("sys").byteorder)
    assert _hwnd_value(raw) == value


def test_hwnd_value_rejects_unknown_representation():
    with pytest.raises(TypeError, match="unsupported_hwnd_representation"):
        _hwnd_value(object())
