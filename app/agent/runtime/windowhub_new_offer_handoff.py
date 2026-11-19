"""Follow the native ownership of one new-offer transaction across its dialogs."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.runtime.active_document_scope import selected_document_tab
from app.agent.runtime.windowhub_mdi_native_probe import offer_caption_id, same_offer_id

_DRAFT_TITLE = re.compile(r"(?:okna - )?(dokument\s*\d+)\s*\*?", re.IGNORECASE)
WIZARD_STAGES = {"position", "dimensions", "basic_parameters", "glazing", "hardware", "modifier"}


def offer_title(title):
    value = title.strip()
    if value.casefold().startswith("okna - "):
        value = value[7:]
    return value if offer_caption_id(value) is not None else None


def _draft_name(title):
    match = _DRAFT_TITLE.fullmatch(title.strip())
    return re.sub(r"\s+", "", match[1]).casefold() if match else None


def active_native_draft_name(scene, api):
    """Resolve a name only when the native captions and selected tab agree."""
    frame = foreground_handle(scene, api)
    if not frame or stage_of(scene) != "windowhub_unmapped":
        return None
    child = active_mdi_child(frame, api)
    if not child:
        return None
    selected, _ = selected_document_tab(scene)
    names = {
        draft for title in (api.title(frame), api.title(child), selected or "")
        if (draft := _draft_name(title))
    }
    if len(names) == 1:
        return names.pop()
    return None


def scoped_position_stage(scene, scope, api=None):
    stage = stage_of(scene)
    if stage == "windowhub_unmapped" and isinstance(scope, NewOfferHandoff):
        title = scene.observation.state.active_window_title or ""
        if _draft_name(title) or (api is not None and scope.recognizes_editor(scene, api)):
            return "offer_document"
    return stage


def foreground_handle(scene, api):
    hwnd = scene.observation.metadata.get("window_handle")
    return hwnd if type(hwnd) is int and hwnd > 0 and api.foreground() == hwnd else 0


def owner_chain(hwnd, api):
    """Follow direct owner HWNDs, retaining an MDI owner before the root frame."""
    result = []
    while hwnd and hwnd not in result and len(result) < 12:
        result.append(hwnd)
        owner = api.owner(hwnd)
        if not owner:
            root = api.parent(hwnd, 2)
            owner = api.owner(root) if root and root != hwnd else 0
        hwnd = owner
    return tuple(result)


def active_mdi_child(frame, api):
    active = []
    for host in api.mdi_hosts(frame):
        child = api.active_child(host)
        if child and api.parent(child, 1) == host and api.parent(host, 2) == frame:
            active.append(child)
    return active[0] if len(active) == 1 else 0


@dataclass
class NewOfferHandoff:
    frame: int
    pid: int
    previous_child: int
    previous_children: frozenset[int]
    previous_offer: str | None
    properties: int = 0
    position: int = 0
    child: int = 0
    offer: str | None = None
    visual_editor_child: int = 0
    explicit_draft: str | None = None
    visual_draft_check: Callable | None = None

    @classmethod
    def begin(cls, scene, api):
        hwnd = foreground_handle(scene, api)
        if not hwnd or stage_of(scene) not in {"start", "offer_document"}:
            return None
        pid = api.pid(hwnd)
        if not pid:
            return None
        children = frozenset(
            child for host in api.mdi_hosts(hwnd) for child in api.descendants(host)
            if api.parent(child, 1) == host
        )
        return cls(hwnd, pid, active_mdi_child(hwnd, api), children, offer_title(api.title(hwnd)))

    @classmethod
    def bind_selected_draft(cls, scene, api, name, *, visual_draft_check=None):
        """Bind only a named, already foreground, unnumbered test document."""
        draft = _draft_name(name)
        frame = foreground_handle(scene, api)
        if not draft or not frame or stage_of(scene) != "windowhub_unmapped":
            return None
        child = active_mdi_child(frame, api)
        pid = api.pid(frame)
        if not child or not pid or api.pid(child) != pid:
            return None
        scope = cls(frame, pid, 0, frozenset(), None, child=child, explicit_draft=draft,
                    visual_draft_check=visual_draft_check)
        return scope if scope.editor_candidate(scene, api) == "eligible" else None

    def _owned(self, hwnd, api):
        if not hwnd or api.pid(hwnd) != self.pid or api.pid(self.frame) != self.pid:
            return False
        return any(
            link == self.frame or api.parent(link, 2) == self.frame or api.parent(link, 3) == self.frame
            for link in owner_chain(hwnd, api)
        )

    def before_confirm(self, scene, api):
        hwnd = foreground_handle(scene, api)
        if stage_of(scene) != "document_properties" or hwnd == self.frame or not self._owned(hwnd, api):
            return False
        self.properties = hwnd
        return True

    def _editor_child(self, api, *, observed_replacement=False):
        active = active_mdi_child(self.frame, api)
        if active == self.child:
            return active
        if (
            self.explicit_draft or not observed_replacement or not active or active in self.previous_children
            or api.pid(active) != self.pid or self.child in api.descendants(self.frame)
            or api.pid(self.child)
        ):
            return 0
        return active

    def editor_candidate(self, scene, api, *, observed_replacement=False):
        """Check whether read-only visual verification may inspect this frame."""
        hwnd = foreground_handle(scene, api)
        if not (self.explicit_draft or (self.properties and self.position)) or not self.child or hwnd != self.frame:
            return "not_bound_editor_frame"
        child = self._editor_child(api, observed_replacement=observed_replacement)
        if not self._owned(hwnd, api) or not child:
            return "native_active_document_changed"
        if stage_of(scene) not in {"windowhub_unmapped", "offer_document"}:
            return "not_workspace_stage"
        selected, _ = selected_document_tab(scene)
        child_title = api.title(child)
        frame_title = api.title(hwnd)
        for caption in (frame_title, child_title, selected or ""):
            normalized = caption.strip().casefold()
            if normalized.startswith(("okna - zlc/", "zlc/")) or normalized in {"start1", "okna - start1"}:
                return "other_document_kind"
            numbered = offer_title(caption)
            if numbered and not (same_offer_id(numbered, self.offer) or same_offer_id(numbered, offer_title(child_title))):
                return "other_numbered_offer"
        child_draft = _draft_name(child_title)
        selected_draft = _draft_name(selected or "")
        draft_names = {_draft_name(frame_title), child_draft, selected_draft}
        if self.explicit_draft and (
            (self.explicit_draft not in draft_names and self.visual_draft_check is None)
            or any(name and name != self.explicit_draft for name in draft_names)
            or (selected and not selected_draft)
            or (child_title.strip() and not child_draft)
        ):
            return "explicit_draft_does_not_match"
        if child_draft and selected_draft and child_draft != selected_draft:
            return "other_selected_draft"
        return "eligible"

    def accept_visual_editor(self, scene, api):
        if self.editor_candidate(scene, api, observed_replacement=True) != "eligible":
            return False
        current = self._editor_child(api, observed_replacement=True)
        if not current:
            return False
        self.child = self.visual_editor_child = current
        return True

    def has_visual_editor(self, scene, api):
        return bool(
            self.visual_editor_child and self.visual_editor_child == self.child
            and self.editor_candidate(scene, api) == "eligible"
        )

    def recognizes_editor(self, scene, api):
        """Recognize a title-less editor only for the already bound new MDI child."""
        if self.has_visual_editor(scene, api):
            return True
        if not self.properties or not self.position or not self.child:
            return False
        hwnd = foreground_handle(scene, api)
        if hwnd != self.frame or api.pid(hwnd) != self.pid or active_mdi_child(hwnd, api) != self.child:
            return False
        selected, _ = selected_document_tab(scene)
        child_title = api.title(self.child).strip()
        selected_draft = _draft_name(selected or "")
        draft_tab_matches = selected_draft and (not child_title or selected_draft == _draft_name(child_title))
        if not selected or not (same_offer_id(selected, self.offer) or (not self.offer and draft_tab_matches)):
            return False
        toolbar = getattr(api, "editor_toolbar", None)
        return bool(toolbar and toolbar(hwnd))

    def _workspace(self, scene, api):
        """Match the selected tab and the linked native child or main caption."""
        if self.has_visual_editor(scene, api):
            return True
        selected, _ = selected_document_tab(scene)
        if not selected:
            return False
        frame_title = api.title(self.frame)
        child_title = api.title(self.child) if self.child else ""
        if self.offer:
            return same_offer_id(selected, self.offer) and (
                same_offer_id(offer_title(frame_title), self.offer)
                or same_offer_id(offer_title(child_title), self.offer)
            )
        draft = _draft_name(child_title)
        return self.recognizes_editor(scene, api) or bool(
            draft and draft == _draft_name(selected) and draft == _draft_name(frame_title)
        )

    def bind_next_position(self, scene, api):
        """Arm continuation after a verified Add action opens the position form."""
        hwnd = foreground_handle(scene, api)
        if not self.explicit_draft or stage_of(scene) != "position" or not self._owns_draft_wizard(hwnd, api):
            return False
        self.position = hwnd
        return True

    def _owns_draft_wizard(self, hwnd, api):
        return bool(
            hwnd and hwnd != self.frame and self._owned(hwnd, api)
            and active_mdi_child(self.frame, api) == self.child
        )

    def verify(self, scene, api, *, entry=False, follows=None):
        """Return the evidence source, or a diagnostic explaining the block."""
        hwnd = foreground_handle(scene, api)
        stage = scoped_position_stage(scene, self, api)
        if self.explicit_draft:
            if self.has_visual_editor(scene, api):
                return "native_new_draft"
            if (
                self.position and stage in WIZARD_STAGES and self._owns_draft_wizard(hwnd, api)
                and (hwnd == self.position or follows == self.position)
            ):
                self.position = hwnd
                return "owned_position_transaction"
            return "explicit_draft_editor_unverified"
        if not self.properties or not self._owned(hwnd, api):
            return "foreground_or_native_owner_unverified"
        if hwnd == self.properties or (entry and stage not in {"position", "offer_document"}):
            return "unexpected_confirmation_destination"
        if hwnd != self.frame and stage not in WIZARD_STAGES:
            return "unrecognized_owned_window"

        observed_child = active_mdi_child(self.frame, api)
        if self.child and observed_child != self.child:
            return "active_document_changed"
        # A caption on an existing MDI child predating New Offer cannot
        # authorize a new draft. A wizard owned by the approved frame may
        # open before a new child or the OFR number has been assigned.
        if (
            observed_child and observed_child != self.previous_child
            and observed_child in self.previous_children
            and api.title(observed_child).strip().casefold() != "start1"
        ):
            return "preexisting_document_became_active"
        candidate = observed_child if observed_child and observed_child not in self.previous_children else 0
        if candidate and api.pid(candidate) != self.pid:
            return "active_document_process_changed"
        titles = [offer_title(api.title(handle)) for handle in (self.frame, candidate) if handle]
        titles = [title for title in titles if title and not same_offer_id(title, self.previous_offer)]
        ids = {offer_caption_id(title) for title in titles}
        if len(ids) > 1 or (self.offer and ids and offer_caption_id(self.offer) not in ids):
            return "native_document_titles_disagree"
        if not candidate and self.previous_offer and hwnd == self.frame and not self.offer and not titles:
            return "new_document_not_observed"

        if hwnd != self.frame:
            follows_action = follows and follows == self.position
            if not entry and hwnd != self.position and not follows_action and (
                not self.position or self.position not in owner_chain(hwnd, api)
            ):
                return "wizard_successor_unverified"
            self.position = hwnd
        if not candidate and not self.offer and not titles:
            return "draft_workspace_unverified" if hwnd == self.frame else "owned_position_transaction"

        if candidate:
            self.child = candidate
        if titles:
            self.offer = titles[0]
        if hwnd == self.frame and not self._workspace(scene, api):
            return "selected_document_unverified"
        return "native_offer" if self.offer else "native_new_draft"


VERIFIED_HANDOFF = {"native_offer", "native_new_draft", "owned_position_transaction"}
