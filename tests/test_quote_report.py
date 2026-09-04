import unittest

from app.quote_orchestrator import ItemStatus, PreflightIssue, IssueSeverity, QuoteItem, QuoteReport
from app.quote_report import SalesmanQuoteReport


class SalesmanQuoteReportTests(unittest.TestCase):
    def test_preflight_report_shows_ready_attention_and_skipped(self) -> None:
        ready = QuoteItem("1", object())
        attention = QuoteItem(
            "2",
            object(),
            issues=[
                PreflightIssue(
                    "2", IssueSeverity.WARNING, "TEST_WARNING", "Sprawdź pozycję."
                )
            ],
        )
        skipped = QuoteItem("3", object(), status=ItemStatus.SKIPPED)
        skipped.issues = [
            PreflightIssue(
                "3", IssueSeverity.BLOCKING, "UNSUPPORTED_CELL_COUNT", "Za dużo pól."
            )
        ]

        text = SalesmanQuoteReport().preflight([ready, attention, skipped])

        self.assertIn("OK — Pozycja 1", text)
        self.assertIn("WYMAGA UWAGI — Pozycja 2", text)
        self.assertIn("POMINIĘTA — Pozycja 3", text)
        self.assertIn("UNSUPPORTED_CELL_COUNT", text)
        self.assertIn("Gotowe: 1", text)
        self.assertIn("Wymagają uwagi: 1", text)
        self.assertIn("Pominięte: 1", text)

    def test_final_report_lists_execution_results(self) -> None:
        report = QuoteReport(
            completed=("1", "2"),
            skipped=("3",),
            failed=("4",),
            issues=(),
        )

        text = SalesmanQuoteReport().final(report)

        self.assertIn("Wykonane: 2", text)
        self.assertIn("Pominięte: 1", text)
        self.assertIn("Nieudane: 1", text)
        self.assertIn("OK: 1, 2", text)
        self.assertIn("POMINIĘTE: 3", text)
        self.assertIn("BŁĘDY: 4", text)


if __name__ == "__main__":
    unittest.main()
