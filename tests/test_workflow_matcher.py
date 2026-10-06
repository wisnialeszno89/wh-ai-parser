from app.agent.learning.learned_workflow import LearnedWorkflow
from app.agent.learning.workflow_matcher import WorkflowMatcher


def _workflow(workflow_id, name, trigger, application="WindowHub"):
    return LearnedWorkflow(
        workflow_id=workflow_id,
        name=name,
        application=application,
        trigger=trigger,
        steps=(),
    )


def test_exact_trigger_is_top_match():
    workflows = (
        _workflow("wf-1", "Dodanie okna", "dodaj nowe okno"),
        _workflow("wf-2", "Dodanie drzwi", "dodaj nowe drzwi"),
    )

    matches = WorkflowMatcher().match(
        "Dodaj nowe okno",
        workflows,
        application="WindowHub",
    )

    assert matches
    assert matches[0].workflow.workflow_id == "wf-1"
    assert matches[0].score == 1.0


def test_matcher_handles_polish_diacritics():
    workflow = _workflow(
        "wf-1",
        "Zapisz ofertę",
        "zapisz ofertę",
    )

    matches = WorkflowMatcher().match(
        "zapisz oferte",
        (workflow,),
    )

    assert matches[0].workflow.workflow_id == "wf-1"


def test_matcher_filters_by_application():
    workflows = (
        _workflow("wf-1", "Dodanie okna", "dodaj nowe okno", "WindowHub"),
        _workflow("wf-2", "Dodanie okna", "dodaj nowe okno", "OtherApp"),
    )

    matches = WorkflowMatcher().match(
        "dodaj nowe okno",
        workflows,
        application="WindowHub",
    )

    assert [item.workflow.workflow_id for item in matches] == ["wf-1"]


def test_matcher_returns_none_below_threshold():
    workflow = _workflow(
        "wf-1",
        "Zapisz ofertę",
        "zapisz ofertę",
    )

    assert WorkflowMatcher().best_match(
        "sprawdź pogodę",
        (workflow,),
        min_score=0.55,
    ) is None
