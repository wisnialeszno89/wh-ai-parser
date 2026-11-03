from types import SimpleNamespace

import pytest

from app.agent.experience.experience_models import (
    ExperienceEpisode,
    ExperienceStep,
)
from app.agent.experience.experience_retriever import ExperienceRetriever
from app.agent.experience.experience_store import ExperienceStore
from app.agent.experience.guided_learning_service import GuidedLearningService
from app.agent.experience.offer_learning_adapter import record_offer_context
from app.agent.offers.offer_context import OfferContext
from app.agent.runtime.windows_desktop_v2_agent_runtime import (
    WindowsDesktopV2AgentRuntime,
)
from app.agent.runtime.windows_desktop_v2_agent_runtime_factory import (
    _create_experience_retriever,
)


def _step(
    *,
    action="click",
    target="new_offer_button",
    purpose="Open the new offer form",
    verification="The new offer form is visible",
):
    return ExperienceStep(
        action=action,
        target=target,
        purpose=purpose,
        verification=verification,
    )


def _learn_one(store, *, tenant="company-a", operator="operator-a", app="okna.exe"):
    service = GuidedLearningService(
        store=store,
        tenant_id=tenant,
        operator_id=operator,
    )
    session = service.begin(
        application_id=app,
        task_kind="create_window_offer",
        tags=("window_offer", "new_offer"),
    )
    session.record_step(_step())
    session.record_step(
        _step(
            action="select",
            target="profile_selector",
            purpose="Choose the requested window profile",
            verification="The selected profile is shown in the form",
        )
    )
    draft = service.complete(session, outcome="completed")
    return service, draft


def test_guided_learning_draft_is_not_saved_before_operator_approval(tmp_path):
    store = ExperienceStore(tmp_path)
    service, draft = _learn_one(store)

    assert draft.approved_by_operator is False
    assert store.list_approved(
        tenant_id="company-a",
        operator_id="operator-a",
        application_id="okna.exe",
    ) == ()

    with pytest.raises(
        ValueError,
        match="guided_learning_operator_approval_required",
    ):
        service.approve(draft, operator_confirmed=False)


def test_guided_learning_persists_only_after_explicit_operator_approval(tmp_path):
    store = ExperienceStore(tmp_path)
    service, draft = _learn_one(store)

    approved = service.approve(draft, operator_confirmed=True)
    restored = store.list_approved(
        tenant_id="company-a",
        operator_id="operator-a",
        application_id="okna.exe",
    )

    assert approved.approved_by_operator is True
    assert len(restored) == 1
    assert restored[0].episode_id == approved.episode_id
    assert len(restored[0].steps) == 2


def test_experience_memory_is_isolated_by_company_operator_and_application(tmp_path):
    store = ExperienceStore(tmp_path)
    service, draft = _learn_one(store)
    service.approve(draft, operator_confirmed=True)

    assert len(store.list_approved(
        tenant_id="company-a",
        operator_id="operator-a",
        application_id="okna.exe",
    )) == 1
    assert store.list_approved(
        tenant_id="company-b",
        operator_id="operator-a",
        application_id="okna.exe",
    ) == ()
    assert store.list_approved(
        tenant_id="company-a",
        operator_id="operator-b",
        application_id="okna.exe",
    ) == ()
    assert store.list_approved(
        tenant_id="company-a",
        operator_id="operator-a",
        application_id="excel.exe",
    ) == ()


def test_experience_retrieval_returns_only_approved_semantic_examples(tmp_path):
    store = ExperienceStore(tmp_path)
    service, draft = _learn_one(store)
    service.approve(draft, operator_confirmed=True)

    retriever = ExperienceRetriever(
        store=store,
        tenant_id="company-a",
        operator_id="operator-a",
    )
    records = retriever.retrieve(
        application_id="OKNA.EXE",
        goal="Create a new window offer",
        max_items=3,
    )

    assert len(records) == 1
    assert records[0]["application"] == "okna.exe"
    assert records[0]["task_kind"] == "create_window_offer"
    assert records[0]["steps"][0]["target"] == "new_offer_button"
    assert "tenant_id" not in records[0]
    assert "operator_id" not in records[0]
    assert "raw_request" not in records[0]


def test_experience_retrieval_never_crosses_application_scope(tmp_path):
    store = ExperienceStore(tmp_path)
    service, draft = _learn_one(store, app="okna.exe")
    service.approve(draft, operator_confirmed=True)

    retriever = ExperienceRetriever(
        store=store,
        tenant_id="company-a",
        operator_id="operator-a",
    )

    assert retriever.retrieve(
        application_id="excel.exe",
        goal="Create a window offer",
    ) == ()


def test_unapproved_episode_cannot_be_written_directly(tmp_path):
    store = ExperienceStore(tmp_path)
    _, draft = _learn_one(store)

    with pytest.raises(
        ValueError,
        match="experience_episode_requires_operator_approval",
    ):
        store.save_approved(draft)


def test_learning_rejects_non_semantic_or_unsafe_action_names():
    with pytest.raises(ValueError, match="experience_action_not_allowed"):
        _step(action="run_shell_command")


def test_learning_rejects_empty_demonstrations(tmp_path):
    service = GuidedLearningService(
        store=ExperienceStore(tmp_path),
        tenant_id="company-a",
        operator_id="operator-a",
    )
    session = service.begin(
        application_id="okna.exe",
        task_kind="create_window_offer",
    )

    with pytest.raises(ValueError, match="guided_learning_steps_required"):
        service.complete(session, outcome="completed")

    assert session.closed is False


def test_learning_session_cannot_be_completed_twice(tmp_path):
    service = GuidedLearningService(
        store=ExperienceStore(tmp_path),
        tenant_id="company-a",
        operator_id="operator-a",
    )
    session = service.begin(
        application_id="okna.exe",
        task_kind="create_window_offer",
    )
    session.record_step(_step())
    service.complete(session, outcome="completed")

    with pytest.raises(ValueError, match="guided_learning_session_closed"):
        service.complete(session, outcome="completed")


def test_v2_runtime_loads_experience_only_for_observed_application():
    calls = []

    class _Provider:
        def retrieve(self, **kwargs):
            calls.append(kwargs)
            return ({"task_kind": "create_window_offer"},)

    runtime = object.__new__(WindowsDesktopV2AgentRuntime)
    runtime.experience_provider = _Provider()
    scene = SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(active_application="Okna.exe")
        )
    )

    result = runtime._retrieve_experience(scene, "Create a window offer")

    assert result == ({"task_kind": "create_window_offer"},)
    assert calls == [{
        "application_id": "Okna.exe",
        "goal": "Create a window offer",
        "max_items": 3,
    }]


def test_v2_runtime_ignores_unavailable_experience_store():
    class _Provider:
        def retrieve(self, **_kwargs):
            raise RuntimeError("store unavailable")

    runtime = object.__new__(WindowsDesktopV2AgentRuntime)
    runtime.experience_provider = _Provider()
    scene = SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(active_application="Okna.exe")
        )
    )

    assert runtime._retrieve_experience(scene, "Create an offer") == ()


def test_experience_factory_requires_both_tenant_and_operator_scope(monkeypatch, tmp_path):
    monkeypatch.delenv("NAVIMIND_TENANT_ID", raising=False)
    monkeypatch.delenv("NAVIMIND_OPERATOR_ID", raising=False)
    monkeypatch.setenv("NAVIMIND_EXPERIENCE_DIR", str(tmp_path))

    assert _create_experience_retriever() is None

    monkeypatch.setenv("NAVIMIND_TENANT_ID", "company-a")
    assert _create_experience_retriever() is None

    monkeypatch.setenv("NAVIMIND_OPERATOR_ID", "operator-a")
    retriever = _create_experience_retriever()

    assert isinstance(retriever, ExperienceRetriever)



def test_offer_learning_adapter_keeps_only_normalized_technical_fields(tmp_path):
    store = ExperienceStore(tmp_path)
    service = GuidedLearningService(
        store=store,
        tenant_id="company-a",
        operator_id="operator-a",
    )
    session = service.begin(
        application_id="okna.exe",
        task_kind="create_window_offer",
        tags=("window_offer",),
    )
    context = OfferContext(
        raw_request="Offer for Max Mustermann, private address removed from memory",
        width=1500,
        height=1400,
        quantity=1,
        product_type="window",
        profile="profile-82",
        configuration="double_leaf",
        opening="right_tilt_turn",
        openings=("left_fixed", "right_tilt_turn"),
        color_inside="white",
        color_outside="anthracite",
        glazing="triple",
    )

    facts = record_offer_context(session, context)
    session.record_step(_step())
    draft = service.complete(session, outcome="completed")
    approved = service.approve(draft, operator_confirmed=True)
    retriever = ExperienceRetriever(
        store=store,
        tenant_id="company-a",
        operator_id="operator-a",
    )
    result = retriever.retrieve(
        application_id="okna.exe",
        goal="Create window offer",
    )

    assert {fact.key for fact in facts} == {
        "width",
        "height",
        "quantity",
        "product_type",
        "profile",
        "configuration",
        "opening",
        "openings",
        "color_inside",
        "color_outside",
        "glazing",
    }
    assert approved.facts
    assert result[0]["example_facts"]["width"] == 1500
    assert result[0]["example_facts"]["height"] == 1400
    assert result[0]["example_facts"]["glazing"] == "triple"
    assert result[0]["evidence_type"] == (
        "approved_demonstration_example_not_a_universal_rule"
    )
    serialized = str(approved.to_storage_dict())
    assert "Max Mustermann" not in serialized
    assert "raw_request" not in serialized


def test_offer_learning_adapter_omits_missing_and_conflicting_fields():
    from app.agent.experience.offer_learning_adapter import (
        facts_from_offer_context,
    )

    context = OfferContext(
        raw_request="Some customer text that must not be retained",
        width=1200,
        height=None,
        product_type="window",
        color_outside=None,
        glazing="triple",
    )

    facts = facts_from_offer_context(context)
    by_key = {fact.key: fact.value for fact in facts}

    assert by_key == {
        "width": 1200,
        "quantity": 1,
        "product_type": "window",
        "glazing": "triple",
    }
