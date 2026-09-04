from app.quote_orchestrator import (
    IssueSeverity,
    ItemStatus,
    PreflightIssue,
    QuoteItem,
    QuoteOrchestrator,
)


def test_preflight_marks_only_blocking_items_as_skipped():
    items = [
        QuoteItem("1", {"size": "1000x1000"}),
        QuoteItem("2", {"size": "1500x1500"}),
    ]

    def validator(item):
        if item.item_id == "2":
            return [
                PreflightIssue(
                    item_id="2",
                    severity=IssueSeverity.BLOCKING,
                    code="DIMENSION_OUT_OF_RANGE",
                    message="dimension is outside the standard range",
                )
            ]
        return []

    prepared = QuoteOrchestrator().preflight(items, validator)

    assert prepared[0].status == ItemStatus.READY
    assert prepared[1].status == ItemStatus.SKIPPED


def test_run_continues_after_execution_failure():
    items = [
        QuoteItem("1", {}),
        QuoteItem("2", {}),
        QuoteItem("3", {}),
    ]

    def execute(item):
        if item.item_id == "2":
            raise RuntimeError("WH rejected glass")
        return True

    report = QuoteOrchestrator().run(items, execute)

    assert report.completed == ("1", "3")
    assert report.failed == ("2",)
    assert report.skipped == ()
    assert report.total == 3
    assert any(issue.code == "EXECUTION_EXCEPTION" for issue in report.issues)


def test_skipped_preflight_item_does_not_execute():
    item = QuoteItem(
        "10",
        {},
        status=ItemStatus.SKIPPED,
        issues=[
            PreflightIssue(
                item_id="10",
                severity=IssueSeverity.BLOCKING,
                code="UNKNOWN_CONSTRUCTION",
                message="construction could not be understood",
            )
        ],
    )
    called = []

    report = QuoteOrchestrator().run([item], lambda current: called.append(current.item_id) or True)

    assert called == []
    assert report.skipped == ("10",)
    assert report.completed == ()


def test_run_skips_known_wh_rejection_and_continues():
    items = [QuoteItem("1", {}), QuoteItem("2", {}), QuoteItem("3", {})]

    def execute(item):
        if item.item_id == "2":
            raise RuntimeError("too large")
        return True

    report = QuoteOrchestrator().run(
        items,
        execute,
        error_code=lambda _: "DIMENSION_TOO_LARGE",
    )

    assert report.completed == ("1", "3")
    assert report.skipped == ("2",)
    assert report.failed == ()
    assert report.issues[-1].severity == IssueSeverity.DECISION_REQUIRED


def test_run_retries_missing_dependency_and_then_succeeds():
    calls = 0

    def execute(item):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("dependency missing")
        return True

    report = QuoteOrchestrator().run(
        [QuoteItem("1", {})],
        execute,
        error_code=lambda _: "MISSING_DEPENDENCY",
    )

    assert report.completed == ("1",)
    assert report.failed == ()
    assert calls == 2


def test_unknown_wh_error_is_reported_as_failed_but_does_not_break_batch():
    items = [QuoteItem("1", {}), QuoteItem("2", {}), QuoteItem("3", {})]

    def execute(item):
        if item.item_id == "2":
            raise RuntimeError("brand new WH message")
        return True

    report = QuoteOrchestrator().run(items, execute)

    assert report.completed == ("1", "3")
    assert report.failed == ("2",)
    assert report.total == 3
    assert report.issues[-1].code == "UNKNOWN_ERROR"

