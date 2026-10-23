from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from app.agent.adapters.excel_workbook_adapter import ExcelWorkbookAdapter
from app.agent.adapters.excel_annual_xy_aggregation import (
    AnnualXYAggregationError,
    ExcelAnnualXYAggregationService,
)


def make_adapter(root):
    root.mkdir(parents=True, exist_ok=True)
    return ExcelWorkbookAdapter(allowed_roots=(root,))


def make_xlsx(adapter, path, rows, *, sheet="Monthly"):
    adapter.create(path, sheets=(sheet,))
    adapter.write_range(
        path,
        sheet=sheet,
        start_cell="A1",
        values=tuple(tuple(row) for row in rows),
    )
    return path


def test_annual_xy_aggregation_from_xlsx_uses_iso_dates_writes_new_file_and_verifies(tmp_path):
    root = tmp_path / "approved"
    adapter = make_adapter(root)
    source = make_xlsx(
        adapter,
        root / "monthly.xlsx",
        [
            ("Month", "Units", "Revenue", "Units unit", "Revenue unit"),
            (datetime(2024, 1, 1), 10, 125.5, "pcs", "PLN"),
            (datetime(2024, 2, 1), 20, 200.5, "pcs", "PLN"),
            (datetime(2025, 1, 1), 5, 80, "pcs", "PLN"),
        ],
    )

    result = ExcelAnnualXYAggregationService(adapter=adapter).aggregate(
        source,
        sheet="Monthly",
        period_column="Month",
        x_column="Units",
        y_column="Revenue",
        x_unit_column="Units unit",
        y_unit_column="Revenue unit",
        operation="sum",
    )

    assert [row.year for row in result.rows] == [2024, 2025]
    assert [(row.x_value, row.y_value) for row in result.rows] == [
        (Decimal("30"), Decimal("326.0")),
        (Decimal("5"), Decimal("80")),
    ]
    assert [row.period_count for row in result.rows] == [2, 1]
    assert result.output_verified is True
    assert result.unit_validation_status == "verified_from_columns"
    assert result.output_path != source
    assert result.output_path.exists()

    summary = adapter.read_table(
        result.output_path,
        sheet="Annual Summary",
    )
    assert summary.rows[0] == (2024, 30, 326, "pcs", "PLN", 2, 2)
    assert summary.rows[1] == (2025, 5, 80, "pcs", "PLN", 1, 1)

    report = adapter.read_table(
        result.output_path,
        sheet="Validation Report",
    )
    report_map = {row[0]: row[1] for row in report.rows if len(row) >= 2}
    assert report_map["output_verification"] == "passed"
    assert report_map["unit_validation_status"] == "verified_from_columns"

    # The source workbook remains untouched.
    original = adapter.read_range(
        source,
        sheet="Monthly",
        cell_range="A1:E4",
    )
    assert len(original.values) == 4
    assert original.values[1][1:3] == (10, 125.5)


def test_annual_xy_aggregation_reads_semicolon_csv_and_uses_explicit_mean(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "monthly.csv"
    source.write_text(
        "Period;X total;Y total\n"
        "2024-01;1,5;10\n"
        "2024-02;2,5;20\n"
        "2024-03;3;30\n",
        encoding="utf-8",
    )
    service = ExcelAnnualXYAggregationService(adapter=make_adapter(root))

    result = service.aggregate(
        source,
        period_column="Period",
        x_column="X total",
        y_column="Y total",
        operation="mean",
    )

    assert len(result.rows) == 1
    assert result.rows[0].year == 2024
    assert result.rows[0].x_value == Decimal("7") / Decimal("3")
    assert result.rows[0].y_value == Decimal("20")
    assert result.unit_validation_status == "not_provided"
    assert result.caveats
    assert result.output_verified is True
    assert result.output_path.suffix == ".xlsx"


def test_duplicate_periods_are_rejected_unless_include_policy_is_explicit(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "duplicates.csv"
    source.write_text(
        "Month,X,Y\n"
        "2024-01,1,10\n"
        "01/2024,2,20\n",
        encoding="utf-8",
    )
    service = ExcelAnnualXYAggregationService(adapter=make_adapter(root))

    with pytest.raises(AnnualXYAggregationError) as raised:
        service.aggregate(
            source,
            period_column="Month",
            x_column="X",
            y_column="Y",
        )
    assert raised.value.code == "duplicate_periods"
    assert raised.value.row_numbers == (2, 3)
    assert not (root / "duplicates-annual-xy-summary.xlsx").exists()

    included = service.aggregate(
        source,
        period_column="Month",
        x_column="X",
        y_column="Y",
        duplicate_period_policy="include",
    )
    assert included.rows[0].x_value == Decimal("3")
    assert included.rows[0].y_value == Decimal("30")
    assert included.duplicate_period_count == 1


def test_missing_values_fail_closed_or_skip_whole_rows_by_explicit_policy(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "missing.csv"
    source.write_text(
        "Month,X,Y\n"
        "2024-01,1,10\n"
        "2024-02,,20\n"
        "2024-03,3,30\n",
        encoding="utf-8",
    )
    service = ExcelAnnualXYAggregationService(adapter=make_adapter(root))

    with pytest.raises(AnnualXYAggregationError) as raised:
        service.aggregate(source, period_column="Month", x_column="X", y_column="Y")
    assert raised.value.code == "missing_required_value"
    assert raised.value.row_numbers == (3,)

    result = service.aggregate(
        source,
        period_column="Month",
        x_column="X",
        y_column="Y",
        missing_value_policy="skip_rows",
    )
    assert result.accepted_rows == 2
    assert result.missing_rows_skipped == 1
    assert result.skipped_row_numbers == (3,)
    assert result.rows[0].x_value == Decimal("4")
    assert result.rows[0].y_value == Decimal("40")


def test_incompatible_units_block_output_and_mixed_columns_are_not_converted(tmp_path):
    root = tmp_path / "approved"
    adapter = make_adapter(root)
    source = make_xlsx(
        adapter,
        root / "unit-conflict.xlsx",
        [
            ("Month", "X", "Y", "X Unit"),
            ("2024-01", 10, 100, "kg"),
            ("2024-02", 20, 200, "tonne"),
        ],
    )

    with pytest.raises(AnnualXYAggregationError) as raised:
        ExcelAnnualXYAggregationService(adapter=adapter).aggregate(
            source,
            sheet="Monthly",
            period_column="Month",
            x_column="X",
            y_column="Y",
            x_unit_column="X Unit",
        )
    assert raised.value.code == "incompatible_x_units"
    assert not (root / "unit-conflict-annual-xy-summary.xlsx").exists()


def test_invalid_columns_duplicate_headers_and_bad_periods_are_rejected(tmp_path):
    root = tmp_path / "approved"
    adapter = make_adapter(root)
    source = make_xlsx(
        adapter,
        root / "bad.xlsx",
        [
            ("Period", "X", "X"),
            ("2024-01", 1, 10),
        ],
    )
    service = ExcelAnnualXYAggregationService(adapter=adapter)

    with pytest.raises(AnnualXYAggregationError) as duplicate_header:
        service.aggregate(
            source,
            sheet="Monthly",
            period_column="Period",
            x_column="X",
            y_column=3,
        )
    assert duplicate_header.value.code == "duplicate_headers"

    with pytest.raises(AnnualXYAggregationError) as out_of_range:
        service.aggregate(
            source,
            sheet="Monthly",
            period_column=1,
            x_column=2,
            y_column=4,
        )
    assert out_of_range.value.code == "column_out_of_range"

    period_source = root / "bad-period.csv"
    period_source.write_text(
        "Period,X,Y\n"
        "45292,1,2\n",
        encoding="utf-8",
    )
    with pytest.raises(AnnualXYAggregationError) as bad_period:
        service.aggregate(
            period_source,
            period_column="Period",
            x_column="X",
            y_column="Y",
        )
    assert bad_period.value.code == "ambiguous_numeric_period"


def test_source_roots_output_overwrite_and_file_type_are_enforced(tmp_path):
    approved = tmp_path / "approved"
    adapter = make_adapter(approved)
    outside = tmp_path / "outside.csv"
    outside.write_text("Period,X,Y\n2024-01,1,2\n", encoding="utf-8")
    service = ExcelAnnualXYAggregationService(adapter=adapter)

    with pytest.raises(PermissionError):
        service.aggregate(
            outside,
            period_column="Period",
            x_column="X",
            y_column="Y",
        )

    source = approved / "safe.csv"
    source.write_text("Period,X,Y\n2024-01,1,2\n", encoding="utf-8")

    with pytest.raises(AnnualXYAggregationError) as same_path:
        service.aggregate(
            source,
            period_column="Period",
            x_column="X",
            y_column="Y",
            output_path=source,
        )
    assert same_path.value.code == "source_overwrite_blocked"

    existing_output = approved / "existing.xlsx"
    adapter.create(existing_output)
    with pytest.raises(FileExistsError):
        service.aggregate(
            source,
            period_column="Period",
            x_column="X",
            y_column="Y",
            output_path=existing_output,
        )

    with pytest.raises(AnnualXYAggregationError) as bad_output:
        service.aggregate(
            source,
            period_column="Period",
            x_column="X",
            y_column="Y",
            output_path=approved / "summary.csv",
        )
    assert bad_output.value.code == "invalid_output_type"


def test_read_table_preserves_internal_blank_rows_and_enforces_row_budget(tmp_path):
    root = tmp_path / "approved"
    adapter = make_adapter(root)
    source = make_xlsx(
        adapter,
        root / "table.xlsx",
        [
            ("Period", "X", "Y"),
            ("2024-01", 1, 10),
            (None, None, None),
            ("2024-03", 3, 30),
        ],
    )

    table = adapter.read_table(source, sheet="Monthly")
    assert table.row_numbers == (2, 3, 4)
    assert table.rows[1] == (None, None, None)

    with pytest.raises(ValueError, match="data-row budget"):
        adapter.read_table(
            source,
            sheet="Monthly",
            max_data_rows=2,
        )
