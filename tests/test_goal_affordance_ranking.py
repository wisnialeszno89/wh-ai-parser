"""Goal relevance is only ranking, never an execution authorization."""
from types import SimpleNamespace as NS

from app.agent.runtime.goal_affordance_ranking import (
    normalize_words, relevance_score, order_observed_affordances,
)


class FakeReferenceMap:
    def resolve(self, ref, *, task_id, world_revision):
        return {
            "ref_template": NS(label="0001 Oferta bez cen", metadata={}),
            "ref_width": NS(label="Szerokość całego okna", metadata={}),
            "ref_color": NS(label="Wybierz kolor profili", metadata={}),
            "ref_edit": NS(label="Edytuj", metadata={}),
        }[ref]


def test_dimension_goal_ranks_width_ahead_of_unrelated_templates():
    list_of_actions = [
        {"entity_ref": "ref_template", "name": "click", "description": "Click visible control"},
        {"entity_ref": "ref_edit", "name": "click", "description": "Click visible control"},
        {"entity_ref": "ref_width", "name": "write_text", "description": "Enter data"},
        {"entity_ref": "ref_color", "name": "click", "description": "Click visible control"},
    ]
    ranked = order_observed_affordances(
        list_of_actions,
        goal="Zmień szerokość okna na 1500 mm",
        reference_map=FakeReferenceMap(),
        task_id="test", world_revision=1,
    )
    assert ranked[0]["entity_ref"] == "ref_width"
    assert len(ranked) == 4
    assert sorted(a["entity_ref"] for a in ranked) == sorted(
        a["entity_ref"] for a in list_of_actions
    )


def test_color_task_ranks_color_control_first():
    affordances = [
        {"entity_ref": "ref_template", "description": "Click"},
        {"entity_ref": "ref_color", "description": "Click"},
    ]
    ranked = order_observed_affordances(
        affordances, goal="Zmień kolor profili",
        reference_map=FakeReferenceMap(),
        task_id="x", world_revision=2,
    )
    assert ranked[0]["entity_ref"] == "ref_color"


def test_no_goal_overlap_keeps_observed_order():
    affordances = [
        {"entity_ref": "ref_template", "description": "Click"},
        {"entity_ref": "ref_width", "description": "Click"},
    ]
    ranked = order_observed_affordances(
        affordances, goal="Czynność niestandardowa",
        reference_map=FakeReferenceMap(),
        task_id="x", world_revision=2,
    )
    assert ranked == affordances


def test_normalization_of_polish_diacritics():
    assert "szerokosc" in normalize_words("Szerokość")
    assert relevance_score(
        "ustaw szerokość", label="Szerokość całego okna"
    ) > relevance_score(
        "ustaw szerokość", label="Zestaw nagłówek/stopka"
    )
