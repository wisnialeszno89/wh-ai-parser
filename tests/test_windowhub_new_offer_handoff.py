from types import SimpleNamespace as NS

from app.agent.runtime.windowhub_new_offer_handoff import (
    NewOfferHandoff, scoped_position_stage,
)


class Native:
    hwnd = 10
    active = 30

    def __init__(self):
        self.titles = {10: "Okna - Start1", 30: "Start1", 31: "OFR/17-", 40: "Dokument1"}
        self.owners = {20: 10, 21: 10, 22: 10}
        self.children = [30, 31]
        self.pids = {}

    def foreground(self):
        return self.hwnd

    def title(self, hwnd):
        return self.titles.get(hwnd, "")

    def pid(self, hwnd):
        return self.pids.get(hwnd, 500)

    def owner(self, hwnd):
        return self.owners.get(hwnd, 0)

    def parent(self, hwnd, flag):
        if flag == 1 and hwnd in self.children:
            return 15
        if flag == 2 and (hwnd == 15 or hwnd in self.children):
            return 10
        return hwnd

    def mdi_hosts(self, hwnd):
        return (15,) if hwnd == 10 else ()

    def descendants(self, hwnd):
        return self.children if hwnd == 15 else ()

    def active_child(self, host):
        return self.active

    def observe(self, hwnd, title, *, tab=None):
        self.hwnd = hwnd
        elements = [] if tab is None else [
            NS(kind="tabitem", label=tab, metadata={
                "source": "windowhub_ui_automation", "uia_tab_scope": "document",
                "uia_selected": True, "uia_visible": True,
            }),
        ]
        return NS(observation=NS(
            state=NS(active_application="Okna.exe", active_window_title=title),
            metadata={"window_handle": hwnd},
        ), elements=elements)


def approved(native):
    scope = NewOfferHandoff.begin(native.observe(10, "Okna - Start1"), native)
    assert scope.before_confirm(native.observe(20, "Właściwości dokumentu"), native)
    return scope


def test_new_position_can_open_before_numbered_offer_and_become_verified_workspace():
    native = Native()
    scope = approved(native)
    native.children.append(40)
    native.active = 40
    native.titles[10] = "Okna - Dokument1"
    position = native.observe(21, "Dodawanie nowej pozycji")
    assert scope.verify(position, native, entry=True) == "native_new_draft"
    dimensions = native.observe(22, "Wielkość okna")
    assert scope.verify(dimensions, native, follows=21) == "native_new_draft"
    workspace = native.observe(10, "Okna - Dokument1", tab="Dokument1")
    assert scoped_position_stage(workspace, scope) == "offer_document"
    assert scope.verify(workspace, native) == "native_new_draft"
    native.titles.update({10: "Okna - OFR/42-", 40: "OFR/42-"})
    assert scope.verify(native.observe(10, "Okna - OFR/42-", tab="OFR/42-"), native) == "native_offer"
    assert scope.offer == "OFR/42-"


def test_modal_transaction_handles_direct_successor_hwnd_before_mdi_child_exists():
    native = Native()
    scope = approved(native)
    assert scope.verify(native.observe(21, "Dodawanie nowej pozycji"), native, entry=True) == "owned_position_transaction"
    dimensions = native.observe(22, "Wielkość okna")
    assert scope.verify(dimensions, native) == "wizard_successor_unverified"
    assert scope.verify(dimensions, native, follows=21) == "owned_position_transaction"
    assert scope.verify(dimensions, native) == "owned_position_transaction"


def test_same_process_without_native_owner_cannot_authorize_wizard():
    native = Native()
    scope = approved(native)
    del native.owners[21]
    assert scope.verify(native.observe(21, "Dodawanie nowej pozycji"), native, entry=True) == "foreground_or_native_owner_unverified"


def test_switch_to_an_old_offer_in_same_mdi_is_rejected():
    native = Native()
    scope = approved(native)
    native.active = 31
    assert scope.verify(native.observe(21, "Dodawanie nowej pozycji"), native, entry=True) == "preexisting_document_became_active"


def test_draft_workspace_requires_selected_tab_to_match_new_native_child():
    native = Native()
    scope = approved(native)
    native.children.append(40)
    native.active = 40
    native.titles[10] = "Okna - Dokument1"
    assert scope.verify(native.observe(21, "Dodawanie nowej pozycji"), native, entry=True) == "native_new_draft"
    assert scope.verify(native.observe(10, "Okna - Dokument1", tab="OFR/17-"), native) == "selected_document_unverified"


def test_live_start_hands_off_directly_to_existing_position_runner(monkeypatch):
    from app.agent.runtime import windowhub_document_core
    from tools import run_windowhub_existing_offer_position_test as position
    from tools import run_windowhub_new_offer_entry as entry

    native = Native()
    start = native.observe(10, "Okna - Start1")
    monkeypatch.setattr(position, "inspect", lambda loop: start)
    monkeypatch.setattr(entry, "main", lambda argv: 0)

    def confirm(*, before_confirm, on_confirmed, **kwargs):
        assert before_confirm(native.observe(20, "Właściwości dokumentu"))
        on_confirmed(native.observe(21, "Dodawanie nowej pozycji"))
        return 0

    def resume(loop, scope, api):
        assert isinstance(scope, NewOfferHandoff)
        assert scope.offer is None
        return 0 if position.belongs_to_offer(
            native.observe(21, "Dodawanie nowej pozycji"), scope, native,
        ) else 4

    monkeypatch.setattr(windowhub_document_core, "run_document_core", confirm)
    assert position.run_from_start(
        object(), "Test", native, on_offer_ready=resume, require_customer_confirmation=True,
    ) == 0


def test_main_editor_without_document_in_title_is_recognized_by_native_scope():
    native = Native()
    scope = approved(native)
    native.children.append(40)
    native.active = 40
    assert scope.verify(native.observe(21, "Dodawanie nowej pozycji"), native, entry=True) == "native_new_draft"
    native.titles[10] = "Okna -"
    workspace = native.observe(10, "Okna -", tab="Dokument1")
    assert scoped_position_stage(workspace, scope, native) == "windowhub_unmapped"
    native.editor_toolbar = lambda hwnd: 282
    assert scoped_position_stage(workspace, scope, native) == "offer_document"
    assert scope.verify(workspace, native) == "native_new_draft"
    assert scoped_position_stage(native.observe(10, "Okna -", tab="OFR/17-"), scope, native) == "windowhub_unmapped"
    native.active = 31
    assert scoped_position_stage(workspace, scope, native) == "windowhub_unmapped"


def test_visual_editor_proof_bridges_unknown_title_and_missing_uia_tab(monkeypatch):
    from tools import run_windowhub_existing_offer_position_test as wizard

    native = Native()
    scope = approved(native)
    native.children.append(40)
    native.active = 40
    assert scope.verify(native.observe(21, "Dodawanie nowej pozycji"), native, entry=True) == "native_new_draft"
    basic = native.observe(22, "Podstawowe parametry okna")
    scope.verify(basic, native, follows=21)
    basic.elements.append(NS(kind="button", label="Zakończ", metadata={
        "source": "windowhub_ui_automation", "automation_id": "42",
        "uia_visible": True, "uia_enabled": True,
    }))

    def observe(loop):
        native.titles[10] = "Okna -"
        return native.observe(10, "Okna -")

    monkeypatch.setattr(wizard, "inspect", observe)
    monkeypatch.setattr(wizard, "resolve_native_wrapper", lambda *args, **kw: NS(
        iface_invoke=NS(Invoke=lambda: None),
    ))
    calls = []

    def vision(scene, bound, api):
        calls.append(scene)
        return bound.accept_visual_editor(scene, api)

    destination = wizard.confirm_stage(object(), basic, scope, native, verify_editor=vision)
    assert destination is calls[0]
    assert scope.visual_editor_child == 40
    assert wizard.belongs_to_offer(destination, scope, native)

    native.active = 31
    assert not wizard.belongs_to_offer(destination, scope, native)


def test_visual_editor_cannot_be_used_for_order_or_mismatched_selected_document():
    native = Native()
    scope = approved(native)
    native.children.append(40)
    native.active = 40
    assert scope.verify(native.observe(21, "Dodawanie nowej pozycji"), native, entry=True) == "native_new_draft"
    native.titles[10] = "Okna -"
    assert not scope.accept_visual_editor(native.observe(10, "Okna -", tab="Dokument2"), native)
    assert not scope.accept_visual_editor(native.observe(10, "Okna -", tab="ZLC/25"), native)
    assert scope.visual_editor_child == 0


def test_editor_can_replace_destroyed_new_draft_handle_after_finish():
    native = Native()
    scope = approved(native)
    native.children.append(40)
    native.active = 40
    assert scope.verify(native.observe(21, "Dodawanie nowej pozycji"), native, entry=True) == "native_new_draft"
    native.children.append(41)
    native.titles[41] = "Dokument1"
    native.titles[10] = "Okna -"
    native.active = 41
    workspace = native.observe(10, "Okna -")
    assert not scope.accept_visual_editor(workspace, native)
    native.children.remove(40)
    native.pids[40] = 0
    assert scope.accept_visual_editor(workspace, native)
    assert scope.child == 41


def test_editor_only_binds_exact_selected_unnumbered_draft_and_never_switches():
    native = Native()
    native.children.extend((40, 41))
    native.active = 40
    native.titles.update({10: "Okna -", 40: "Dokument15", 41: "Dokument16"})
    workspace = native.observe(10, "Okna -", tab="Dokument15")

    assert NewOfferHandoff.bind_selected_draft(workspace, native, "Dokument16") is None
    assert NewOfferHandoff.bind_selected_draft(workspace, native, "OFR/17-") is None
    scope = NewOfferHandoff.bind_selected_draft(workspace, native, "Dokument15")
    assert scope is not None and scope.accept_visual_editor(workspace, native)
    assert scope.verify(workspace, native) == "native_new_draft"

    native.active = 41
    changed = native.observe(10, "Okna -", tab="Dokument16")
    assert not scope.accept_visual_editor(changed, native)
    assert scope.verify(changed, native) == "explicit_draft_editor_unverified"


def test_editor_only_uses_frame_caption_or_verified_visual_tab_without_overriding_conflicts():
    native = Native()
    native.active = 40
    native.children.append(40)
    native.titles.update({10: "Okna - Dokument15*", 40: ""})
    scene = native.observe(10, "Okna - Dokument15*")
    assert NewOfferHandoff.bind_selected_draft(scene, native, "Dokument15")
    native.titles[10] = "Okna -"
    scene = native.observe(10, "Okna -")
    assert NewOfferHandoff.bind_selected_draft(scene, native, "Dokument15") is None
    visual = lambda rgb: True
    assert NewOfferHandoff.bind_selected_draft(scene, native, "Dokument15", visual_draft_check=visual)
    scene = native.observe(10, "Okna -", tab="Dokument16")
    assert NewOfferHandoff.bind_selected_draft(scene, native, "Dokument15", visual_draft_check=visual) is None
