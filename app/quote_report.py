from __future__ import annotations

from app.decision.decision_result import DecisionResult
from app.decision.decision_trace import DecisionKind
from app.quote_orchestrator import ItemStatus, QuoteItem, QuoteReport


class SalesmanQuoteReport:
    """Render a compact human-readable report for a salesman."""

    def preflight(self, items: list[QuoteItem]) -> str:
        lines = ["PRE-FLIGHT WYCENY", ""]
        ready = 0
        attention = 0
        skipped = 0

        for item in items:
            if item.status == ItemStatus.SKIPPED:
                skipped += 1
                label = "POMINIĘTA"
            elif item.issues:
                attention += 1
                label = "WYMAGA UWAGI"
            else:
                ready += 1
                label = "OK"

            lines.append(f"{label} — Pozycja {item.item_id}")
            for issue in item.issues:
                lines.append(
                    f"  [{issue.severity.value.upper()}] "
                    f"{issue.code}: {issue.message}"
                )
            if not item.issues:
                lines.append(
                    "  Brak problemów wykrytych przed wykonaniem."
                )
            lines.append("")

        lines.extend(
            [
                "PODSUMOWANIE",
                f"Gotowe: {ready}",
                f"Wymagają uwagi: {attention}",
                f"Pominięte: {skipped}",
            ]
        )
        return "\n".join(lines)

    def decisions(self, result: DecisionResult) -> str:
        lines = [
            "ŹRÓDŁA INFORMACJI",
            "",
        ]

        for trace in result.trace:
            if trace.kind == DecisionKind.FACT:
                label = "fakt"
            elif trace.kind == DecisionKind.DEFAULT:
                label = "wartość domyślna"
            elif trace.kind == DecisionKind.SALESMAN_DECISION:
                label = "decyzja handlowca"
            elif trace.kind == DecisionKind.COMPATIBILITY:
                label = "kompatybilność"
            elif trace.kind == DecisionKind.RULE:
                label = "reguła"
            else:
                label = "brak danych"

            lines.append(
                f"{trace.field}: {trace.value} — {label}"
            )

        if not result.trace:
            lines.append("Brak zarejestrowanych decyzji.")

        return "\n".join(lines)

    def final(self, report: QuoteReport) -> str:
        lines = [
            "RAPORT WYCENY",
            "",
            f"Wykonane: {len(report.completed)}",
            f"Pominięte: {len(report.skipped)}",
            f"Nieudane: {len(report.failed)}",
        ]
        if report.completed:
            lines.append(f"  OK: {', '.join(report.completed)}")
        if report.skipped:
            lines.append(f"  POMINIĘTE: {', '.join(report.skipped)}")
        if report.failed:
            lines.append(f"  BŁĘDY: {', '.join(report.failed)}")
        return "\n".join(lines)
