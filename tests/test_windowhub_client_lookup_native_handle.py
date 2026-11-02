from __future__ import annotations

from types import SimpleNamespace

from tools.diagnose_windowhub_client_lookup_popup_link import (
    _lookup_native_handle,
)


def test_lookup_native_handle_prefers_wrapper_handle():
    wrapper = SimpleNamespace(
        handle=12345,
        element_info=SimpleNamespace(handle=67890),
    )
    assert _lookup_native_handle(wrapper) == 12345


def test_lookup_native_handle_falls_back_to_element_info_handle():
    wrapper = SimpleNamespace(
        element_info=SimpleNamespace(handle=67890),
    )
    assert _lookup_native_handle(wrapper) == 67890


def test_lookup_native_handle_returns_zero_when_no_native_handle_exists():
    wrapper = SimpleNamespace(
        element_info=SimpleNamespace(handle=0),
    )
    assert _lookup_native_handle(wrapper) == 0


def test_lookup_native_handle_survives_wrapper_property_error():
    class WrapperWithBrokenHandle:
        @property
        def handle(self):
            raise RuntimeError("no HWND projection")

        element_info = SimpleNamespace(handle=24680)

    assert _lookup_native_handle(WrapperWithBrokenHandle()) == 24680
