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
