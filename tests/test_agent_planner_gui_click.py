from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.planning.agent_planner import AgentPlanner


def test_planner_creates_semantic_click_action():
    plan = AgentPlanner().plan(
        AgentRequest(
            message="Kliknij przycisk Dalej.",
        )
    )

    assert plan.intent is AgentIntent.EXECUTE_IN_WH
    assert plan.requires_manual_review is False
    assert len(plan.steps) == 1

    action = plan.steps[0].action

    assert action.name == "click_screen_element"
    assert action.target == "Dalej"
    assert "coordinate" not in action.description.lower()
    assert "pyautogui" not in action.description.lower()


def test_planner_supports_semantic_click_without_button_word():
    plan = AgentPlanner().plan(
        AgentRequest(
            message="kliknij ustawienia",
        )
    )

    assert plan.intent is AgentIntent.EXECUTE_IN_WH
    assert plan.steps[0].action.name == "click_screen_element"
    assert plan.steps[0].action.target == "ustawienia"


def test_planner_does_not_turn_generic_text_into_click():
    plan = AgentPlanner().plan(
        AgentRequest(
            message="przygotuj wycenę okna 1230x1480",
        )
    )

    assert plan.intent is AgentIntent.CREATE_QUOTE
