from types import SimpleNamespace
import json

from tools.live_pdf_quote_draft_smoke import (
    _contains_submission_marker,
    _has_verified_draft_save,
    _preview,
    _verified_final_fields,
)


def test_live_preview_contains_only_supported_facts_and_page_refs():
    preparation = SimpleNamespace(
        extraction=SimpleNamespace(
            facts=(
                SimpleNamespace(
                    field_name="product_type",
                    source=SimpleNamespace(page_number=1),
                    evidence_text="Product: window — private source excerpt",
                ),
                SimpleNamespace(
                    field_name="width",
                    source=SimpleNamespace(page_number=2),
                    evidence_text="Width: 1200 mm — private source excerpt",
                ),
                SimpleNamespace(
                    field_name="height",
                    source=SimpleNamespace(page_number=2),
                    evidence_text="Height: 1500 mm — private source excerpt",
                ),
            ),
            page_count=2,
            ocr_pages=(),
        ),
        validation=SimpleNamespace(
            normalized_values={
                "product_type": "window",
                "width": 1200,
                "height": 1500,
                "client_name": "Do not print this field",
            },
            missing_fields=(),
            conflicts=(),
        ),
        requires_manual_review=False,
    )

    preview = _preview(preparation)
    serialized = json.dumps(preview, ensure_ascii=False)

    assert preview["validated_facts"] == {
        "product_type": "window",
        "width": 1200,
        "height": 1500,
    }
    assert preview["source_pages_by_field"] == {
        "height": [2],
        "product_type": [1],
        "width": [2],
    }
    assert "private source excerpt" not in serialized
    assert "Do not print this field" not in serialized


def test_live_preview_falls_back_to_ingestion_page_count_when_missing():
    preparation = SimpleNamespace(
        extraction=SimpleNamespace(
            facts=(),
            page_count=None,
            ocr_pages=(),
        ),
        validation=SimpleNamespace(
            normalized_values={},
            missing_fields=(),
            conflicts=(),
        ),
        requires_manual_review=False,
    )

    preview = _preview(
        preparation,
        ingestion_result=SimpleNamespace(page_count=3),
    )

    assert preview["page_count"] == 3


def test_live_smoke_requires_a_verified_draft_save_action():
    checkpoint = SimpleNamespace(
        completed_steps=(
            SimpleNamespace(
                action_name="click_screen_element",
                requested_target="Zapisz szkic",
                actual_target="Zapisz szkic",
            ),
        ),
    )

    assert _has_verified_draft_save(checkpoint) is True


def test_live_smoke_rejects_a_target_that_combines_save_and_submission():
    checkpoint = SimpleNamespace(
        completed_steps=(
            SimpleNamespace(
                action_name="click_screen_element",
                requested_target="Zapisz i wyślij",
                actual_target="Zapisz i wyślij",
            ),
        ),
        steps=(),
    )

    assert _has_verified_draft_save(checkpoint) is False


def test_live_smoke_rejects_submission_markers_in_checkpoint_history():
    checkpoint = SimpleNamespace(
        steps=(
            SimpleNamespace(
                action_name="click_screen_element",
                requested_target="Wyślij ofertę",
            ),
        ),
    )

    assert _contains_submission_marker(checkpoint) is True


def test_live_smoke_final_verification_requires_core_quote_fields():
    checkpoint = SimpleNamespace(
        final_evidence=(
            {"field": "product_type"},
            {"field": "width"},
            {"field": "height"},
        ),
    )

    assert _verified_final_fields(checkpoint) == {
        "product_type",
        "width",
        "height",
    }
