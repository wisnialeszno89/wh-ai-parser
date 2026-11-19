"""Follow the native ownership of one new-offer transaction across its dialogs."""
from __future__ import annotations

from dataclasses import dataclass
import re

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.runtime.active_document_scope import selected_document_tab
from app.agent.runtime.windowhub_mdi_native_probe import offer_caption_id, same_offer_id

_DRAFT_TITLE = re.compile(r"(?:okna - )?(dokument\s*\d+)", re.IGNORECASE)
WIZARD_STAGES = {"position", "dimensions", "basic_parameters", "glazing", "hardware", "modifier"}


def offer_title(title):
    value = title.strip()
    if value.casefold().startswith("okna - "):
        value = value[7:]
    return value if offer_caption_id(value) is not None else None


def _draft_name(title):
    match = _DRAFT_TITLE.fullmatch(title.strip())
    return re.sub(r"\s+", "", match[1]).casefold() if match else None


def scoped_position_stage(scene, scope):
    stage = stage_of(scene)
    if stage == "windowhub_unmapped" and isinstance(scope, NewOfferHandoff):
        title = scene.observation.state.active_window_title or ""
        if _draft_name(title):
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

    def _workspace(self, scene, api):
        """Match the selected tab and the linked native child or main caption."""
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
        return bool(draft and draft == _draft_name(selected) and draft == _draft_name(frame_title))

    def verify(self, scene, api, *, entry=False, follows=None):
        """Return the evidence source, or a diagnostic explaining the block."""
        hwnd = foreground_handle(scene, api)
        stage = scoped_position_stage(scene, self)
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
