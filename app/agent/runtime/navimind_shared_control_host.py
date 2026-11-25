"""Single-process NaviMind panel/agent host, initially read-only.

The host shares one panel controller and arbiter. A verified WindowHub scene
may release a waiting mission; it does not itself permit GUI automation.
All actual agent input must be routed through guarded_dispatch() by a future
trusted V2 integration; the initial desktop launcher NEVER executes input.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from app.agent.runtime.navimind_local_input_arbiter import InputDenied
from app.agent.runtime.navimind_mission_chat import MissionChat
from app.agent.runtime.navimind_panel_controller import NaviMindPanelController, PanelMode
from app.agent.runtime.navimind_v2_preaction_scene_guard import (
    compare_preaction_scenes,
)


@dataclass(frozen=True)
class HostObservation:
    document_key: str | None
    reason: str
    stage: str
    verified: bool


def verify_offer_observation(scene: Any, expected_offer: str) -> HostObservation:
    """Read only, require exact OFR title, unique selected tab and WindowHub."""
    if not isinstance(expected_offer, str) or not expected_offer.strip():
        return HostObservation(None, "expected_offer_required", "unknown", False)
    try:
        from app.agent.learning.windowhub_demonstration import stage_of
        from app.agent.runtime.active_document_scope import selected_document_tab
        from app.agent.runtime.windowhub_mdi_native_probe import same_offer_id
        stage = stage_of(scene) or "unknown"
        app = (scene.observation.state.active_application or "").replace(
            "\\", "/"
        ).rsplit("/", 1)[-1].casefold()
        title = (scene.observation.state.active_window_title or "").strip()
        selected, selected_reason = selected_document_tab(scene)
        if app != "okna.exe" or stage != "offer_document":
            return HostObservation(None, "windowhub_offer_not_foreground", stage, False)
        if not title.casefold().startswith("okna - ofr/"):
            return HostObservation(None, "offer_title_unverified", stage, False)
        observed_id = title[len("Okna - "):]
        if not (same_offer_id(observed_id, expected_offer)
                and selected is not None
                and same_offer_id(selected, expected_offer)):
            return HostObservation(None, "selected_offer_not_exactly_verified",
                                   stage, False)
        hwnd = (scene.observation.metadata or {}).get("window_handle")
        if type(hwnd) is not int or hwnd <= 0:
            return HostObservation(None, "foreground_window_handle_unverified",
                                   stage, False)
        return HostObservation(expected_offer, "verified_exact_selected_offer", stage, True)
    except (AttributeError, ValueError, TypeError, KeyError):
        return HostObservation(None, "offer_scene_unreadable", "unknown", False)


class NaviMindSharedHost:
    """Read-only stage for actual Windows: one arbiter and one panel.

    Accepting an observation is NOT a promise of action safety. Immediately
    before every future live action, guarded_dispatch() must reobserve and
    compare current UI, then use the same shared arbiter at native dispatch.
    """

    def __init__(self, expected_offer: str,
                 controller: NaviMindPanelController | None = None):
        if not isinstance(expected_offer, str) or not expected_offer.strip():
            raise ValueError("expected_offer_required")
        self.expected_offer = expected_offer.strip()
        self.controller = controller or NaviMindPanelController()
        self.controller.connect_host()
        self._accepted_scene: Any = None
        self.last_reason = "human_control_default"
        self.chat = MissionChat(
            document_key=self.expected_offer,
            arbiter=self.controller.arbiter,
            on_takeover=self.takeover,
        )

    def release_for_reobservation(self) -> None:
        self._accepted_scene = None
        self.controller.resume()
        self.last_reason = "fresh_offer_observation_required"

    def inspect_fresh_scene(self, scene: Any) -> HostObservation:
        """Host receives fresh observer data; no operation is executed."""
        if self.controller.snapshot().mode != PanelMode.RESUME_PENDING:
            return HostObservation(None, "agent_not_waiting_for_observation",
                                   "unknown", False)
        # A user message is not merely a pause: it creates a new mission
        # revision. Re-observing the same offer cannot authorize an old plan.
        if self.chat.snapshot().requires_replan:
            return HostObservation(None, "chat_instruction_requires_approved_replan",
                                   "unknown", False)
        result = verify_offer_observation(scene, self.expected_offer)
        self.last_reason = result.reason
        if not result.verified:
            return result
        self._accepted_scene = scene
        self.controller.confirm_verified_resume(
            verified_document_key=result.document_key,
            verified_from_fresh_scene=True,
        )
        return result

    def takeover(self) -> None:
        self.controller.takeover()
        self._accepted_scene = None
        self.last_reason = "human_takeover"

    def stop(self) -> None:
        self.controller.stop()
        self._accepted_scene = None
        self.last_reason = "task_cancelled"

    def research_price_for_chat(
        self, *, human_message_id: int, request: Any,
        provider: Any = None, today: date | None = None,
    ) -> Any:
        """Trusted host integration: public research remains advisory only.

        Deliberately does NOT alter the arbiter, resume the agent or write
        a quotation. Without a configured provider, it returns an honest
        unavailable report to the same local mission chat.
        """
        from app.agent.runtime.navimind_price_search_workflow import (
            publish_research_to_chat, search_price_for_current_chat,
        )
        if self.controller.snapshot().mode == PanelMode.STOPPED:
            raise ValueError("stopped_mission_cannot_research")
        report = search_price_for_current_chat(
            chat=self.chat,
            human_message_id=human_message_id,
            request=request,
            provider=provider,
            today=today if today is not None else date.today(),
        )
        publish_research_to_chat(self.chat, report)
        return report

    def propose_amendment_from_chat(
        self, *, human_message_id: int, position_evidence: Any,
    ) -> Any:
        """Review-only, typed correction from a pinned chat message.

        The caller must supply real independently observed position evidence.
        This entrypoint never turns a model reply into a native operation.
        """
        from app.agent.runtime.navimind_chat_amendment_bridge import (
            prepare_amendment,
        )
        if self.controller.snapshot().mode == PanelMode.STOPPED:
            raise ValueError("stopped_mission_cannot_stage_amendment")
        return prepare_amendment(
            self.chat, message_id=human_message_id,
            evidence=position_evidence,
        )

    def guarded_dispatch(self, loop: Any, operation: Callable[[], Any]) -> Any:
        """Future V2 bridge: reobserve + check document + arbiter dispatch.

        Not invoked by the initial UI launcher. It requires one existing
        accepted snapshot, and does not create an authorization from a
        document string supplied by the user.
        """
        permit = self.controller.current_permit()
        if permit is None or self._accepted_scene is None:
            raise InputDenied("no_shared_host_agent_permission")
        fresh = loop.observe_scene()
        proof = verify_offer_observation(fresh, self.expected_offer)
        if not proof.verified:
            self.controller.arbiter.invalidate_observation()
            self._accepted_scene = None
            raise InputDenied("exact_offer_changed_before_dispatch")
        comparison = compare_preaction_scenes(self._accepted_scene, fresh)
        if not comparison.safe:
            self.controller.arbiter.invalidate_observation()
            self._accepted_scene = None
            raise InputDenied(comparison.reason)
        return self.controller.arbiter.dispatch(permit, operation)

    def execute_one_verified_v2_action(
        self, loop: Any, resolved: Any, *, approved_persistent: bool = False,
    ) -> Any:
        """Native V2 bridge: exactly one preapproved step, with local arbiter.

        This is for a trusted local task coordinator, not a remote model
        tool. The operator must already have resumed the exact OFR document.
        The permit is consumed whether execution succeeds or fails; the next
        step requires a new observation and human ownership handshake.
        """
        permit = self.controller.current_permit()
        baseline = self._accepted_scene
        if permit is None or baseline is None:
            raise InputDenied("no_shared_host_agent_permission")
        if permit.document_key != self.expected_offer:
            raise InputDenied("v2_offer_permit_mismatch")
        from app.agent.runtime.navimind_v2_preaction_scene_guard import (
            verify_preaction_scene,
        )
        from app.agent.runtime.windowhub_goal_v2_coordinator import (
            execute_v2_step,
        )
        try:
            comparison, scene = verify_preaction_scene(loop, baseline)
            if not comparison.safe:
                raise InputDenied(comparison.reason)
            proof = verify_offer_observation(scene, self.expected_offer)
            if not proof.verified:
                raise InputDenied(proof.reason)
            return execute_v2_step(
                loop, scene, resolved,
                approved_persistent=approved_persistent,
                expected_offer=self.expected_offer,
                pre_model_scene=baseline,
                input_arbiter=self.controller.arbiter,
                input_permit=permit,
            )
        finally:
            # A newly created dialog, changed MDI state or human input makes
            # all old semantic references and permits stale.
            self.controller.arbiter.invalidate_observation()
            self._accepted_scene = None
            self.last_reason = "v2_step_requires_fresh_reobservation"
