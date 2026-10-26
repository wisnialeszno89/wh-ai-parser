"""Explicitly gated live PDF -> WindowHub draft-only test.

This tool does not upload the source PDF or its extracted full text. The user
must explicitly enable live execution, acknowledge remote reasoning, and type
an approval phrase after reviewing locally validated quote facts. Each runner
advance is bounded to one observe/plan/validate/execute/verify cycle. Pending
submission/confirmation actions are never approved by this tool.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
import os
import re
import sys
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.adapters.pdf_document_adapter import (
    PdfDocumentAdapter,
    PdfDocumentError,
)
from app.agent.adapters.pdf_ingestion_service import PdfIngestionService
from app.agent.runtime.resumable_task import TaskStatus
from app.agent.runtime.windowhub_agent_runtime import (
    create_windowhub_agent_runtime,
)


_PREVIEW_FIELDS = ("product_type", "width", "height", "quantity")
_REQUIRED_FINAL_FIELDS = frozenset({"product_type", "width", "height"})
_SUBMISSION_MARKERS = re.compile(
    r"(?<!\w)(submit|dispatch|send|publish|confirm|approve|finalize|finalise|"
    r"wyślij|wyslij|przekaż|przekaz|zatwierdź|zatwierdz|finalizuj)(?!\w)",
    re.IGNORECASE,
)
_SAVE_MARKERS = re.compile(
    r"(?<!\w)(save|saved|draft|zapisz|zapis|zachowaj|szkic)(?!\w)",
    re.IGNORECASE,
)
_TERMINAL_STATUSES = frozenset({
    TaskStatus.COMPLETED,
    TaskStatus.STOPPED,
    TaskStatus.WAITING_FOR_INPUT,
    TaskStatus.WAITING_FOR_CONFIRMATION,
    TaskStatus.WAITING_FOR_APPROVAL,
})


class _CountingControlLoop:
    """Count calls so this CLI can prove preparation did not observe/act."""

    def __init__(self, delegate) -> None:
        self._delegate = delegate
        self.observe_calls = 0
        self.run_calls = 0

    def observe_scene(self, *args, **kwargs):
        self.observe_calls += 1
        return self._delegate.observe_scene(*args, **kwargs)

    def run(self, *args, **kwargs):
        self.run_calls += 1
        return self._delegate.run(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._delegate, name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create and independently verify one real WindowHub draft from "
            "a locally approved PDF. Never submits or sends the offer."
        )
    )
    parser.add_argument("--pdf", required=True, help="Explicit local PDF path.")
    parser.add_argument(
        "--approved-root",
        required=True,
        help="Exact local directory approved to supply the PDF.",
    )
    parser.add_argument(
        "--task-id",
        default=None,
        help="Optional unique checkpoint ID. A generated ID is safer for a new test.",
    )
    parser.add_argument(
        "--checkpoint-dir",
        default=None,
        help="Optional local directory for resumable task checkpoints.",
    )
    parser.add_argument(
        "--max-actions",
        type=int,
        default=8,
        help="Maximum GUI actions in this run (1..8; default 8).",
    )
    parser.add_argument(
        "--max-reasoning-calls",
        type=int,
        default=8,
        help="Maximum planner calls persisted with the checkpoint (1..8).",
    )
    parser.add_argument(
        "--allow-remote-reasoning",
        action="store_true",
        required=True,
        help=(
            "Acknowledge that validated quote facts and current WindowHub scene "
            "context may be sent to the configured remote reasoning provider. "
            "The full PDF text/citations are not inserted into the task prompt."
        ),
    )
    parser.add_argument(
        "--confirm-live-draft-only",
        action="store_true",
        required=True,
        help="Explicitly authorize the tool to offer a live draft-only test.",
    )
    return parser.parse_args()


def _preview(preparation) -> dict[str, object]:
    """Return only validated field values and page references, never raw excerpts."""
    normalized = preparation.validation.normalized_values
    facts = {
        key: normalized[key]
        for key in _PREVIEW_FIELDS
        if key in normalized
    }
    pages_by_field: dict[str, list[int]] = {}
    for fact in preparation.extraction.facts:
        field_name = getattr(fact, "field_name", None)
        source = getattr(fact, "source", None)
        page_number = getattr(source, "page_number", None)
        if (
            isinstance(field_name, str)
            and field_name in facts
            and isinstance(page_number, int)
            and not isinstance(page_number, bool)
            and page_number > 0
        ):
            pages_by_field.setdefault(field_name, []).append(page_number)
    return {
        "validated_facts": facts,
        "source_pages_by_field": {
            key: sorted(set(value))
            for key, value in sorted(pages_by_field.items())
        },
        "page_count": getattr(preparation.extraction, "page_count", None),
        "ocr_required_pages": list(
            getattr(preparation.extraction, "ocr_pages", ()) or ()
        ),
        "manual_review_required": bool(preparation.requires_manual_review),
        "missing_field_names": sorted(
            str(value) for value in (preparation.validation.missing_fields or ())
        ),
        "conflict_field_names": sorted({
            str(getattr(item, "field_name", "unknown"))
            for item in (preparation.validation.conflicts or ())
        }),
    }


def _contains_submission_marker(checkpoint) -> bool:
    for step in getattr(checkpoint, "steps", ()):
        if _SUBMISSION_MARKERS.search(
            f"{getattr(step, 'action_name', '')} {getattr(step, 'requested_target', '')}"
        ):
            return True
    return False


def _has_verified_draft_save(checkpoint) -> bool:
    """Require a verified semantic save action before reporting draft success."""
    for step in getattr(checkpoint, "completed_steps", ()):
        text = (
            f"{getattr(step, 'action_name', '')} "
            f"{getattr(step, 'requested_target', '')} "
            f"{getattr(step, 'actual_target', '') or ''}"
        )
        if _SAVE_MARKERS.search(text) and not _SUBMISSION_MARKERS.search(text):
            return True
    return False


def _verified_final_fields(checkpoint) -> set[str]:
    evidence = getattr(checkpoint, "final_evidence", ()) or ()
    return {
        str(item.get("field"))
        for item in evidence
        if isinstance(item, Mapping) and isinstance(item.get("field"), str)
    }


def _print_checkpoint(checkpoint, cycle: int | None = None) -> None:
    if cycle is not None:
        print(f"cycle: {cycle}")
    print(f"task_status: {checkpoint.status.value}")
    print(f"actions_used: {checkpoint.actions_used}")
    print(f"verified_steps: {len(checkpoint.completed_steps)}")
    print(f"draft_only: {checkpoint.draft_only}")
    print(f"execution_approved: {checkpoint.execution_approved}")
    print(f"pending_confirmation: {checkpoint.status is TaskStatus.WAITING_FOR_CONFIRMATION}")
    print(f"stop_reason_present: {bool(checkpoint.stop_reason)}")


def _build_runtime(pdf_service: PdfIngestionService, args: argparse.Namespace):
    from app.agent.runtime.windowhub_agent_control_loop import (
        create_windowhub_agent_control_loop,
    )

    def control_loop_factory(*, plan_reasoner):
        delegate = create_windowhub_agent_control_loop(plan_reasoner=plan_reasoner)
        return _CountingControlLoop(delegate)

    checkpoint_env = "AGENT_TASK_CHECKPOINT_STORE_DIR"
    previous_checkpoint_dir = os.environ.get(checkpoint_env)
    if args.checkpoint_dir:
        os.environ[checkpoint_env] = str(Path(args.checkpoint_dir).expanduser().resolve())

    try:
        runtime = create_windowhub_agent_runtime(
            control_loop_factory=control_loop_factory,
            pdf_ingestion_service=pdf_service,
        )
    finally:
        if args.checkpoint_dir:
            if previous_checkpoint_dir is None:
                os.environ.pop(checkpoint_env, None)
            else:
                os.environ[checkpoint_env] = previous_checkpoint_dir
    return runtime


def main() -> int:
    load_dotenv()
    args = parse_args()

    if os.name != "nt":
        print("result: ABORTED")
        print("reason: windows_required")
        return 2
    if os.environ.get("WH_REAL_WINDOWHUB", "").strip() != "1":
        print("result: ABORTED")
        print("reason: explicit_live_mode_required")
        print("hint: set WH_REAL_WINDOWHUB=1 only for this controlled draft test")
        return 2
    if not (
        os.environ.get("NAVIMIND_AGENT_URL", "").strip()
        or os.environ.get("AGENT_TASK_REASONING", "").strip() == "1"
    ):
        print("result: ABORTED")
        print("reason: task_reasoner_not_configured")
        return 2
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print("result: ABORTED")
        print("reason: plan_reasoner_credentials_not_configured")
        return 2
    if not sys.stdin.isatty():
        print("result: ABORTED")
        print("reason: interactive_confirmation_required")
        return 2
    if not 1 <= args.max_actions <= 8:
        print("result: ABORTED")
        print("reason: max_actions_out_of_range")
        return 2
    if not 1 <= args.max_reasoning_calls <= 8:
        print("result: ABORTED")
        print("reason: max_reasoning_calls_out_of_range")
        return 2

    try:
        approved_root = Path(args.approved_root).expanduser().resolve(strict=True)
        if not approved_root.is_dir():
            print("result: ABORTED")
            print("reason: approved_root_not_directory")
            return 2

        pdf_adapter = PdfDocumentAdapter(allowed_roots=(approved_root,))
        pdf_service = PdfIngestionService(adapter=pdf_adapter)
        runtime = _build_runtime(pdf_service, args)
        control = runtime.control_loop
    except Exception as exc:
        print("result: ABORTED")
        print(f"error_type: {type(exc).__name__}")
        print("error_details_printed: 0")
        return 2

    task_id = args.task_id or f"live-pdf-draft-{uuid4().hex[:16]}"
    if runtime.get_resumable_task(task_id) is not None:
        print("result: ABORTED")
        print("reason: task_id_already_exists")
        print("existing_checkpoint_modified: False")
        return 2

    source_alias = f"approved-pdf-{uuid4().hex[:12]}.pdf"
    request_message = (
        "Prepare a draft WindowHub offer using only the validated facts from the "
        "supplied PDF."
    )

    try:
        extraction = runtime.ingest_pdf(args.pdf, source_alias=source_alias)
        preparation = runtime.prepare_pdf_quote(
            source_alias,
            request_message=request_message,
        )
    except PdfDocumentError as exc:
        print("result: ABORTED")
        print(f"pdf_error_code: {exc.code}")
        print("pdf_path_printed: 0")
        return 3
    except Exception as exc:
        print("result: ABORTED")
        print(f"error_type: {type(exc).__name__}")
        print("error_details_printed: 0")
        return 3

    preview = _preview(preparation)
    print("mode: LIVE_DRAFT_ONLY_PENDING_USER_APPROVAL")
    print("source_pdf_uploaded: False")
    print("full_pdf_text_in_task_prompt: False")
    print("remote_reasoning_enabled_by_explicit_flag: True")
    print("current_ui_context_may_be_sent_to_remote_reasoner: True")
    print("pdf_extraction_status: " + str(extraction.status))
    print("pdf_page_count: " + str(extraction.page_count))
    print("pdf_needs_ocr: " + str(extraction.needs_ocr))
    print("task_id: " + task_id)
    print("local_fact_preview: " + json.dumps(preview, ensure_ascii=False, sort_keys=True))
    print(f"control_loop_observations_before_approval: {control.observe_calls}")
    print(f"control_loop_runs_before_approval: {control.run_calls}")

    if (
        not preparation.can_continue_to_offer_workflow
        or preparation.requires_manual_review
    ):
        print("result: MANUAL_REVIEW_REQUIRED")
        print("task_checkpoint_created: False")
        return 4

    if control.observe_calls != 0 or control.run_calls != 0:
        print("result: ABORTED")
        print("reason: unexpected_preapproval_gui_activity")
        return 5

    print()
    print("LIVE EFFECTS: may create and save one draft offer in WindowHub.")
    print("The script will not approve an action requiring confirmation and will never approve submission.")
    print("Check the fact values and page references above, and ensure the intended WindowHub window is open.")
    print("To proceed, type exactly: APPROVE DRAFT-ONLY WINDOWHUB TEST")
    try:
        entered = input("> ")
    except EOFError:
        entered = ""
    if entered != "APPROVE DRAFT-ONLY WINDOWHUB TEST":
        print("result: CANCELLED")
        print("task_checkpoint_created: False")
        print("control_loop_observations: 0")
        print("gui_actions_executed: 0")
        return 0

    try:
        started = runtime.start_pdf_quote_task(
            source_alias,
            request_message=request_message,
            task_id=task_id,
            max_actions=args.max_actions,
            max_reasoning_calls=args.max_reasoning_calls,
        )
        checkpoint = started.checkpoint
        if (
            not started.task_created
            or started.requires_manual_review
            or checkpoint is None
            or checkpoint.status is not TaskStatus.WAITING_FOR_APPROVAL
            or checkpoint.approval_required is not True
            or checkpoint.execution_approved is not False
            or checkpoint.draft_only is not True
        ):
            print("result: ABORTED")
            print("reason: approval_checkpoint_contract_failed")
            print("task_checkpoint_created: " + str(checkpoint is not None))
            return 5

        if control.observe_calls != 0 or control.run_calls != 0:
            print("result: ABORTED")
            print("reason: unexpected_preapproval_gui_activity")
            return 5

        approved = runtime.approve_resumable_task_execution(task_id)
        if (
            approved.status is not TaskStatus.READY
            or approved.execution_approved is not True
            or approved.draft_only is not True
        ):
            print("result: ABORTED")
            print("reason: task_approval_state_invalid")
            return 5

        current = approved
        for cycle in range(1, args.max_reasoning_calls + args.max_actions + 2):
            if current.status in _TERMINAL_STATUSES:
                break
            current = runtime.advance_resumable_task(task_id)
            _print_checkpoint(current, cycle)
            if current.draft_only is not True:
                print("result: STOPPED_UNSAFE_DRAFT_FLAG")
                return 6
            if _contains_submission_marker(current):
                print("result: STOPPED_SUBMISSION_MARKER_DETECTED")
                print("submission_action_approved_by_tool: False")
                return 6
            if current.status in _TERMINAL_STATUSES:
                break

        print()
        _print_checkpoint(current)
        if current.status is TaskStatus.WAITING_FOR_CONFIRMATION:
            print("result: STOPPED_FOR_ACTION_CONFIRMATION")
            print("pending_action_was_auto_approved: False")
            print("next_step: inspect the checkpoint manually; this tool will not approve it")
            return 7

        if current.status is not TaskStatus.COMPLETED:
            print("result: INCOMPLETE")
            print("final_verification_complete: False")
            return 8

        verified_fields = _verified_final_fields(current)
        save_action_verified = _has_verified_draft_save(current)
        if (
            current.draft_only is not True
            or not _REQUIRED_FINAL_FIELDS.issubset(verified_fields)
            or not save_action_verified
            or _contains_submission_marker(current)
        ):
            print("result: COMPLETED_WITHOUT_REQUIRED_DRAFT_VERIFICATION")
            print("final_verified_fields: " + json.dumps(sorted(verified_fields)))
            print(f"draft_save_action_verified: {save_action_verified}")
            return 9

        print("final_verified_fields: " + json.dumps(sorted(verified_fields)))
        print("draft_save_action_verified: True")
        print("result: PASS")
        print("draft_created_or_saved: True")
        print("submission_or_send_attempted_by_tool: False")
        print("raw_pdf_text_printed: 0")
        return 0
    except Exception as exc:
        # Error text can contain UI labels or local path fragments; keep logs redacted.
        print("result: FAILED")
        print(f"error_type: {type(exc).__name__}")
        print("error_details_printed: 0")
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
