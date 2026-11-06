"""Customer skill is bounded, independently verified and feeds NaviMind."""
from types import SimpleNamespace

import tools.run_windowhub_goal_v2 as runner
import tools.run_windowhub_top_trans_single_window_mission as mission


class FakeLoop:
    def observe_scene(self):
        return SimpleNamespace(
            observation=SimpleNamespace(state=SimpleNamespace(
                active_application="Okna.exe",
                active_window_title="Właściwości dokumentu",
            )),
            elements=(),
        )


def test_customer_skill_refuses_model_when_result_unverified(monkeypatch, capsys):
    monkeypatch.setattr(runner, "enrich_windowhub_scene", lambda scene: scene)
    monkeypatch.setattr(runner, "stage_of", lambda scene: "document_properties")
    monkeypatch.setattr(mission, "customer_selected", lambda scene, name: False)
    monkeypatch.setattr(mission, "progressive_customer_selection",
                        lambda loop, scene, name: (False, "customer_not_verified"))

    class NoReasoner:
        def reason(self, request):
            raise AssertionError("Do not call model after unverified customer action")

    assert runner.run_goal(
        FakeLoop(), goal="New offer", reasoner=NoReasoner(),
        mode="execute", max_actions=3, customer_lookup_name="Top Trans",
    ) == 6
    assert "CUSTOMER_SKILL_STATUS=customer_not_verified" in capsys.readouterr().out


def test_verified_customer_skill_sends_feedback_into_fresh_v2_cycle(monkeypatch):
    monkeypatch.setattr(runner, "enrich_windowhub_scene", lambda scene: scene)
    monkeypatch.setattr(runner, "stage_of", lambda scene: "document_properties")
    monkeypatch.setattr(mission, "customer_selected", lambda scene, name: False)
    monkeypatch.setattr(mission, "progressive_customer_selection",
                        lambda loop, scene, name: (True, "CUSTOMER_VERIFIED_NATIVE_READBACK"))
    seen = {}

    class FakeSession:
        def prepare_cycle(self, scene, **kwargs):
            seen["experience"] = kwargs["experience"]
            seen["revision"] = kwargs["world_revision"]
            return SimpleNamespace(request_payload={"capabilities": {"actions": []}})

    class Reasoner:
        last_error = "intentional_test_stop"

        def reason(self, request):
            seen["model_called"] = True
            return None

    monkeypatch.setattr(runner, "ComputerUseV2ActionSession", FakeSession)
    assert runner.run_goal(
        FakeLoop(), goal="New offer", reasoner=Reasoner(),
        mode="execute", max_actions=3, customer_lookup_name="Top Trans",
    ) == 5
    assert seen["revision"] == 2
    assert seen["model_called"] is True
    assert seen["experience"][-1]["verified"] is True
    assert seen["experience"][-1]["action_type"] == "select_existing_customer"


def test_customer_skill_requires_explicit_mode_and_name():
    from tools.run_windowhub_goal_v2 import parse_args
    args = parse_args(["--customer-lookup-skill", "--customer-name", "Top Trans"])
    assert args.customer_lookup_skill is True
    assert args.customer_name == "Top Trans"
