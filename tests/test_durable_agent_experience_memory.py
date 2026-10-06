from app.agent.agent_request import AgentRequest
from app.agent.learning.agent_mode import AgentMode
from app.agent.memory.agent_memory import AgentExperience, AgentMemoryRepository
from app.agent.memory.agent_memory_store import AgentMemoryStore


def test_agent_experience_round_trip():
    experience = AgentExperience(
        experience_id="exp-1",
        kind="runtime_execution",
        application="WindowHub",
        intent="create_quote",
        workflow_id=None,
        outcome="success",
        summary="Executed a semantic plan.",
        created_at="2026-10-06T12:00:00+00:00",
        metadata={"executed_actions": 3},
    )

    restored = AgentExperience.from_payload(
        experience.to_payload()
    )

    assert restored == experience


def test_agent_memory_repository_persists_experience(tmp_path):
    repository = AgentMemoryRepository(tmp_path / "memory")
    experience = AgentExperience(
        experience_id="exp-2",
        kind="learned_workflow_replay",
        application="WindowHub",
        intent="observe_workflow",
        workflow_id="wf-1",
        outcome="success",
        summary="Replayed learned workflow.",
        created_at="2026-10-06T12:01:00+00:00",
        metadata={"parameter_names": ["szerokosc"]},
    )

    repository.save(experience)

    assert repository.get("exp-2") == experience
    assert repository.all() == (experience,)


def test_agent_memory_store_loads_and_orders_persisted_experiences(tmp_path):
    repository = AgentMemoryRepository(tmp_path / "memory")
    first = AgentMemoryStore(
        repository=repository,
        load_persisted=False,
    )

    first.add(
        AgentExperience(
            experience_id="exp-a",
            kind="runtime_execution",
            application="WindowHub",
            intent="create_quote",
            workflow_id=None,
            outcome="failure",
            summary="Plan failed.",
            created_at="2026-10-06T12:00:00+00:00",
        )
    )
    first.add(
        AgentExperience(
            experience_id="exp-b",
            kind="runtime_execution",
            application="WindowHub",
            intent="create_quote",
            workflow_id=None,
            outcome="success",
            summary="Plan completed.",
            created_at="2026-10-06T12:02:00+00:00",
        )
    )

    second = AgentMemoryStore(
        repository=repository,
        load_persisted=True,
    )

    recent = second.recent(
        application="WindowHub",
        limit=2,
    )

    assert [item.experience_id for item in recent] == [
        "exp-b",
        "exp-a",
    ]
