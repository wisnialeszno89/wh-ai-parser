from types import SimpleNamespace

from app.agent.runtime.windowhub_customer_grid_inspection import _rows_from_grid


class Grid:
    def __init__(self, rows, headers):
        self.rows = rows
        self.iface_grid = SimpleNamespace(
            CurrentRowCount=len(rows),
            CurrentColumnCount=len(headers),
            GetItem=self.get_item,
        )
        self.iface_table = SimpleNamespace(
            GetCurrentColumnHeaders=lambda: [
                SimpleNamespace(CurrentName=header) for header in headers
            ],
        )

    def get_item(self, row, column):
        return SimpleNamespace(CurrentName=self.rows[row][column])


def test_fully_blank_row_is_not_the_same_as_unnamed_real_customer():
    grid = Grid(
        [
            ["", "", "", ""],
            ["", "55 Pułku Piechoty", "", "Leszno"],
            ["Müller", "Teststrasse", "12345", "Berlin"],
        ],
        ["Imię", "Ulica", "Kod", "Miasto"],
    )
    result = _rows_from_grid(grid)
    assert result.status == "grid_read"
    assert result.blank_name_candidate_indices == (0, 1)
    assert result.fully_blank_candidate_indices == (0,)
    assert result.reported_rows == 3


def test_unlabeled_grid_still_detects_blank_row_but_not_name_candidates():
    result = _rows_from_grid(
        Grid([["", ""], ["", "Known address"]], ["", ""])
    )
    assert result.fully_blank_candidate_indices == (0,)
    assert result.blank_name_candidate_indices == ()


def test_multiple_blank_rows_report_ambiguity_without_selecting_anyone():
    result = _rows_from_grid(
        Grid([["", ""], ["", ""]], ["Nazwa", "Ulica"])
    )
    assert result.fully_blank_candidate_indices == (0, 1)
    assert result.grid_count == 1


def test_row_scan_respects_limit():
    result = _rows_from_grid(Grid([[""] for _ in range(20)], ["Nazwa"]), max_rows=5)
    assert result.inspected_rows == 5
    assert len(result.fully_blank_candidate_indices) == 5


def test_unreadable_cell_is_not_mistaken_for_empty_client():
    class UnreadableGrid(Grid):
        def get_item(self, row, column):
            return object()
    result = _rows_from_grid(UnreadableGrid([[""]], ["Nazwa"]))
    assert result.fully_blank_candidate_indices == ()
    assert result.blank_name_candidate_indices == ()


def test_blank_candidate_requires_complete_grid_and_one_fully_empty_record():
    from app.agent.runtime.windowhub_customer_grid_inspection import (
        resolve_blank_customer_candidate,
    )
    complete = _rows_from_grid(
        Grid([["", ""], ["Firma", "Adres"]], ["Nazwa", "Ulica"]),
        max_rows=10,
    )
    decision = resolve_blank_customer_candidate(complete)
    assert decision.status == "candidate_only"
    assert decision.row_index == 0

    partial = _rows_from_grid(
        Grid([["", ""] for _ in range(20)], ["Nazwa", "Ulica"]),
        max_rows=2,
    )
    assert resolve_blank_customer_candidate(partial).status == "partial_page"

    ambiguous = _rows_from_grid(
        Grid([["", ""], ["", ""]], ["Nazwa", "Ulica"])
    )
    assert resolve_blank_customer_candidate(ambiguous).status == "not_unique"
