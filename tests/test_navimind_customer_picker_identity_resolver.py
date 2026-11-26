"""Offline regression for the precise legacy WindowHub customer-picker control.

No native calls or desktop input are performed. This test injects fake UIA
elements and only exercises the resolver's read-only identity checks.
"""
from __future__ import annotations

import ctypes
from types import SimpleNamespace
import pytest
from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_wrapper


class Rect:
    left, top, right, bottom = 300, 250, 320, 270


class Wrapper:
    def __init__(self, *, runtime="1-2-3", name="Klient - wybór", control_id="IDC_ZAMAWIAJACY"):
        self.element_info = SimpleNamespace(
            control_type="Button", automation_id=control_id,
            runtime_id=runtime.split("-"), name=name,
            enabled=True, visible=True,
        )

    def rectangle(self):
        return Rect()


class Desktop:
    def __init__(self, wrappers):
        self.wrappers = wrappers

    def window(self, *, handle):
        assert handle == 55
        return self

    def wrapper_object(self):
        return self

    def descendants(self):
        return self.wrappers


def scene(*, count=1, stage="document_properties"):
    title = "Właściwości dokumentu" if stage == "document_properties" else "Okna - Start1"
    root = SimpleNamespace(
        state=SimpleNamespace(active_application="Okna.exe", active_window_title=title),
        metadata={
            "window_handle": 55,
            "window_rect": SimpleNamespace(left=200, top=200),
        },
    )
    elem = lambda: SimpleNamespace(
        kind="button",
        label="Klient - wybór",
        x=100, y=50, width=20, height=20,
        metadata={
            "semantic_label": "Klient - wybór",
            "source": "windowhub_ui_automation",
            "uia_visible": True, "uia_enabled": True,
            "uia_control_type": "button",
            "uia_runtime_id": "1-2-3",
            "automation_id": "IDC_ZAMAWIAJACY",
            "name": "Klient - wybór",
        },
    )
    return SimpleNamespace(observation=root, elements=[elem() for _ in range(count)])


@pytest.fixture
def foreground(monkeypatch):
    monkeypatch.setattr(
        ctypes, "windll",
        SimpleNamespace(user32=SimpleNamespace(GetForegroundWindow=lambda: 55)),
        raising=False,
    )
    monkeypatch.setattr(
        "app.agent.perception.windowhub_ui_automation_provider.WindowHubUIAutomationProvider._runtime_id",
        staticmethod(lambda wrapper: "-".join(map(str, wrapper.element_info.runtime_id))),
    )


def test_unique_exact_id_can_resolve_button_with_different_visible_name(foreground):
    candidate = Wrapper()
    result = resolve_native_wrapper(
        scene(), label="Wybierz istniejącego klienta",
        automation_id="IDC_ZAMAWIAJACY",
        allowed_stages=("document_properties",),
        desktop=Desktop([candidate]), exact_customer_picker_id=True,
    )
    assert result is candidate


def test_generic_resolver_does_not_ignore_semantic_name(foreground):
    with pytest.raises(ValueError, match="native_target_not_unique"):
        resolve_native_wrapper(
            scene(), label="Wybierz istniejącego klienta",
            automation_id="IDC_ZAMAWIAJACY",
            allowed_stages=("document_properties",),
            desktop=Desktop([Wrapper()]),
        )


def test_exact_id_exception_fails_for_wrong_scope_or_foreground(foreground, monkeypatch):
    with pytest.raises(ValueError, match="exact_customer_picker_scope_forbidden"):
        resolve_native_wrapper(
            scene(), label="NOWA OFERTA",
            automation_id="IDC_ZAMAWIAJACY",
            allowed_stages=("document_properties",),
            desktop=Desktop([Wrapper()]), exact_customer_picker_id=True,
        )
    monkeypatch.setattr(
        ctypes.windll.user32, "GetForegroundWindow", lambda: 99
    )
    with pytest.raises(ValueError, match="windowhub_not_foreground"):
        resolve_native_wrapper(
            scene(), label="Wybierz istniejącego klienta",
            automation_id="IDC_ZAMAWIAJACY",
            allowed_stages=("document_properties",),
            desktop=Desktop([Wrapper()]), exact_customer_picker_id=True,
        )


def test_exact_id_exception_requires_unique_scene_and_native_runtime_identity(foreground):
    with pytest.raises(ValueError, match="native_target_not_unique"):
        resolve_native_wrapper(
            scene(count=2), label="Wybierz istniejącego klienta",
            automation_id="IDC_ZAMAWIAJACY",
            allowed_stages=("document_properties",),
            desktop=Desktop([Wrapper()]), exact_customer_picker_id=True,
        )
    with pytest.raises(ValueError, match="fresh_native_control_identity_mismatch"):
        resolve_native_wrapper(
            scene(), label="Wybierz istniejącego klienta",
            automation_id="IDC_ZAMAWIAJACY",
            allowed_stages=("document_properties",),
            desktop=Desktop([Wrapper(runtime="9-9-9")]), exact_customer_picker_id=True,
        )
