"""Portable acceptance tests for durable NaviMind rule memory."""
from __future__ import annotations

import json

import pytest

from app.agent.learning.navimind_correction_rulebook import (
    Correction, LearningScope, RuleBook, RuleCase, propose_rule, RuleState,
)
from app.agent.learning.navimind_versioned_rule_memory import (
    RuleMemoryStore, SCHEMA,
)


def scope(application="WindowHub", field="description", *tags):
    return LearningScope(application, "commercial_quote", field, tags)


def create_candidate(book: RuleBook, name="warning", application="WindowHub"):
    actual_scope = scope(application, "description", "outside_warranty")
    correction = Correction(
        name + "-correction", "DEMO/001", "1", actual_scope,
        "Oferta indywidualna", "Oferta indywidualna. Sprawdź gwarancję.",
        True, True,
    )
    candidate = propose_rule(correction, rule_id=name)
    book.propose(candidate)
    return candidate


def activate(book, candidate, approver="salesperson"):
    s = candidate.scope
    cases = (
        RuleCase("positive-1-" + candidate.rule_id, s,
                 candidate.match_value, candidate.replacement_value, True),
        RuleCase("positive-2-" + candidate.rule_id,
                 LearningScope(s.application, s.workflow, s.field,
                               s.context_tags + ("additional",)),
                 candidate.match_value, candidate.replacement_value, True),
        RuleCase("negative-" + candidate.rule_id,
                 LearningScope(s.application, s.workflow, s.field,
                               ("not_applicable",)),
                 candidate.match_value, candidate.match_value, True),
    )
    assert book.test(candidate.rule_id, cases).eligible_for_promotion
    book.approve(candidate.rule_id, approver=approver,
                 correction_id=candidate.correction_id)


def test_empty_memory_first_generation_and_restart(tmp_path):
    path = tmp_path / "memory.json"
    store = RuleMemoryStore(path)
    assert store.load().generation == 0
    book = RuleBook()
    candidate = create_candidate(book)
    activate(book, candidate)
    generation = store.save(book, expected_generation=0)
    assert generation == 1
    reopened = RuleMemoryStore(path).load()
    assert reopened.generation == 1
    assert reopened.book.records[candidate.rule_id].state == RuleState.ACTIVE
    assert reopened.book.suggest(candidate.scope, candidate.match_value) == (
        candidate.rule_id, candidate.replacement_value,
    )


def test_revocation_survives_restart(tmp_path):
    store = RuleMemoryStore(tmp_path / "memory.json")
    book = RuleBook()
    candidate = create_candidate(book)
    activate(book, candidate)
    gen = store.save(book, expected_generation=0)
    book.revoke(candidate.rule_id, operator="salesperson")
    store.save(book, expected_generation=gen)
    loaded = store.load()
    assert loaded.generation == 2
    assert loaded.book.records[candidate.rule_id].state == RuleState.REVOKED
    assert loaded.book.suggest(candidate.scope, candidate.match_value) is None


def test_separate_apps_do_not_leak_rules(tmp_path):
    store = RuleMemoryStore(tmp_path / "memory.json")
    book = RuleBook()
    window_rule = create_candidate(book, "window", "WindowHub")
    excel_rule = create_candidate(book, "excel", "Excel")
    activate(book, window_rule)
    activate(book, excel_rule)
    store.save(book, expected_generation=0)
    loaded = store.load().book
    assert loaded.suggest(window_rule.scope, window_rule.match_value)[0] == "window"
    assert loaded.suggest(excel_rule.scope, excel_rule.match_value)[0] == "excel"
    assert loaded.suggest(scope("Word", "description", "outside_warranty"),
                          window_rule.match_value) is None


def test_stale_generation_blocks_overwriting_recent_memory(tmp_path):
    store = RuleMemoryStore(tmp_path / "rules.json")
    book = RuleBook()
    create_candidate(book)
    assert store.save(book, expected_generation=0) == 1
    before = store.path.read_bytes()
    with pytest.raises(ValueError, match="memory_generation_conflict"):
        store.save(RuleBook(), expected_generation=0)
    assert store.path.read_bytes() == before


def test_corrupted_checksum_is_rejected_not_loaded(tmp_path):
    store = RuleMemoryStore(tmp_path / "rules.json")
    book = RuleBook()
    c = create_candidate(book)
    activate(book, c)
    store.save(book, expected_generation=0)
    text = store.path.read_text(encoding="utf-8")
    store.path.write_text(text.replace("Oferta indywidualna", "Błędne dane", 1),
                          encoding="utf-8")
    with pytest.raises(ValueError, match="memory_checksum_mismatch"):
        store.load()


def test_invalid_json_fails_closed_instead_of_starting_empty(tmp_path):
    store = RuleMemoryStore(tmp_path / "rules.json")
    store.path.write_text('{"schema":', encoding="utf-8")
    with pytest.raises(ValueError, match="memory_unreadable"):
        store.load()


def test_unknown_schema_does_not_silently_migrate(tmp_path):
    store = RuleMemoryStore(tmp_path / "rules.json")
    store.path.write_text(json.dumps({
        "schema": "navimind.learning.rulebook.v999",
        "payload": {"generation": 1, "rules": []}, "sha256": "x",
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported_memory_version"):
        store.load()


def test_tested_but_unapproved_rule_remains_inactive_across_restart(tmp_path):
    store = RuleMemoryStore(tmp_path / "rules.json")
    book = RuleBook()
    candidate = create_candidate(book)
    # An unapproved proposal must not become executable.
    store.save(book, expected_generation=0)
    reopened = store.load()
    assert reopened.book.records[candidate.rule_id].state == RuleState.PROPOSED
    assert reopened.book.suggest(candidate.scope, candidate.match_value) is None


def test_duplicate_rule_id_in_stored_data_rejected_even_with_valid_checksum(tmp_path):
    from hashlib import sha256
    from app.agent.learning.navimind_versioned_rule_memory import _canonical
    store = RuleMemoryStore(tmp_path / "rules.json")
    book = RuleBook()
    create_candidate(book)
    store.save(book, expected_generation=0)
    envelope = json.loads(store.path.read_text(encoding="utf-8"))
    envelope["payload"]["rules"] *= 2
    envelope["sha256"] = sha256(_canonical({
        "schema": SCHEMA, "payload": envelope["payload"],
    })).hexdigest()
    store.path.write_bytes(_canonical(envelope))
    with pytest.raises(ValueError, match="duplicate_persisted_rule"):
        store.load()


def test_zero_unverified_cases_cannot_be_faked_by_inconsistent_counters(tmp_path):
    from hashlib import sha256
    from app.agent.learning.navimind_versioned_rule_memory import _canonical
    store = RuleMemoryStore(tmp_path / "rules.json")
    book = RuleBook()
    c = create_candidate(book)
    activate(book, c)
    store.save(book, expected_generation=0)
    envelope = json.loads(store.path.read_text(encoding="utf-8"))
    report = envelope["payload"]["rules"][0]["test_report"]
    report["positive_passed"] += 1
    envelope["sha256"] = sha256(_canonical({
        "schema": SCHEMA, "payload": envelope["payload"],
    })).hexdigest()
    store.path.write_bytes(_canonical(envelope))
    with pytest.raises(ValueError, match="inconsistent_test_report"):
        store.load()


def test_missing_path_does_not_create_file_on_read(tmp_path):
    store = RuleMemoryStore(tmp_path / "folder" / "rules.json")
    assert store.load().generation == 0
    assert not store.path.exists()


def test_refuse_symlink_memory(tmp_path):
    existing = tmp_path / "target.json"
    existing.write_text("do not follow", encoding="utf-8")
    link = tmp_path / "link.json"
    try:
        link.symlink_to(existing)
    except (NotImplementedError, OSError):
        pytest.skip("symlink unsupported")
    with pytest.raises(ValueError, match="memory_symlink_refused"):
        RuleMemoryStore(link).load()
