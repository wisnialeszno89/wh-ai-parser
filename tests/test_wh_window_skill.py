from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.skills.wh_window_skill import (
    WHWindowSkill,
)


def test_wh_skill_supports_quote_intent():
    skill = WHWindowSkill()

    assert skill.supports(
        AgentIntent.CREATE_QUOTE
    )


def test_wh_skill_supports_execution_intent():
    skill = WHWindowSkill()

    assert skill.supports(
        AgentIntent.EXECUTE_IN_WH
    )


def test_wh_skill_does_not_support_word_intent():
    skill = WHWindowSkill()

    assert not skill.supports(
        AgentIntent.WRITE_CUSTOMER_REPLY
    )


def test_wh_skill_delegates_quote_planning():
    skill = WHWindowSkill()

    plan = skill.plan(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    assert plan.intent == (
        AgentIntent.CREATE_QUOTE
    )

    names = {
        step.action.name
        for step in plan.steps
    }

    assert "collect_offer_context" in names
    assert "validate_offer" in names
    assert "build_construction" in names
