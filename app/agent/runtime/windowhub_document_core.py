"""Single verified document-properties core for WindowHub.

The customer's requested values flow through arguments; no Top Trans demo
globals or hardcoded construction parameters are used. Fail closed on customer
identity uncertainty, but still allow independently verifiable price flags
to be set in the open, unsaved document.
"""
from __future__ import annotations

from app.agent.learning.windowhub_demonstration import stage_of

PRICE_TARGETS = (
    ("exclude_construction_price", False),
    ("exclude_installation_price", True),
    ("exclude_removal_price", True),
    ("exclude_finishing_price", True),
)


def document_readiness(*, customer_verified: bool, flags_verified: bool) -> str:
    if not flags_verified:
        return "pricing_unverified"
    if not customer_verified:
        return "customer_unverified"
    return "ready"


_MANUAL_CUSTOMER = object()


def confirm_customer_completion(customer_name, completions, ask):
    """Ask for an exact observed name or a user-supplied full name."""
    labels = sorted({label.casefold(): label for label in sorted(completions)}.values(), key=str.casefold)
    try:
        if len(labels) == 1:
            reply = ask(f"Czy wybrać '{labels[0]}' dla '{customer_name}'? [tak/ręcznie/N]: ")
            answer = reply.strip().casefold()
            if answer in {"ręcznie", "recznie"}:
                return _MANUAL_CUSTOMER
            return labels[0] if answer in {"tak", "t"} else None
        if labels:
            print("CUSTOMER_VISIBLE_COMPLETIONS=" + repr(labels[:10]))
        full_name = ask("Podaj pełną nazwę klienta lub wpisz 'ręcznie' (Enter = przerwij): ").strip()
        if full_name.casefold() in {"ręcznie", "recznie"}:
            return _MANUAL_CUSTOMER
    except (EOFError, KeyboardInterrupt):
        return None
    if (
        not full_name or len(full_name) > 100 or any(ord(char) < 32 for char in full_name)
        or full_name.casefold() == customer_name.casefold()
    ):
        return None
    return full_name


def customer_confirmation_conflicts(picker_metadata, expected, *, allow_opaque_caption=False):
    """Compare a native value with the operator's confirmed selection."""
    raw = picker_metadata.get("current_value")
    if not isinstance(raw, str) or not raw.strip():
        return False
    if raw.strip().casefold() == expected.strip().casefold():
        return False
    return not (
        allow_opaque_caption and picker_metadata.get("current_value_source")
        in {"window_text", "rich_text"}
    )


def run_document_core(*, customer_name: str, fresh_document: bool,
                      interactive_handoff: bool = False,
                      ask=input, on_confirmed=None, before_confirm=None,
                      confirm_similar_customer=False, replace_customer_filter=False,
                      allow_test_blank_customer=False, require_customer_confirmation=False) -> int:
    """Configure document, then confirm only after full evidence.

    When resuming an open dialog, never retype a previously clicked customer
    just because a legacy LookUpEdit doesn't expose its selected native value.
    """
    from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
    from app.agent.runtime.windows_desktop_agent_control_loop import (
        create_windows_desktop_agent_control_loop,
    )
    from tools.run_windowhub_top_trans_single_window_mission import (
        inspect, customer_selected, progressive_customer_selection,
        verify_exclusion, toggle_price_once, matches, observe_step,
    )
    from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_wrapper
    from app.agent.offers.windowhub_customer_result_selection import (
        customer_name_completes_query, customer_name_has_reordered_words,
    )

    ok, reason = activate_windowhub_workflow_window()
    print("DOCUMENT_CORE_ACTIVATION=" + reason)
    if not ok:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = inspect(loop)
    if stage_of(scene) != "document_properties":
        print("DOCUMENT_CORE_STAGE=not_document_properties")
        return 4

    customer_source = "native"
    operator_approved = False
    allow_opaque_caption = False
    verified_customer = customer_selected(scene, customer_name)
    print("CUSTOMER_INITIAL_READBACK=" + str(verified_customer))

    if not verified_customer and fresh_document:
        completions = set()
        lookup_options = {}
        if confirm_similar_customer:
            lookup_options.update(visible_completions=completions, short_prefix_only=True)
        if replace_customer_filter:
            lookup_options["replace_existing"] = True
        matched, detail = progressive_customer_selection(
            loop, scene, customer_name, require_result_click=True, **lookup_options,
        )
        print("CUSTOMER_LOOKUP_STATUS=" + detail)
        hwnd = getattr(scene.observation, "metadata", {}).get("window_handle")
        if confirm_similar_customer and completions and detail == "CUSTOMER_NO_EXACT_RESULT_FOR_SHORT_PREFIX":
            approved = confirm_customer_completion(customer_name, completions, ask)
            if approved is None:
                print("CUSTOMER_COMPLETION_STOP=not_approved")
                return 6
            if approved is not _MANUAL_CUSTOMER:
                operator_approved = True
                customer_name = approved
                focused, reason = activate_windowhub_workflow_window()
                print("CUSTOMER_COMPLETION_REFOCUS=" + reason)
                resumed = inspect(loop) if focused else None
                if (
                    type(hwnd) is not int or hwnd <= 0 or resumed is None
                    or stage_of(resumed) != "document_properties"
                    or resumed.observation.metadata.get("window_handle") != hwnd
                ):
                    print("CUSTOMER_COMPLETION_STOP=document_changed")
                    return 6
                matched, detail = progressive_customer_selection(
                    loop, resumed, customer_name, require_result_click=True,
                    replace_existing=True, short_prefix_only=True,
                )
                print("CUSTOMER_APPROVED_EXACT_LOOKUP_STATUS=" + detail)

        if not matched and confirm_similar_customer:
            if type(hwnd) is not int or hwnd <= 0:
                print("CUSTOMER_MANUAL_STOP=original_document_unverified")
                return 6
            clicked_exact = detail.startswith("CUSTOMER_CLICKED_BUT_SELECTION_UNVERIFIED_")
            try:
                if clicked_exact:
                    print("CUSTOMER_VISUAL_CONFIRMATION_REQUIRED=True")
                    reply = ask(
                        f"Sprawdź pole klienta w WindowHub. Czy wybrano '{customer_name}'? [tak/N]: "
                    )
                    if reply.strip().casefold() not in {"tak", "t"}:
                        print("CUSTOMER_MANUAL_STOP=selection_not_confirmed")
                        return 6
                    manual = customer_name
                else:
                    print("CUSTOMER_MANUAL_SELECTION_REQUIRED=True")
                    hint = (
                        " W teście bez klienta pozostaw pole puste i wpisz 'BEZ KLIENTA'."
                        if allow_test_blank_customer else ""
                    )
                    manual = ask(
                        "Wybierz klienta w WindowHub, pozostaw Właściwości dokumentu otwarte "
                        "i wpisz w PowerShell pełną nazwę wybranego klienta." + hint
                        + " [Enter = przerwij]: "
                    ).strip()
            except (EOFError, KeyboardInterrupt):
                return 6
            blank = not clicked_exact and allow_test_blank_customer and manual.casefold() == "bez klienta"
            if not blank and (
                not manual or len(manual) > 100 or any(ord(char) < 32 for char in manual)
            ):
                print("CUSTOMER_MANUAL_STOP=invalid_confirmation")
                return 6
            if not blank and not (
                manual.casefold() == customer_name.casefold()
                or customer_name_completes_query(manual, customer_name)
                or customer_name_has_reordered_words(manual, customer_name)
            ):
                try:
                    answer = ask(
                        f"Czy zastąpić klienta '{customer_name}' wybranym '{manual}'? [tak/N]: "
                    )
                except (EOFError, KeyboardInterrupt):
                    return 6
                if answer.strip().casefold() not in {"tak", "t"}:
                    print("CUSTOMER_MANUAL_STOP=client_change_not_approved")
                    return 6
            focused, reason = activate_windowhub_workflow_window()
            print("CUSTOMER_MANUAL_REFOCUS=" + reason)
            resumed = inspect(loop) if focused else None
            if (
                resumed is None or stage_of(resumed) != "document_properties"
                or resumed.observation.metadata.get("window_handle") != hwnd
            ):
                print("CUSTOMER_MANUAL_STOP=document_changed")
                return 6
            # If UIA does expose a concrete value, make it agree with the
            # operator. An opaque field can only be attested by the operator.
            picker = matches(resumed, automation_id="IDC_ZAMAWIAJACY")
            if len(picker) != 1:
                print("CUSTOMER_MANUAL_STOP=lookup_identity_unverified")
                return 6
            allow_opaque_caption = not blank and (
                not clicked_exact or detail == (
                    "CUSTOMER_CLICKED_BUT_SELECTION_UNVERIFIED_native_selected_value_not_exposed_popup_closed"
                )
            )
            if customer_confirmation_conflicts(
                picker[0].metadata or {}, "" if blank else manual,
                allow_opaque_caption=allow_opaque_caption,
            ):
                print("CUSTOMER_MANUAL_STOP=visible_lookup_value_disagrees")
                return 6
            if allow_opaque_caption and (picker[0].metadata or {}).get("current_value_source") in {
                "window_text", "rich_text",
            }:
                print("CUSTOMER_CAPTION_NOT_USED_AS_SELECTED_VALUE=True")
            customer_name = "" if blank else manual
            customer_source = "human_confirmed_blank_test" if blank else "human_confirmed_selection"
            matched = True
            operator_approved = True
            print("CUSTOMER_VERIFICATION_SOURCE=" + customer_source)

        verified_customer = matched
        if not verified_customer:
            print("CUSTOMER_COMMIT_STATUS=unverified")
    elif not verified_customer:
        print("CUSTOMER_LOOKUP_STATUS=already_open_no_blind_reselection")
        print("CUSTOMER_COMMIT_STATUS=unverified")

    if require_customer_confirmation and verified_customer and not operator_approved:
        selection = inspect(loop)
        hwnd = selection.observation.metadata.get("window_handle")
        if (
            type(hwnd) is not int or hwnd <= 0 or stage_of(selection) != "document_properties"
            or not customer_selected(selection, customer_name)
        ):
            print("CUSTOMER_APPROVAL_STOP=selection_unverified")
            return 6
        try:
            answer = ask(f"Potwierdź klienta oferty '{customer_name}' [tak/N]: ")
        except (EOFError, KeyboardInterrupt):
            return 6
        if answer.strip().casefold() not in {"tak", "t"}:
            print("CUSTOMER_APPROVAL_STOP=declined")
            return 6
        focused, _ = activate_windowhub_workflow_window()
        selection = inspect(loop) if focused else None
        if (
            selection is None or stage_of(selection) != "document_properties"
            or selection.observation.metadata.get("window_handle") != hwnd
            or not customer_selected(selection, customer_name)
        ):
            print("CUSTOMER_APPROVAL_STOP=selection_changed")
            return 6
        print("CUSTOMER_APPROVAL=confirmed")

    # Four checkboxes share one stable dialog. Inspect the entire form once,
    # invoke each *freshly rebound native* UIA TogglePattern only if required,
    # and capture one new scene at the end. Individual native toggles still
    # validate current state, identity and foreground before changing it.
    # On any mismatch, stop; never blindly retry.
    pricing_scene = inspect(loop)
    if stage_of(pricing_scene) != "document_properties" or (
        confirm_similar_customer and pricing_scene.observation.metadata.get("window_handle")
        != scene.observation.metadata.get("window_handle")
    ):
        print("DOCUMENT_PRICE_STAGE_LOST=before_batch")
        return 6
    changed = []
    for key, desired in PRICE_TARGETS:
        if verify_exclusion(pricing_scene, key, desired_checked=desired):
            print("DOCUMENT_PRICE_" + key + "=verified_already")
            continue
        if not toggle_price_once(pricing_scene, key, desired_checked=desired):
            print("DOCUMENT_PRICE_" + key + "=change_failed")
            if not confirm_similar_customer:
                return 6
            break
        changed.append(key)

    final = inspect(loop)
    if confirm_similar_customer and (
        stage_of(final) != "document_properties"
        or final.observation.metadata.get("window_handle") != scene.observation.metadata.get("window_handle")
    ):
        print("DOCUMENT_CONFIRM_STOP=original_document_changed")
        return 6
    if customer_source != "native":
        final_picker = matches(final, automation_id="IDC_ZAMAWIAJACY")
        if len(final_picker) != 1 or customer_confirmation_conflicts(
            final_picker[0].metadata or {}, customer_name,
            allow_opaque_caption=allow_opaque_caption,
        ):
            print("DOCUMENT_CONFIRM_STOP=customer_evidence_changed")
            return 6
    for key in changed:
        if verify_exclusion(final, key, desired_checked=dict(PRICE_TARGETS)[key]):
            print("DOCUMENT_PRICE_" + key + "=verified_updated")
        else:
            print("DOCUMENT_PRICE_" + key + "=readback_failed")
            if not confirm_similar_customer:
                return 6
    print("DOCUMENT_PRICE_BATCH_SCREENSHOTS=2")
    flags_ok = stage_of(final) == "document_properties" and all(
        verify_exclusion(final, key, desired_checked=desired)
        for key, desired in PRICE_TARGETS
    )
    if not flags_ok and confirm_similar_customer:
        try:
            answer = ask(
                "Ustaw ręcznie: bez cen montażu, demontażu i wykończenia, z ceną konstrukcji. "
                "Zostaw Właściwości dokumentu otwarte i wpisz 'gotowe' (Enter = przerwij): "
            )
        except (EOFError, KeyboardInterrupt):
            return 6
        if answer.strip().casefold() != "gotowe":
            return 6
        focused, reason = activate_windowhub_workflow_window()
        print("DOCUMENT_PRICE_HANDOFF_REFOCUS=" + reason)
        if not focused:
            return 6
        final = inspect(loop)
        if (
            stage_of(final) != "document_properties"
            or final.observation.metadata.get("window_handle") != scene.observation.metadata.get("window_handle")
        ):
            print("DOCUMENT_CONFIRM_STOP=original_document_changed")
            return 6
        picker = matches(final, automation_id="IDC_ZAMAWIAJACY")
        if len(picker) != 1 or customer_confirmation_conflicts(
            picker[0].metadata or {}, customer_name, allow_opaque_caption=allow_opaque_caption,
        ):
            print("DOCUMENT_CONFIRM_STOP=customer_evidence_changed")
            return 6
        flags_ok = all(verify_exclusion(final, key, desired_checked=desired) for key, desired in PRICE_TARGETS)
        print("DOCUMENT_PRICE_HANDOFF_READBACK=" + str(flags_ok))

    # Fresh exact-value readback has priority. A previously observed native
    # verified selection may also count, but merely typing never does.
    if require_customer_confirmation and customer_source == "native":
        verified_customer = verified_customer and customer_selected(final, customer_name)
    else:
        verified_customer = verified_customer or customer_selected(final, customer_name)
    readiness = document_readiness(
        customer_verified=verified_customer, flags_verified=flags_ok
    )
    print("DOCUMENT_PRICE_FLAGS_VERIFIED=" + str(flags_ok))
    print("DOCUMENT_CUSTOMER_VERIFIED=" + str(verified_customer and customer_source == "native"))
    if customer_source != "native":
        print("DOCUMENT_CUSTOMER_ACCEPTANCE=" + customer_source)
    print("DOCUMENT_READINESS=" + readiness)
    if readiness == "customer_unverified" and interactive_handoff:
        # This is a human approval, not a machine verification. Keep the
        # identity explicit and require a *second* opt-in to continue.
        print("HANDOFF_REASON=WindowHub lookup hides the committed value")
        print("HANDOFF_INSTRUCTION=Check the selected customer on the live WindowHub form.")
        try:
            confirmed = ask(
                "Potwierdź nazwę wybranego klienta, wpisując dokładnie '"
                + customer_name + "' (Enter = odmowa): "
            )
        except (EOFError, KeyboardInterrupt):
            print("HANDOFF_DECLINED=True")
            return 6
        if confirmed.strip().casefold() == customer_name.strip().casefold():
            print("CUSTOMER_VERIFICATION_SOURCE=human_explicit_confirmation")
            try:
                resume = ask("Kontynuować pracę z aktualnego miejsca według wytycznych? [tak/N]: ")
            except (EOFError, KeyboardInterrupt):
                print("HANDOFF_DECLINED=True")
                return 6
            if resume.strip().casefold() in {"tak", "t"}:
                # PowerShell became foreground while taking the answer.
                # Restore WindowHub automatically before inspecting the dialog.
                refocused, why = activate_windowhub_workflow_window()
                print("HANDOFF_REFOCUS=" + why)
                if not refocused:
                    return 6
                # Re-observe to defend against handoff-time UI changes.
                final = inspect(loop)
                if stage_of(final) != "document_properties" or not all(
                    verify_exclusion(final, key, desired_checked=desired)
                    for key, desired in PRICE_TARGETS
                ):
                    print("HANDOFF_REVALIDATION_FAILED=True")
                    return 6
                verified_customer = True
                readiness = "ready"
                print("HANDOFF_RESUME_APPROVED=True")
        if readiness != "ready":
            print("HANDOFF_DECLINED=True")
    if readiness != "ready":
        print("DOCUMENT_REMAINS_OPEN=True")
        print("NO_UNVERIFIED_OK_CLICK=True")
        return 6

    matches_ok = matches(final, kind="button", label="OK")
    if len(matches_ok) != 1:
        print("DOCUMENT_CONFIRM=ambiguous_button")
        return 6
    try:
        wrapper = resolve_native_wrapper(
            final, label="OK", allowed_stages=("document_properties",),
        )
        native_invoke = getattr(wrapper, "iface_invoke", None)
        if before_confirm is not None and not before_confirm(final):
            print("DOCUMENT_CONFIRM=transaction_source_unverified")
            return 6
        if native_invoke is not None:
            native_invoke.Invoke()
        else:
            wrapper.click_input()
    except Exception as exc:
        print("DOCUMENT_CONFIRM_ERROR=" + type(exc).__name__)
        return 6
    from time import sleep
    for attempt in range(5):
        scene = inspect(loop)
        stage = stage_of(scene)
        if stage in {"offer_document", "position"}:
            print("DOCUMENT_CONFIRM_STAGE=" + stage)
            if on_confirmed is not None:
                on_confirmed(scene)
            return 0
        if stage != "document_properties" and stage != "windowhub_unmapped":
            break
        if attempt < 4:
            sleep(0.25)
    print("DOCUMENT_CONFIRM=transition_unverified")
    return 6
