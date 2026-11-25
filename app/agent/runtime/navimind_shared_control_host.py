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


@dataclass(frozen=True)
class VerifiedWorkflowScope:
    """Identity of a wizard reached by verified native input from pinned OFR."""
    document_key: str
    revision: int
    stage: str
    title: str
    hwnd: int


_PINNED_WIZARD_STAGES = frozenset({
    "position", "dimensions", "basic_parameters", "glazing",
    "hardware", "modifier", "document_properties",
})


def verify_workflow_scope(scene: Any, scope: VerifiedWorkflowScope | None,
                          *, expected_offer: str, revision: int) -> HostObservation:
    """Never recognize an arbitrary dialog by its title alone."""
    if (scope is None or scope.document_key != expected_offer
            or scope.revision != revision):
        return HostObservation(None, "verified_workflow_scope_missing", "unknown", False)
    try:
        from app.agent.learning.windowhub_demonstration import stage_of
        stage = stage_of(scene)
        state = scene.observation.state
        app = (state.active_application or "").replace(chr(92), "/").rsplit("/", 1)[-1].casefold()
        title = (state.active_window_title or "").strip()
        hwnd = (scene.observation.metadata or {}).get("window_handle")
        if (stage != scope.stage or stage not in _PINNED_WIZARD_STAGES
                or app != "okna.exe" or title != scope.title
                or type(hwnd) is not int or hwnd != scope.hwnd):
            return HostObservation(None, "verified_workflow_dialog_changed",
                                   stage or "unknown", False)
        return HostObservation(expected_offer, "verified_pinned_workflow_dialog", stage, True)
    except (AttributeError, TypeError, ValueError, KeyError):
        return HostObservation(None, "verified_workflow_dialog_unreadable", "unknown", False)


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
        from app.agent.runtime.navimind_draft_bootstrap import DRAFT_DOCUMENT_KEY
        self._draft_phase = (
            "start" if self.expected_offer == DRAFT_DOCUMENT_KEY else None
        )
        self.draft_document_bound_callback: Callable[[str], bool] | None = None
        self.draft_unnumbered_ready_callback: Callable[[], bool] | None = None
        self._draft_native_scope: Any = None
        self.controller = controller or NaviMindPanelController()
        self.controller.connect_host()
        self._accepted_scene: Any = None
        self.last_reason = "human_control_default"
        self._approved_work_revision: int | None = None
        self._workflow_scope: VerifiedWorkflowScope | None = None
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
        if (self.chat.snapshot().requires_replan
                and self._approved_work_revision
                != self.chat.snapshot().mission_revision):
            return HostObservation(None, "chat_instruction_requires_approved_replan",
                                   "unknown", False)
        result = verify_offer_observation(scene, self.expected_offer)
        if self._draft_phase is not None:
            from app.agent.runtime.navimind_draft_bootstrap import (
                DRAFT_DOCUMENT_KEY, verify_draft_start, draft_offer_candidate,
            )
            if self._draft_phase == "start":
                check = verify_draft_start(scene)
                result = HostObservation(
                    DRAFT_DOCUMENT_KEY if check.valid else None,
                    check.reason, check.stage, check.valid,
                )
            elif self._draft_phase == "awaiting_customer_selection":
                # Exactly one native new-document transaction must link
                # Start1, properties, customer and now the selected offer.
                # Unsaved offers may open the position wizard BEFORE
                # WindowHub allocates any OFR number.
                from app.agent.runtime.navimind_draft_bootstrap import (
                    verified_new_offer_from_native_transaction,
                    verified_unnumbered_position_from_native_transaction,
                )
                candidate = verified_new_offer_from_native_transaction(
                    scene, self._draft_native_scope,
                )
                if (candidate is not None
                        and self.draft_document_bound_callback is not None
                        and self.draft_document_bound_callback(candidate)):
                    self.expected_offer = candidate
                    self.chat.document_key = candidate
                    self._draft_phase = None
                    self._draft_native_scope = None
                    self._workflow_scope = None
                    result = verify_offer_observation(scene, candidate)
                elif (
                    verified_unnumbered_position_from_native_transaction(
                        scene, self._draft_native_scope, entry=True,
                    )
                    and self.draft_unnumbered_ready_callback is not None
                    and self.draft_unnumbered_ready_callback()
                ):
                    self._draft_phase = "unsaved_position"
                    self._workflow_scope = VerifiedWorkflowScope(
                        DRAFT_DOCUMENT_KEY,
                        self.chat.snapshot().mission_revision,
                        "position",
                        (scene.observation.state.active_window_title or "").strip(),
                        scene.observation.metadata["window_handle"],
                    )
                    result = HostObservation(
                        DRAFT_DOCUMENT_KEY, "verified_native_unsaved_position",
                        "position", True,
                    )
                else:
                    result = HostObservation(
                        None, "draft_customer_or_new_offer_not_verified",
                        "unknown", False,
                    )
            elif self._draft_phase == "properties":
                result = verify_workflow_scope(
                    scene, self._workflow_scope,
                    expected_offer=DRAFT_DOCUMENT_KEY,
                    revision=self.chat.snapshot().mission_revision,
                )
                if result.stage != "document_properties":
                    result = HostObservation(
                        None, "draft_properties_scope_required", "unknown", False,
                    )
            elif self._draft_phase == "unsaved_position":
                from app.agent.runtime.navimind_draft_bootstrap import (
                    verified_unnumbered_position_from_native_transaction,
                )
                follows = (
                    self._workflow_scope.hwnd
                    if self._workflow_scope is not None else None
                )
                if verified_unnumbered_position_from_native_transaction(
                    scene, self._draft_native_scope,
                    previous_hwnd=follows,
                ):
                    from app.agent.learning.windowhub_demonstration import stage_of
                    current_stage = stage_of(scene)
                    self._workflow_scope = VerifiedWorkflowScope(
                        DRAFT_DOCUMENT_KEY,
                        self.chat.snapshot().mission_revision,
                        current_stage,
                        (scene.observation.state.active_window_title or "").strip(),
                        scene.observation.metadata["window_handle"],
                    )
                    result = HostObservation(
                        DRAFT_DOCUMENT_KEY, "native_unsaved_draft_wizard",
                        current_stage, True,
                    )
                else:
                    result = HostObservation(
                        None, "draft_native_wizard_changed", "unknown", False,
                    )
        elif not result.verified:
            result = verify_workflow_scope(
                scene, self._workflow_scope,
                expected_offer=self.expected_offer,
                revision=self.chat.snapshot().mission_revision,
            )
        self.last_reason = result.reason
        if not result.verified:
            return result
        self._accepted_scene = scene
        self.controller.confirm_verified_resume(
            verified_document_key=result.document_key,
            verified_from_fresh_scene=True,
        )
        return result

    def note_verified_workflow_step(self, scene: Any, *, revision: int) -> bool:
        """Store exact dialog identity only after V2 verified an action."""
        if (revision != self._approved_work_revision
                or revision != self.chat.snapshot().mission_revision):
            return False
        try:
            from app.agent.learning.windowhub_demonstration import stage_of
            stage = stage_of(scene)
            if stage == "offer_document":
                proof = verify_offer_observation(scene, self.expected_offer)
                if not proof.verified:
                    return False
                self._workflow_scope = None
                return True
            if stage not in _PINNED_WIZARD_STAGES:
                return False
            if self._draft_phase == "unsaved_position":
                from app.agent.runtime.navimind_draft_bootstrap import (
                    verified_unnumbered_position_from_native_transaction,
                )
                follows = (
                    self._workflow_scope.hwnd
                    if self._workflow_scope is not None else None
                )
                if not verified_unnumbered_position_from_native_transaction(
                    scene, self._draft_native_scope,
                    previous_hwnd=follows,
                ):
                    return False
            state = scene.observation.state
            app = (state.active_application or "").replace(chr(92), "/").rsplit("/", 1)[-1].casefold()
            title = (state.active_window_title or "").strip()
            hwnd = (scene.observation.metadata or {}).get("window_handle")
            if (app != "okna.exe" or not title or type(hwnd) is not int
                    or hwnd <= 0):
                return False
            self._workflow_scope = VerifiedWorkflowScope(
                self.expected_offer, revision, stage, title, hwnd
            )
            return True
        except (AttributeError, TypeError, ValueError, KeyError):
            return False

    def approve_current_work_for_resume(self, *, revision: int,
                                        task_id: str, coordinator: Any) -> bool:
        """Called only on a local operator resume click, never by the model."""
        item = coordinator.current()
        if (item is None or not coordinator.is_current(item)
                or item.revision != revision
                or item.task_id != task_id
                or self.chat.snapshot().mission_revision != revision
                or item.document_key != self.expected_offer):
            return False
        from app.agent.runtime.navimind_work_mission import WorkStage
        if item.stage not in {WorkStage.READY, WorkStage.PAUSED}:
            return False
        allowed_pauses = {"one_native_step_verified_reobserve_next"}
        if self._draft_phase == "awaiting_customer_selection":
            allowed_pauses.add("draft_customer_selection_required")
        if self._draft_phase == "unsaved_position":
            allowed_pauses.add("one_native_step_verified_reobserve_next")
        if (item.stage == WorkStage.PAUSED
                and item.reason not in allowed_pauses):
            return False
        self._approved_work_revision = revision
        return True

    def pause_for_draft_customer(self) -> None:
        """Release native input while retaining read-only Start1 provenance.

        Called only after verified picker opening; user manually identifies
        the customer. Any later manual Takeover/revoke destroys ancestry.
        """
        if (self._draft_phase != "awaiting_customer_selection"
                or self._draft_native_scope is None):
            self.takeover()
            return
        self._approved_work_revision = None
        self.controller.takeover()
        self._accepted_scene = None
        self._workflow_scope = None
        self.last_reason = "manual_customer_selection_pending"

    def takeover(self) -> None:
        self._approved_work_revision = None
        self._workflow_scope = None
        # Explicit manual takeover or PDF revocation invalidates all draft
        # ancestry. Only the controlled picker handoff may retain it.
        self._draft_native_scope = None
        self.controller.takeover()
        self._accepted_scene = None
        self.last_reason = "human_takeover"

    def stop(self) -> None:
        self._approved_work_revision = None
        self._workflow_scope = None
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

    def execute_draft_start_once(self, loop: Any, *, revision: int):
        """Native Start1 action under the identical single-use input arbiter."""
        from app.agent.runtime.navimind_draft_bootstrap import (
            safe_native_start_action,
        )
        return safe_native_start_action(loop, self, mission_revision=revision)

    def execute_draft_customer_picker_once(self, loop: Any, *, revision: int):
        """Open exact known picker, never guess or mutate a customer record."""
        from app.agent.runtime.navimind_draft_bootstrap import (
            safe_native_open_customer_picker,
        )
        return safe_native_open_customer_picker(
            loop, self, mission_revision=revision,
        )

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
        if self._approved_work_revision != self.chat.snapshot().mission_revision:
            raise InputDenied("work_mission_revision_not_operator_approved")
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
                proof = verify_workflow_scope(
                    scene, self._workflow_scope,
                    expected_offer=self.expected_offer,
                    revision=self.chat.snapshot().mission_revision,
                )
            if not proof.verified:
                raise InputDenied(proof.reason)
            return execute_v2_step(
                loop, scene, resolved,
                approved_persistent=approved_persistent,
                expected_offer=(self.expected_offer
                                if proof.stage == "offer_document" else None),
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
