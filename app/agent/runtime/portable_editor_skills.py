"""Portable, side-effect-free editor skill planning for NaviMind.

Plans writing item descriptions and attaching user-authorized photos in any
supported desktop editor. It never accesses clipboard, OS, images or windows.
A Windows adapter must verify editor identity and final content separately.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import PurePath


class EditorOperation(str, Enum):
    REPLACE_TEXT = "replace_text"
    APPEND_TEXT = "append_text"
    INSERT_IMAGE = "insert_image"


class EditorStep(str, Enum):
    WRITE = "write"
    INSPECT = "inspect"
    ASK = "ask"
    DONE = "done"


@dataclass(frozen=True)
class EditorTarget:
    application: str
    document_id: str
    position_id: str
    control_id: str
    unique: bool
    editable: bool
    supports_images: bool
    live_observed: bool


@dataclass(frozen=True)
class Attachment:
    path: str
    authorized_by_user: bool
    available: bool
    image_validated: bool

    def __post_init__(self):
        if not self.path.strip() or PurePath(self.path).name in (".", ".."):
            raise ValueError("invalid_attachment_path")


@dataclass(frozen=True)
class EditorRequest:
    operation: EditorOperation
    text: str = ""
    image: Attachment | None = None
    expected_application: str = "WindowHub"
    expected_document_id: str = ""
    expected_position_id: str = ""

    def __post_init__(self):
        if not self.expected_document_id or not self.expected_position_id:
            raise ValueError("document_and_position_required")
        if self.operation == EditorOperation.INSERT_IMAGE:
            if self.image is None or self.text:
                raise ValueError("image_request_requires_only_attachment")
        elif not self.text.strip() or self.image is not None:
            raise ValueError("text_request_requires_only_nonempty_text")


@dataclass(frozen=True)
class EditorPlan:
    step: EditorStep
    reason: str
    operation: EditorOperation | None = None
    target_control_id: str | None = None
    content_fingerprint: str | None = None
    # UI binding and verification are separate responsibilities.
    verified_written: bool = False


def plan_editor_step(request: EditorRequest, target: EditorTarget | None) -> EditorPlan:
    if target is None or not target.live_observed:
        return EditorPlan(EditorStep.INSPECT, "fresh_editor_observation_required")
    if (target.application != request.expected_application
            or target.document_id != request.expected_document_id
            or target.position_id != request.expected_position_id):
        return EditorPlan(EditorStep.INSPECT, "document_position_identity_mismatch")
    if not target.unique or not target.control_id:
        return EditorPlan(EditorStep.INSPECT, "ambiguous_editor_control")
    if not target.editable:
        return EditorPlan(EditorStep.ASK, "editor_not_editable")

    if request.operation == EditorOperation.INSERT_IMAGE:
        image = request.image
        assert image is not None
        if not image.authorized_by_user:
            return EditorPlan(EditorStep.ASK, "image_use_permission_required")
        if not image.available or not image.image_validated:
            return EditorPlan(EditorStep.INSPECT, "image_source_not_verified")
        if not target.supports_images:
            return EditorPlan(EditorStep.ASK, "editor_image_capability_not_verified")
        fingerprint = sha256(image.path.encode("utf-8")).hexdigest()[:16]
    else:
        fingerprint = sha256(request.text.encode("utf-8")).hexdigest()[:16]

    return EditorPlan(
        EditorStep.WRITE, "ready_for_locally_verified_single_editor_action",
        operation=request.operation,
        target_control_id=target.control_id,
        content_fingerprint=fingerprint,
    )


@dataclass(frozen=True)
class EditorReadback:
    same_application: bool
    same_document: bool
    same_position: bool
    same_control: bool
    independent_live_readback: bool
    observed_text: str | None = None
    image_rendered_and_identified: bool = False


def verify_editor_result(request: EditorRequest, readback: EditorReadback) -> bool:
    """Content is verified only by fresh independently measured app state."""
    if not (readback.same_application and readback.same_document
            and readback.same_position and readback.same_control
            and readback.independent_live_readback):
        return False
    if request.operation == EditorOperation.INSERT_IMAGE:
        return readback.image_rendered_and_identified
    if readback.observed_text is None:
        return False
    if request.operation == EditorOperation.REPLACE_TEXT:
        return readback.observed_text == request.text
    # Append can preserve earlier text; the newly added tail must be exact.
    return readback.observed_text.endswith(request.text)
