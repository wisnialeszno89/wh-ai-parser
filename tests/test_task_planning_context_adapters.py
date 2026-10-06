from app.agent.reasoning.task_planning_context import TaskPlanningContext


def test_task_planning_context_serializes_adapter_descriptors():
    context = TaskPlanningContext(
        request_message="read a file",
        intent="computer_use",
        adapters=(
            {
                "adapter_id": "filesystem",
                "application": "FileSystem",
                "capabilities": ("list", "read"),
            },
        ),
    )

    payload = context.to_payload()

    assert payload["adapters"][0]["adapter_id"] == "filesystem"
    assert payload["adapters"][0]["capabilities"] == ("list", "read")
