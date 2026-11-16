"""Regression tests: populated WindowHub dimension edits replace, never append."""
from types import SimpleNamespace as N

from app.agent.runtime.windowhub_dimension_replace import (
    DimensionReplaceResult, classify_replace, replace_dimension_once,
)


def test_classify_dimension_current_value():
    assert classify_replace("1000", 1500) == "replace_existing"
    assert classify_replace("1500", 1500) == "already_satisfied"
    assert classify_replace("", 1400) == "fill_empty"
    assert classify_replace(None, 1500) == "unknown"


def test_reject_invalid_dimension():
    import pytest
    for value in (0, 99, 5001, True):
        with pytest.raises(ValueError):
            classify_replace("1000", value)


def test_existing_value_is_replaced_once_not_appended(monkeypatch):
    from app.agent.runtime import windowhub_dimension_replace as m
    state = {"value": "1000", "calls": 0}

    class FakeValuePattern:
        CurrentIsReadOnly = False
        @property
        def CurrentValue(self):
            return state["value"]

        def SetValue(self, value):
            state["calls"] += 1
            state["value"] = value

    wrapper = N(iface_value=FakeValuePattern())
    loop = N(observe_scene=lambda: object())
    monkeypatch.setattr(m, "current_dimension", lambda scene, key: state["value"])
    monkeypatch.setattr(m, "_resolve_native_field", lambda scene, key: wrapper)

    result = replace_dimension_once(loop, field_name="width_1", desired=1500)
    assert result.status == "verified"
    assert result.previous_value == "1000"
    assert result.observed_value == "1500"
    assert state["calls"] == 1

    result = replace_dimension_once(loop, field_name="width_1", desired=1500)
    assert result.reason == "already_satisfied"
    assert state["calls"] == 1


def test_mismatched_native_value_is_not_overwritten(monkeypatch):
    from app.agent.runtime import windowhub_dimension_replace as m

    class Pattern:
        CurrentValue = "2000"
        CurrentIsReadOnly = False

        def SetValue(self, value):
            raise AssertionError("wrong native field must not be written")

    loop = N(observe_scene=lambda: object())
    monkeypatch.setattr(m, "current_dimension", lambda scene, key: "1000")
    monkeypatch.setattr(m, "_resolve_native_field", lambda scene, key: N(iface_value=Pattern()))

    result = replace_dimension_once(loop, field_name="width_1", desired=1500)
    assert result.status == "blocked"
    assert result.reason == "native_value_changed_since_observation"


def test_one_write_does_not_repeat_when_postcondition_fails(monkeypatch):
    from app.agent.runtime import windowhub_dimension_replace as m
    state = {"calls": 0, "scenes": 0}
    class Pattern:
        CurrentIsReadOnly = False
        CurrentValue = "1000"

        def SetValue(self, value):
            state["calls"] += 1
    def observe():
        state["scenes"] += 1
        return object()
    loop = N(observe_scene=observe)
    monkeypatch.setattr(m, "current_dimension", lambda scene, key: "1000")
    monkeypatch.setattr(m, "_resolve_native_field", lambda scene, key: N(iface_value=Pattern()))
    result = replace_dimension_once(loop, field_name="height_1", desired=1400)
    assert result.status == "blocked"
    assert result.reason == "post_write_readback_mismatch"
    assert state["calls"] == 1
    assert state["scenes"] == 4


def test_unobservable_field_does_not_write(monkeypatch):
    from app.agent.runtime import windowhub_dimension_replace as m
    monkeypatch.setattr(m, "current_dimension", lambda scene, key: None)
    monkeypatch.setattr(m, "_resolve_native_field",
        lambda scene, key: (_ for _ in ()).throw(AssertionError("should not resolve")))
    assert replace_dimension_once(
        N(observe_scene=lambda: object()), field_name="width_1", desired=1500
    ).status == "blocked"
