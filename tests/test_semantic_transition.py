from app.agent.learning.semantic_snapshot import SemanticSnapshot
from app.agent.learning.semantic_transition import SemanticTransition


def test_transition_prefers_state_changes_over_ui_noise():
    before = SemanticSnapshot(
        application="WindowHub",
        window_title="Okna -",
        elements=(
            {
                "kind": "radiobutton",
                "label": "Okno",
                "uia_selected": False,
            },
        ),
    )
    after = SemanticSnapshot(
        application="WindowHub",
        window_title="Dodawanie nowej pozycji",
        elements=(
            {
                "kind": "radiobutton",
                "label": "Okno",
                "uia_selected": True,
            },
            {"kind": "button", "label": "Dalej >"},
            {"kind": "button", "label": "Wstecz"},
            {"kind": "text", "label": "implementation detail"},
        ),
    )

    transition = SemanticTransition.from_snapshots(before, after)

    assert transition.window_title == "Dodawanie nowej pozycji"
    assert transition.requirements == (
        {
            "kind": "radiobutton",
            "label": "Okno",
            "uia_selected": True,
        },
        {
            "kind": "button",
            "label": "Dalej >",
        },
        {
            "kind": "button",
            "label": "Wstecz",
        },
    )


def test_transition_caps_new_semantic_anchors():
    before = SemanticSnapshot(
        application="WindowHub",
        window_title="Start",
        elements=(),
    )
    after = SemanticSnapshot(
        application="WindowHub",
        window_title="Dialog",
        elements=tuple(
            {
                "kind": "button",
                "label": f"Button {index}",
            }
            for index in range(10)
        ),
    )

    transition = SemanticTransition.from_snapshots(
        before,
        after,
        max_requirements=3,
    )

    assert len(transition.requirements) == 3
    assert [item["label"] for item in transition.requirements] == [
        "Button 0",
        "Button 1",
        "Button 2",
    ]


def test_transition_round_trip():
    before = SemanticSnapshot(
        application="WindowHub",
        window_title="Before",
    )
    after = SemanticSnapshot(
        application="WindowHub",
        window_title="After",
        active_document="Dokument1",
        elements=(
            {
                "kind": "edit",
                "label": "Szerokość",
                "current_value": "1230",
            },
        ),
    )

    transition = SemanticTransition.from_snapshots(before, after)
    restored = SemanticTransition.from_payload(
        transition.to_payload()
    )

    assert restored == transition
