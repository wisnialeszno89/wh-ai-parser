from app.agent.agent_action import AgentAction

from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
)


def test_action_without_environment_requirement():

    action = AgentAction(
        name="test",
        description="Test action",
    )

    assert (
        action.environment_requirement
        is None
    )


def test_action_can_define_environment_requirement():

    requirement = EnvironmentRequirement(
        application="WindowHelper",
        requires_focus=True,
    )

    action = AgentAction(
        name="create_quote",
        description=(
            "Create a customer quote."
        ),
        environment_requirement=requirement,
    )

    assert (
        action.environment_requirement
        == requirement
    )


def test_action_preserves_environment_requirement_fields():

    action = AgentAction(
        name="edit_quote",
        description=(
            "Edit an existing quote."
        ),
        environment_requirement=(
            EnvironmentRequirement(
                application="WindowHelper",
                window_title="Customer Quote",
                requires_focus=True,
            )
        ),
    )

    requirement = (
        action.environment_requirement
    )

    assert requirement is not None

    assert (
        requirement.application
        == "WindowHelper"
    )

    assert (
        requirement.window_title
        == "Customer Quote"
    )

    assert (
        requirement.requires_focus
        is True
    )
