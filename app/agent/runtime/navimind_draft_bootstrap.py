"""One authorized, native WindowHub Start1 -> unsaved offer workflow.

Separate from editing an existing OFR: a new document has no number yet.
This module never invents an OFR, commits customer data, saves or sends.
The operator must explicitly start the live mission; every UI action is
routed through the shared host input arbiter and checked after execution.
"""
from __future__ import annotations

from dataclasses import dataclass

DRAFT_DOCUMENT_KEY = "DRAFT/NEW"
START_TITLE = "Okna - Start1"
PROPERTIES_TITLE = "Właściwości dokumentu"


@dataclass(frozen=True)
class DraftProof:
    valid: bool
    stage: str
    reason: str
    hwnd: int | None = None


def verify_draft_start(scene) -> DraftProof:
    """Pin a real foreground Start1; no generic WindowHub title matches."""
    try:
        from app.agent.learning.windowhub_demonstration import stage_of
        state = scene.observation.state
        app = (state.active_application or "").replace(chr(92), "/").rsplit("/", 1)[-1].casefold()
        title = (state.active_window_title or "").strip()
        hwnd = (scene.observation.metadata or {}).get("window_handle")
        if (app != "okna.exe" or title != START_TITLE
                or stage_of(scene) != "start"
                or type(hwnd) is not int or hwnd <= 0):
            return DraftProof(False, "unknown", "draft_start_not_verified")
        # A matching caption is not sufficient to invoke any button. The
        # native resolver rechecks the exact UIA control before dispatch.
        return DraftProof(True, "start", "verified_foreground_start1", hwnd)
    except (TypeError, ValueError, AttributeError, KeyError):
        return DraftProof(False, "unknown", "draft_start_observation_invalid")


def verify_draft_properties(scene, *, prior_hwnd: int | None = None) -> DraftProof:
    """Verify one real WindowHub document-properties dialog after Invoke."""
    try:
        from app.agent.learning.windowhub_demonstration import stage_of
        state = scene.observation.state
        app = (state.active_application or "").replace(chr(92), "/").rsplit("/", 1)[-1].casefold()
        title = (state.active_window_title or "").strip()
        hwnd = (scene.observation.metadata or {}).get("window_handle")
        if (app != "okna.exe" or title != PROPERTIES_TITLE
                or stage_of(scene) != "document_properties"
                or type(hwnd) is not int or hwnd <= 0
                or (type(prior_hwnd) is int and hwnd == prior_hwnd)):
            return DraftProof(False, "unknown", "draft_properties_not_verified")
        return DraftProof(True, "document_properties", "verified_document_properties", hwnd)
    except (TypeError, ValueError, AttributeError, KeyError):
        return DraftProof(False, "unknown", "draft_properties_unreadable")


def draft_offer_candidate(scene) -> str | None:
    """Identify, never assert creation: an OFR with exact selected MDI tab."""
    try:
        from app.agent.runtime.navimind_shared_control_host import verify_offer_observation
        title = (scene.observation.state.active_window_title or "").strip()
        if not title.casefold().startswith("okna - ofr/"):
            return None
        observed_id = title[len("Okna - "):]
        if verify_offer_observation(scene, observed_id).verified:
            return observed_id
    except (AttributeError, ValueError, TypeError, KeyError):
        pass
    return None



def verified_new_offer_from_native_transaction(scene, handoff, *, native_api=None) -> str | None:
    """Native MDI provenance AND exact visible selected OFR are required."""
    if handoff is None:
        return None
    candidate = draft_offer_candidate(scene)
    if candidate is None:
        return None
    try:
        from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi
        api = native_api if native_api is not None else _Win32Mdi()
        source = handoff.verify(scene, api)
        if source != "native_offer":
            return None
        from app.agent.runtime.windowhub_mdi_native_probe import same_offer_id
        if not same_offer_id(handoff.offer, candidate):
            return None
        return candidate
    except Exception:
        return None


def verified_unnumbered_position_from_native_transaction(
    scene, handoff, *, native_api=None, entry: bool = False,
    previous_hwnd: int | None = None,
) -> bool:
    """Verify position editor as a child of THIS new-offer transaction."""
    if handoff is None:
        return False
    try:
        from app.agent.learning.windowhub_demonstration import stage_of
        from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi
        if stage_of(scene) not in {
            "position", "dimensions", "basic_parameters",
            "glazing", "hardware", "modifier",
        }:
            return False
        api = native_api if native_api is not None else _Win32Mdi()
        result = handoff.verify(
            scene, api, entry=entry, follows=previous_hwnd,
        )
        return result in {"native_new_draft", "owned_position_transaction"}
    except Exception:
        return False


def safe_native_start_action(loop, host, *, mission_revision: int) -> DraftProof:
    """One guarded native UIA InvokePattern call, never mouse fallback.

    A failed postcondition may mean Invoke physically happened: never retry.
    The caller is responsible for stopping at review on any failure.
    """
    from app.agent.runtime.navimind_local_input_arbiter import InputDenied
    from app.agent.runtime.navimind_v2_preaction_scene_guard import (
        verify_preaction_scene,
    )
    from tools.run_windowhub_new_offer_native_invoke_once import (
        resolve_native_control,
    )
    import os
    if (os.environ.get("WH_REAL_WINDOWHUB") != "1"
            or os.environ.get("COMPUTER_USE_LIVE") != "1"):
        raise InputDenied("draft_live_flags_required")
    if host.expected_offer != DRAFT_DOCUMENT_KEY:
        raise InputDenied("draft_host_not_in_bootstrap_mode")
    if host._approved_work_revision != mission_revision:
        raise InputDenied("draft_revision_not_operator_approved")
    permit = host.controller.current_permit()
    baseline = host._accepted_scene
    if permit is None or baseline is None or permit.document_key != DRAFT_DOCUMENT_KEY:
        raise InputDenied("draft_live_permit_or_observation_missing")
    try:
        comparison, fresh = verify_preaction_scene(loop, baseline)
        if not comparison.safe:
            raise InputDenied(comparison.reason)
        before = verify_draft_start(fresh)
        if not before.valid:
            raise InputDenied(before.reason)
        # Snapshot real MDI child inventory BEFORE creating the draft. This
        # prevents an existing offer selected later from being mistaken for
        # the document this mission started.
        from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi
        from app.agent.runtime.windowhub_new_offer_handoff import NewOfferHandoff
        native_api = _Win32Mdi()
        handoff = NewOfferHandoff.begin(fresh, native_api)
        if handoff is None:
            raise InputDenied("draft_start_native_mdi_inventory_unverified")
        invoke = resolve_native_control(
            fresh, label="NOWA OFERTA",
            allowed_stages=("start",),
        )
        # A native call is potentially non-idempotent even when it raises.
        host.controller.arbiter.dispatch(permit, invoke.Invoke)
        host._draft_native_scope = handoff
    finally:
        host.controller.arbiter.invalidate_observation()
        host._accepted_scene = None
    from time import sleep
    observed = None
    after = DraftProof(False, "unknown", "draft_post_action_reobservation_failed")
    for attempt in range(5):
        try:
            observed = loop.observe_scene()
            after = verify_draft_properties(observed, prior_hwnd=before.hwnd)
        except Exception:
            after = DraftProof(False, "unknown", "draft_post_action_reobservation_failed")
        if after.valid:
            break
        if attempt < 4:
            sleep(0.2)
    if not after.valid:
        raise RuntimeError("draft_start_action_effect_not_verified_no_retry")
    # Same-process native owner proof, not merely a matching dialog caption.
    from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi
    if not host._draft_native_scope.before_confirm(observed, _Win32Mdi()):
        raise RuntimeError("draft_properties_native_owner_unverified_no_retry")
    if not host.note_verified_workflow_step(observed, revision=mission_revision):
        raise RuntimeError("draft_properties_scope_unverified_no_retry")
    host._draft_phase = "properties"
    return after


def verified_lookup_grid(scene) -> bool:
    """Recognize a unique UIA grid that belongs to the existing customer field."""
    grids = []
    for element in scene.elements:
        metadata = element.metadata or {}
        if (
            element.kind == "table"
            and metadata.get("source") in {
                "windows_ui_automation", "windowhub_ui_automation",
            }
            and metadata.get("automation_id") == "PART_GridControl"
            and metadata.get("uia_visible") is True
            and metadata.get("uia_runtime_id")
            and any(
                isinstance(ancestor, dict)
                and ancestor.get("automation_id") == "IDC_ZAMAWIAJACY"
                for ancestor in (metadata.get("uia_ancestor_structure") or ())
            )
        ):
            grids.append(element)
    return len(grids) == 1


def safe_native_open_customer_picker(loop, host, *, mission_revision: int) -> DraftProof:
    """One native click on known IDC_ZAMAWIAJACY after scoped properties."""
    from app.agent.runtime.navimind_local_input_arbiter import InputDenied
    from app.agent.runtime.navimind_shared_control_host import verify_workflow_scope
    from app.agent.runtime.navimind_v2_preaction_scene_guard import (
        verify_preaction_scene,
    )
    from tools.run_windowhub_new_offer_native_invoke_once import (
        resolve_native_wrapper,
    )
    import os
    if (os.environ.get("WH_REAL_WINDOWHUB") != "1"
            or os.environ.get("COMPUTER_USE_LIVE") != "1"):
        raise InputDenied("draft_live_flags_required")
    if (host.expected_offer != DRAFT_DOCUMENT_KEY
            or host._draft_phase != "properties"
            or host._draft_native_scope is None
            or host._approved_work_revision != mission_revision):
        raise InputDenied("draft_properties_not_authorized")
    permit = host.controller.current_permit()
    baseline = host._accepted_scene
    if permit is None or baseline is None or permit.document_key != DRAFT_DOCUMENT_KEY:
        raise InputDenied("draft_customer_picker_permit_missing")
    try:
        comparison, scene = verify_preaction_scene(loop, baseline)
        if not comparison.safe:
            raise InputDenied(comparison.reason)
        proof = verify_workflow_scope(
            scene, host._workflow_scope,
            expected_offer=DRAFT_DOCUMENT_KEY, revision=mission_revision,
        )
        if not proof.verified or proof.stage != "document_properties":
            raise InputDenied("draft_properties_scope_not_verified")
        previous_hwnd = (scene.observation.metadata or {}).get("window_handle")
        if host._draft_native_scope.properties != previous_hwnd:
            raise InputDenied("draft_native_properties_identity_changed")
        if verified_lookup_grid(scene):
            host._draft_phase = "awaiting_customer_selection"
            return DraftProof(True, "customer_lookup", "customer_picker_already_open", previous_hwnd)
        button = resolve_native_wrapper(
            scene, label="Wybierz istniejącego klienta",
            automation_id="IDC_ZAMAWIAJACY",
            allowed_stages=("document_properties",),
            exact_customer_picker_id=True,
        )
        host.controller.arbiter.dispatch(permit, button.click_input)
    finally:
        host.controller.arbiter.invalidate_observation()
        host._accepted_scene = None
    from time import sleep
    from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi
    from app.agent.runtime.windowhub_new_offer_handoff import owner_chain

    native_api = _Win32Mdi()
    new_hwnd = None
    verified = False
    for attempt in range(5):
        try:
            after = loop.observe_scene()
            state = after.observation.state
            new_hwnd = (after.observation.metadata or {}).get("window_handle")
            app = (state.active_application or "").replace(chr(92), "/").rsplit("/", 1)[-1].casefold()
            title = (state.active_window_title or "").strip()
            if app != "okna.exe" or type(new_hwnd) is not int or new_hwnd <= 0:
                break
            if new_hwnd == previous_hwnd:
                verified = title == PROPERTIES_TITLE and verified_lookup_grid(after)
            else:
                verified = (
                    title.casefold() == "wybór klienta"
                    and native_api.pid(new_hwnd) == host._draft_native_scope.pid
                    and previous_hwnd in owner_chain(new_hwnd, native_api)
                )
        except Exception:
            verified = False
        if verified:
            break
        if attempt < 4:
            sleep(0.2)
    if not verified:
        raise RuntimeError("draft_picker_effect_unverified_no_retry")
    # No automatic selection from ambiguous customer list. Exact customer
    # or a supervised demo is required; the operator may finish manually.
    host._draft_phase = "awaiting_customer_selection"
    return DraftProof(True, "customer_lookup", "manual_exact_customer_selection_required", new_hwnd)


def requested_draft_customer(goal):
    """Accept an explicit full recipient, scoped to the human's offer command."""
    import re
    match = re.search(
        r"\bofert[ęe] dla ([^\n,.!?;]+?)(?= (?:na|z|bez)\b|[\n,.!?;]|$)",
        goal, flags=re.IGNORECASE,
    )
    if match is None:
        return None
    name = match[1].strip()
    if not 2 <= len(name.split()) <= 12 or len(name) > 100:
        return None
    if not all(char.isalpha() or char.isdecimal() or char in " -’'" for char in name):
        return None
    return name


def advance_owned_draft_properties(loop, host, *, revision, customer, customer_retry, exclude_services):
    """Advance a single owned properties form, under one fresh input permit."""
    from time import sleep

    from app.agent.offers.windowhub_customer_result_selection import (
        canonical_customer_name, customer_name_has_reordered_words, select_exact_customer_result,
    )
    from app.agent.offers.windowhub_customer_search_action import (
        type_customer_search, type_directly_into_customer_lookup,
    )
    from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
    from app.agent.runtime.navimind_shared_control_host import verify_workflow_scope
    from app.agent.runtime.navimind_v2_preaction_scene_guard import verify_preaction_scene
    from app.agent.runtime.windowhub_document_core import PRICE_TARGETS
    from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi
    from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_control
    from tools.run_windowhub_top_trans_single_window_mission import (
        toggle_price_once, verify_exclusion,
    )

    handoff = host._draft_native_scope
    permit = host.controller.current_permit()
    if (handoff is None or permit is None or permit.document_key != DRAFT_DOCUMENT_KEY
            or host._approved_work_revision != revision):
        return "draft_properties_not_authorized"
    api = _Win32Mdi()

    def same_properties(scene):
        proof = verify_workflow_scope(
            scene, host._workflow_scope, expected_offer=DRAFT_DOCUMENT_KEY, revision=revision,
        )
        return proof.verified and proof.stage == "document_properties" and (
            api.foreground() == handoff.properties and handoff._owned(handoff.properties, api)
        )

    def native_customer(scene):
        if verified_lookup_grid(scene):
            return False
        controls = [
            e.metadata for e in scene.elements
            if (e.metadata or {}).get("automation_id") == "IDC_ZAMAWIAJACY"
            and (e.metadata or {}).get("uia_visible") is True
        ]
        if len(controls) != 1:
            return False
        observed = controls[0]
        actual = canonical_customer_name(observed.get("current_value"))
        expected = canonical_customer_name(customer)
        matches = actual == expected or customer_name_has_reordered_words(actual, expected)
        source = observed.get("current_value_source")
        if source in {"value", "legacy_value", "get_value"}:
            return matches
        return (
            host._draft_customer_attested_revision == revision
            and (not actual or actual == "lookupedit" or matches)
        )

    comparison, scene = verify_preaction_scene(loop, host._accepted_scene)
    if not comparison.safe or not same_properties(scene):
        return "draft_properties_reobserve_required"
    if not customer:
        return "draft_customer_name_required"
    targets = PRICE_TARGETS if exclude_services else ()

    def fresh_properties():
        observed = enrich_windowhub_scene(loop.observe_scene())
        return observed if same_properties(observed) else None

    def require_current():
        from app.agent.runtime.navimind_local_input_arbiter import InputDenied

        if not host.controller.arbiter.permit_current(permit):
            raise InputDenied("draft_properties_permission_revoked")

    def operate():
        if not native_customer(scene):
            if customer_retry:
                return "draft_customer_selection_required"
            # Type once into the verified lookup and choose only a unique, exact
            # UIA result. A typed filter or dismissed popup alone proves nothing.
            host._draft_customer_search_attempted = True
            prefix = customer.split()[0][:3]
            require_current()
            result = type_customer_search(scene, prefix, strictly_scoped=True)
            if result.reason == "no_edit_and_picker_not_focused":
                require_current()
                result = type_directly_into_customer_lookup(
                    scene, prefix, replace_existing=True, strictly_scoped=True,
                )
            if result.status != "search_submitted_unverified":
                return "draft_customer_selection_required"
            for attempt in range(4):
                current = fresh_properties()
                if current is None:
                    return "draft_customer_selection_required"
                require_current()
                selected, reason = select_exact_customer_result(
                    current, customer, strictly_owned=True,
                )
                if selected:
                    break
                if reason != "EXACT_CUSTOMER_RESULT_NOT_UNIQUE_OR_NOT_VISIBLE":
                    return "draft_customer_selection_required"
                if attempt < 3:
                    sleep(0.2)
            else:
                return "draft_customer_selection_required"
            sleep(0.2)

        for key, checked in targets:
            current = fresh_properties()
            if current is None or not native_customer(current):
                return "draft_customer_selection_required"
            if not verify_exclusion(current, key, desired_checked=checked):
                require_current()
                if not toggle_price_once(current, key, desired_checked=checked):
                    return "draft_preferences_require_operator"

        final = fresh_properties()
        if final is None or not native_customer(final):
            return "draft_customer_selection_required"
        if not all(verify_exclusion(final, key, desired_checked=checked) for key, checked in targets):
            return "draft_preferences_require_operator"
        invoke = resolve_native_control(final, label="OK", allowed_stages=("document_properties",))
        # Record the attempted transition before Invoke. An exception is not a
        # reason to click OK twice; the next step observes the new document.
        require_current()
        host._draft_phase = "awaiting_confirmed_draft"
        invoke.Invoke()
        return "draft_properties_confirmed_reobserve"

    try:
        return host.controller.arbiter.dispatch(permit, operate)
    finally:
        host.controller.arbiter.invalidate_observation()
        host._accepted_scene = None


def focus_owned_properties(handoff, *, still_current=lambda: True):
    """Restore only the properties HWND previously bound to this draft."""
    import ctypes
    from app.agent.runtime.windowhub_mdi_native_probe import _Win32Mdi
    from app.agent.runtime.windowhub_window_activation import _focus_for_draft

    api = _Win32Mdi()
    hwnd = handoff.properties
    if not hwnd or api.title(hwnd) != PROPERTIES_TITLE or not handoff._owned(hwnd, api):
        return False
    return _focus_for_draft(ctypes.windll.user32, hwnd, still_current=still_current)
