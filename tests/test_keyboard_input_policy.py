import pytest

from app.runtime.execution.keyboard.keyboard_input_policy import (
    SAFE_KEY_SEQUENCES,
    normalize_keyboard_sequence,
)


@pytest.mark.parametrize("sequence", SAFE_KEY_SEQUENCES)
def test_keyboard_policy_accepts_only_documented_navigation_sequences(sequence):
    assert normalize_keyboard_sequence(sequence)


@pytest.mark.parametrize(
    "sequence",
    [
        "alt+f4",
        "ctrl+alt+delete",
        "win+l",
        "delete",
        "backspace",
        "enter",
        "ctrl+shift+escape",
        "ctrl+q",
        "",
    ],
)
def test_keyboard_policy_rejects_destructive_or_unapproved_sequences(sequence):
    with pytest.raises(ValueError):
        normalize_keyboard_sequence(sequence)
