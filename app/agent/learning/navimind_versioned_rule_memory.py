"""Versioned, atomic JSON storage for operator-approved NaviMind learning rules.

Portable to Windows and Linux. This layer NEVER reads or edits a WindowHub
document; it stores only rule metadata. SHA-256 detects accidental corruption,
not malicious tampering. Do not store credentials or customer document data.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

from app.agent.learning.navimind_correction_rulebook import (
    LearningScope, RuleBook, RuleCandidate, RuleRecord, RuleState, RuleTestReport,
)

SCHEMA = "navimind.learning.rulebook.v1"
MAX_BYTES = 1_000_000
MAX_RULES = 2000


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _text(value: object, name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()) or len(value) > 10000:
        raise ValueError("invalid_" + name)
    return value


def _scope_from_data(value: object) -> LearningScope:
    if not isinstance(value, dict) or set(value) != {"application", "workflow", "field", "context_tags"}:
        raise ValueError("invalid_scope")
    tags = value["context_tags"]
    if not isinstance(tags, list) or len(tags) > 30 or not all(
        isinstance(tag, str) and 0 < len(tag) <= 100 for tag in tags
    ):
        raise ValueError("invalid_scope_tags")
    return LearningScope(
        _text(value["application"], "application"),
        _text(value["workflow"], "workflow"),
        _text(value["field"], "field"), tuple(tags),
    )


def _record_to_data(record: RuleRecord) -> dict:
    c = record.candidate
    report = record.tested_report
    return {
        "rule_id": c.rule_id,
        "scope": {
            "application": c.scope.application,
            "workflow": c.scope.workflow,
            "field": c.scope.field,
            "context_tags": list(c.scope.context_tags),
        },
        "match_value": c.match_value,
        "replacement_value": c.replacement_value,
        "correction_id": c.correction_id,
        "state": record.state.value,
        "approved_by": record.approved_by,
        "test_report": None if report is None else {
            "rule_id": report.rule_id,
            "passed": report.passed,
            "failed": report.failed,
            "unverified": report.unverified,
            "positive_passed": report.positive_passed,
            "boundary_passed": report.boundary_passed,
            "cases": list(report.cases),
        },
        "history": list(record.history),
    }


def _record_from_data(value: object) -> RuleRecord:
    if not isinstance(value, dict) or set(value) != {
        "rule_id", "scope", "match_value", "replacement_value",
        "correction_id", "state", "approved_by", "test_report", "history",
    }:
        raise ValueError("invalid_rule_record")
    candidate = RuleCandidate(
        _text(value["rule_id"], "rule_id"),
        _scope_from_data(value["scope"]),
        _text(value["match_value"], "match_value"),
        _text(value["replacement_value"], "replacement_value"),
        _text(value["correction_id"], "correction_id"),
    )
    try:
        state = RuleState(value["state"])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_rule_state") from exc
    approved = value["approved_by"]
    if approved is not None:
        approved = _text(approved, "approver")
    raw = value["test_report"]
    report = None
    if raw is not None:
        if not isinstance(raw, dict) or set(raw) != {
            "rule_id", "passed", "failed", "unverified", "positive_passed",
            "boundary_passed", "cases",
        }:
            raise ValueError("invalid_test_report")
        for k in ("passed", "failed", "unverified", "positive_passed", "boundary_passed"):
            if type(raw[k]) is not int or not 0 <= raw[k] <= 10000:
                raise ValueError("invalid_test_counts")
        cases = raw["cases"]
        if (not isinstance(cases, list) or len(cases) > 10000
                or not all(isinstance(x, str) and x.strip() for x in cases)
                or len(set(cases)) != len(cases)):
            raise ValueError("invalid_test_cases")
        report = RuleTestReport(
            _text(raw["rule_id"], "report_rule_id"),
            raw["passed"], raw["failed"], raw["unverified"],
            raw["positive_passed"], raw["boundary_passed"], tuple(cases),
        )
        if (report.rule_id != candidate.rule_id
                or report.passed + report.failed + report.unverified != len(cases)
                or report.positive_passed + report.boundary_passed != report.passed):
            raise ValueError("inconsistent_test_report")
    history = value["history"]
    if (not isinstance(history, list) or len(history) > 1000
            or not all(isinstance(item, str) and item.strip() and len(item) <= 1000 for item in history)):
        raise ValueError("invalid_rule_history")
    if state in (RuleState.ACTIVE, RuleState.REVOKED):
        if report is None or not report.eligible_for_promotion or approved is None:
            raise ValueError("unapproved_or_untested_active_rule")
        if not any(h == "approved:" + approved for h in history):
            raise ValueError("approval_audit_missing")
        if state == RuleState.REVOKED and not any(h.startswith("revoked:") for h in history):
            raise ValueError("revocation_audit_missing")
    if state == RuleState.TESTED and (report is None or not report.eligible_for_promotion):
        raise ValueError("invalid_tested_state")
    if state == RuleState.PROPOSED and approved is not None:
        raise ValueError("proposed_rule_has_approval")
    return RuleRecord(
        candidate=candidate, state=state, tested_report=report,
        approved_by=approved, history=history,
    )


@dataclass(frozen=True)
class StoredMemory:
    book: RuleBook
    generation: int


class RuleMemoryStore:
    """One file per explicitly selected workspace; no network or auto-sync."""
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> StoredMemory:
        if not self.path.exists():
            return StoredMemory(RuleBook(), 0)
        if self.path.is_symlink():
            raise ValueError("memory_symlink_refused")
        if self.path.stat().st_size > MAX_BYTES:
            raise ValueError("memory_too_large")
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("memory_unreadable") from exc
        if not isinstance(envelope, dict) or set(envelope) != {"schema", "payload", "sha256"}:
            raise ValueError("memory_envelope_invalid")
        if envelope["schema"] != SCHEMA:
            raise ValueError("unsupported_memory_version")
        payload = envelope["payload"]
        if not isinstance(payload, dict) or set(payload) != {"generation", "rules"}:
            raise ValueError("memory_payload_invalid")
        digest = sha256(_canonical({"schema": SCHEMA, "payload": payload})).hexdigest()
        if envelope["sha256"] != digest:
            raise ValueError("memory_checksum_mismatch")
        generation = payload["generation"]
        if type(generation) is not int or generation < 1:
            raise ValueError("memory_generation_invalid")
        values = payload["rules"]
        if not isinstance(values, list) or len(values) > MAX_RULES:
            raise ValueError("memory_rule_count_invalid")
        book = RuleBook()
        for value in values:
            record = _record_from_data(value)
            rule_id = record.candidate.rule_id
            if rule_id in book.records:
                raise ValueError("duplicate_persisted_rule")
            book.records[rule_id] = record
        # Reject overlapping active rules that would cause ambiguous suggestions.
        active = [r.candidate for r in book.records.values() if r.state == RuleState.ACTIVE]
        for i, one in enumerate(active):
            for other in active[i + 1:]:
                if (one.scope.application == other.scope.application
                        and one.scope.workflow == other.scope.workflow
                        and one.scope.field == other.scope.field
                        and one.match_value == other.match_value
                        and (set(one.scope.context_tags).issubset(other.scope.context_tags)
                             or set(other.scope.context_tags).issubset(one.scope.context_tags))):
                    raise ValueError("overlapping_active_rules")
        return StoredMemory(book, generation)

    def save(self, book: RuleBook, *, expected_generation: int) -> int:
        """Compare generation and replace atomically, without a merge on conflict.

        This protects sequential updates, not concurrent writers across processes.
        Production multi-process use needs a separate OS lock / database.
        """
        if type(expected_generation) is not int or expected_generation < 0:
            raise ValueError("expected_generation_invalid")
        current = self.load()
        if current.generation != expected_generation:
            raise ValueError("memory_generation_conflict")
        if len(book.records) > MAX_RULES:
            raise ValueError("memory_rule_count_invalid")
        payload = {
            "generation": expected_generation + 1,
            "rules": [_record_to_data(book.records[k]) for k in sorted(book.records)],
        }
        envelope = {
            "schema": SCHEMA,
            "payload": payload,
            "sha256": sha256(_canonical({"schema": SCHEMA, "payload": payload})).hexdigest(),
        }
        encoded = _canonical(envelope) + b"\n"
        if len(encoded) > MAX_BYTES:
            raise ValueError("memory_too_large")
        # Validate complete candidate before touching existing memory file.
        for rule in payload["rules"]:
            _record_from_data(rule)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_symlink():
            raise ValueError("memory_symlink_refused")
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=self.path.parent, prefix=".navimind-rulebook-",
                suffix=".tmp", delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        return payload["generation"]
