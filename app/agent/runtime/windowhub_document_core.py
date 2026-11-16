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


def run_document_core(*, customer_name: str, fresh_document: bool) -> int:
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

    ok, reason = activate_windowhub_workflow_window()
    print("DOCUMENT_CORE_ACTIVATION=" + reason)
    if not ok:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = inspect(loop)
    if stage_of(scene) != "document_properties":
        print("DOCUMENT_CORE_STAGE=not_document_properties")
        return 4

    verified_customer = customer_selected(scene, customer_name)
    print("CUSTOMER_INITIAL_READBACK=" + str(verified_customer))

    if not verified_customer and fresh_document:
        matched, detail = progressive_customer_selection(
            loop, scene, customer_name, require_result_click=True,
        )
        print("CUSTOMER_LOOKUP_STATUS=" + detail)
        verified_customer = matched
        # Do not reinterpret a clicked exact suggestion as confirmed.
        if not verified_customer:
            print("CUSTOMER_COMMIT_STATUS=unverified")
    elif not verified_customer:
        print("CUSTOMER_LOOKUP_STATUS=already_open_no_blind_reselection")
        print("CUSTOMER_COMMIT_STATUS=unverified")

    # Pricing is independently observable even if the legacy lookup cannot
    # expose selected customer data. Safe to configure; not safe to confirm.
    for key, desired in PRICE_TARGETS:
        scene = inspect(loop)
        if stage_of(scene) != "document_properties":
            print("DOCUMENT_PRICE_STAGE_LOST=" + key)
            return 6
        if verify_exclusion(scene, key, desired_checked=desired):
            print("DOCUMENT_PRICE_" + key + "=verified_already")
            continue
        if not toggle_price_once(scene, key, desired_checked=desired):
            print("DOCUMENT_PRICE_" + key + "=change_failed")
            return 6
        after = inspect(loop)
        if not verify_exclusion(after, key, desired_checked=desired):
            print("DOCUMENT_PRICE_" + key + "=readback_failed")
            return 6
        print("DOCUMENT_PRICE_" + key + "=verified_updated")

    final = inspect(loop)
    flags_ok = stage_of(final) == "document_properties" and all(
        verify_exclusion(final, key, desired_checked=desired)
        for key, desired in PRICE_TARGETS
    )
    # Fresh exact-value readback has priority. A previously observed native
    # verified selection may also count, but merely typing never does.
    verified_customer = verified_customer or customer_selected(final, customer_name)
    readiness = document_readiness(
        customer_verified=verified_customer, flags_verified=flags_ok
    )
    print("DOCUMENT_PRICE_FLAGS_VERIFIED=" + str(flags_ok))
    print("DOCUMENT_CUSTOMER_VERIFIED=" + str(verified_customer))
    print("DOCUMENT_READINESS=" + readiness)
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
        if native_invoke is not None:
            native_invoke.Invoke()
        else:
            wrapper.click_input()
    except Exception as exc:
        print("DOCUMENT_CONFIRM_ERROR=" + type(exc).__name__)
        return 6
    for expected in ("offer_document", "position"):
        # Each observation is fresh; no second click, and no document saving.
        scene = inspect(loop)
        if stage_of(scene) == expected:
            print("DOCUMENT_CONFIRM_STAGE=" + expected)
            return 0
    from time import sleep
    for _ in range(3):
        sleep(0.25)
        scene = inspect(loop)
        if stage_of(scene) in {"offer_document", "position"}:
            print("DOCUMENT_CONFIRM_STAGE=" + str(stage_of(scene)))
            return 0
    print("DOCUMENT_CONFIRM=transition_unverified")
    return 6
