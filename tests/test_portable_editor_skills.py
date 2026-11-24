"""Pure unit tests for portable editor planning, safe on Linux Codespaces."""
from app.agent.runtime.portable_editor_skills import (
    Attachment, EditorOperation, EditorReadback, EditorRequest,
    EditorStep, EditorTarget, plan_editor_step, verify_editor_result,
)


def target(**override):
    props = dict(application="WindowHub", document_id="OFR/test",
                 position_id="3", control_id="description",
                 unique=True, editable=True, supports_images=False,
                 live_observed=True)
    props.update(override)
    return EditorTarget(**props)


def request(operation=EditorOperation.REPLACE_TEXT, **override):
    props = dict(operation=operation, text="Konstrukcja nietypowa; wymiary klienta 2300 x 2700 mm",
                 expected_document_id="OFR/test", expected_position_id="3")
    props.update(override)
    return EditorRequest(**props)


def test_text_planning_does_not_claim_written():
    result = plan_editor_step(request(), target())
    assert result.step == EditorStep.WRITE
    assert result.target_control_id == "description"
    assert result.content_fingerprint
    assert result.verified_written is False


def test_stale_wrong_document_wrong_position_and_ambiguous_field_are_blocked():
    cases = (None, target(live_observed=False), target(document_id="OFR/other"),
             target(position_id="4"), target(unique=False), target(control_id=""))
    for item in cases:
        assert plan_editor_step(request(), item).step == EditorStep.INSPECT


def test_read_only_editor_needs_human_not_blind_typing():
    result = plan_editor_step(request(), target(editable=False))
    assert result.step == EditorStep.ASK


def test_image_without_permission_is_not_inserted():
    image = Attachment("/workspaces/example.png", False, True, True)
    req = request(EditorOperation.INSERT_IMAGE, text="", image=image)
    result = plan_editor_step(req, target(supports_images=True))
    assert result.step == EditorStep.ASK
    assert result.reason == "image_use_permission_required"


def test_image_requires_verified_file_and_editor_capability():
    image = Attachment("/workspaces/example.png", True, True, True)
    req = request(EditorOperation.INSERT_IMAGE, text="", image=image)
    assert plan_editor_step(req, target()).reason == "editor_image_capability_not_verified"
    not_validated = Attachment("/workspaces/example.png", True, True, False)
    req2 = request(EditorOperation.INSERT_IMAGE, text="", image=not_validated)
    assert plan_editor_step(req2, target(supports_images=True)).step == EditorStep.INSPECT
    assert plan_editor_step(req, target(supports_images=True)).step == EditorStep.WRITE


def test_success_requires_fresh_independent_readback():
    req = request()
    readback = EditorReadback(True, True, True, True, False, observed_text=req.text)
    assert not verify_editor_result(req, readback)
    good = EditorReadback(True, True, True, True, True, observed_text=req.text)
    assert verify_editor_result(req, good)
    assert not verify_editor_result(req, EditorReadback(True, False, True, True, True, observed_text=req.text))


def test_append_verifies_new_tail_only():
    req = request(EditorOperation.APPEND_TEXT, text="Ostrzeżenie gwarancyjne")
    good = EditorReadback(True, True, True, True, True,
                          observed_text="Opis poprzedni\nOstrzeżenie gwarancyjne")
    assert verify_editor_result(req, good)
    assert not verify_editor_result(req, EditorReadback(True, True, True, True, True,
                                                        observed_text="Ostrzeżenie gwarancyjne\nInne"))


def test_image_verification_requires_actual_identified_rendering():
    image = Attachment("example.png", True, True, True)
    req = request(EditorOperation.INSERT_IMAGE, text="", image=image)
    assert not verify_editor_result(req, EditorReadback(True, True, True, True, True))
    assert verify_editor_result(req, EditorReadback(True, True, True, True, True,
                                                     image_rendered_and_identified=True))
