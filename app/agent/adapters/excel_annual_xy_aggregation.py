"""Deterministic, data-first annual X/Y aggregation for approved local files.

The service reads .xlsx through ExcelWorkbookAdapter or delimited .csv from the
same configured roots. It never automates spreadsheet UI, mutates source files,
guesses ambiguous columns, silently mixes units, or overwrites an output file.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import tempfile
import re
import unicodedata
from typing import Literal

from app.agent.adapters.excel_workbook_adapter import (
    ExcelTable,
    ExcelWorkbookAdapter,
)

AggregationOperation = Literal["sum", "mean", "min", "max"]
DuplicatePeriodPolicy = Literal["reject", "include"]
MissingValuePolicy = Literal["reject", "skip_rows"]

_ALLOWED_OPERATIONS = frozenset({"sum", "mean", "min", "max"})
_ALLOWED_DUPLICATE_POLICIES = frozenset({"reject", "include"})
_ALLOWED_MISSING_POLICIES = frozenset({"reject", "skip_rows"})
_VALIDATION_SHEET = "Validation Report"
_YEAR_MIN = 1900
_YEAR_MAX = 2200
_NUMERIC_TEXT = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")
_YEAR_TEXT = re.compile(r"^(\d{4})$")
_YEAR_MONTH_TEXT = re.compile(r"^(\d{4})[-/.](\d{1,2})$")
_MONTH_YEAR_TEXT = re.compile(r"^(\d{1,2})[-/.](\d{4})$")
_YEAR_MONTH_DAY_TEXT = re.compile(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$")


class AnnualXYAggregationError(ValueError):
    """A structured, deterministic rejection of an annual aggregation request."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        row_numbers: tuple[int, ...] = (),
    ) -> None:
        super().__init__(message)
        self.code = code
        self.row_numbers = row_numbers

    def to_payload(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": str(self),
            "row_numbers": list(self.row_numbers),
        }


@dataclass(frozen=True)
class AnnualXYRow:
    year: int
    x_value: Decimal
    y_value: Decimal
    x_unit: str | None
    y_unit: str | None
    period_count: int
    input_row_count: int

    def to_payload(self) -> dict[str, object]:
        return {
            "year": self.year,
            "x_value": str(self.x_value),
            "y_value": str(self.y_value),
            "x_unit": self.x_unit,
            "y_unit": self.y_unit,
            "period_count": self.period_count,
            "input_row_count": self.input_row_count,
        }


@dataclass(frozen=True)
class AnnualXYAggregationResult:
    source_file_name: str
    source_type: str
    sheet: str | None
    output_path: Path
    output_sheet: str
    period_column: str
    x_column: str
    y_column: str
    operation: AggregationOperation
    rows: tuple[AnnualXYRow, ...]
    input_rows: int
    accepted_rows: int
    blank_rows_skipped: int
    missing_rows_skipped: int
    skipped_row_numbers: tuple[int, ...]
    duplicate_period_count: int
    duplicate_period_policy: DuplicatePeriodPolicy
    missing_value_policy: MissingValuePolicy
    unit_validation_status: str
    caveats: tuple[str, ...]
    output_verified: bool
    source_files: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, object]:
        """Return a safe summary without absolute local filesystem paths."""
        return {
            "status": "verified" if self.output_verified else "unverified",
            "source_file_name": self.source_file_name,
            "source_files": list(self.source_files or (self.source_file_name,)),
            "source_type": self.source_type,
            "sheet": self.sheet,
            "output_file_name": self.output_path.name,
            "output_sheet": self.output_sheet,
            "period_column": self.period_column,
            "x_column": self.x_column,
            "y_column": self.y_column,
            "operation": self.operation,
            "years": [row.year for row in self.rows],
            "rows": [row.to_payload() for row in self.rows],
            "input_rows": self.input_rows,
            "accepted_rows": self.accepted_rows,
            "blank_rows_skipped": self.blank_rows_skipped,
            "missing_rows_skipped": self.missing_rows_skipped,
            "skipped_row_numbers": list(self.skipped_row_numbers),
            "duplicate_period_count": self.duplicate_period_count,
            "duplicate_period_policy": self.duplicate_period_policy,
            "missing_value_policy": self.missing_value_policy,
            "unit_validation_status": self.unit_validation_status,
            "caveats": list(self.caveats),
            "output_verified": self.output_verified,
        }


@dataclass(frozen=True)
class _InputRow:
    source_row: int
    year: int
    normalized_period: str
    x_value: Decimal
    y_value: Decimal
    x_unit: str | None
    y_unit: str | None


class ExcelAnnualXYAggregationService:
    """Build and verify a new annual X/Y workbook using an approved local adapter."""

    MAX_FILE_BYTES = 32 * 1024 * 1024
    MAX_DATA_ROWS = 100_000
    MAX_COLUMNS = 256
    MAX_CSV_SAMPLE_BYTES = 16_384

    def __init__(self, *, adapter: ExcelWorkbookAdapter) -> None:
        if not isinstance(adapter, ExcelWorkbookAdapter):
            raise TypeError("ExcelAnnualXYAggregationService requires an ExcelWorkbookAdapter.")
        self.adapter = adapter

    def aggregate(
        self,
        source_path: str | Path,
        *,
        period_column: str | int,
        x_column: str | int,
        y_column: str | int,
        operation: AggregationOperation = "sum",
        sheet: str | None = None,
        header_row: int = 1,
        x_unit_column: str | int | None = None,
        y_unit_column: str | int | None = None,
        duplicate_period_policy: DuplicatePeriodPolicy = "reject",
        missing_value_policy: MissingValuePolicy = "reject",
        output_path: str | Path | None = None,
        output_sheet: str = "Annual Summary",
    ) -> AnnualXYAggregationResult:
        """Aggregate two numeric columns by year and verify a new output workbook.

        Column selectors are exact, case-insensitive header names or 1-based
        integer column numbers. Ambiguous dates, headers, duplicates, missing
        values, and incompatible units fail closed unless an explicit policy
        is supplied.
        """
        operation = self._operation(operation)
        duplicate_period_policy = self._duplicate_policy(duplicate_period_policy)
        missing_value_policy = self._missing_policy(missing_value_policy)
        self._positive_int(header_row, "header_row")
        output_sheet = self._validate_output_sheet(output_sheet)

        source = self._resolve_input_path(source_path)
        if source.stat().st_size > self.MAX_FILE_BYTES:
            raise AnnualXYAggregationError(
                "file_too_large",
                "The source file exceeds the configured 32 MiB budget.",
            )

        source_type = source.suffix.casefold()[1:]
        if source_type == "xlsx":
            table, resolved_sheet = self._read_xlsx(source, sheet, header_row)
        else:
            if sheet is not None:
                raise AnnualXYAggregationError(
                    "sheet_not_supported_for_csv",
                    "A sheet can only be selected for an .xlsx source.",
                )
            table = self._read_csv(source, header_row)
            resolved_sheet = None

        headers, rows = self._normalize_table_shape(table)
        if not headers:
            raise AnnualXYAggregationError("missing_header", "The source has no header row.")
        if len(rows) > self.MAX_DATA_ROWS:
            raise AnnualXYAggregationError("too_many_rows", "The source exceeds the configured data-row budget.")

        header_names = tuple(str(value).strip() if value is not None else "" for value in headers)
        self._validate_header_row(header_names, rows, table.row_numbers)

        period_index = self._resolve_column(period_column, header_names, "period")
        x_index = self._resolve_column(x_column, header_names, "X")
        y_index = self._resolve_column(y_column, header_names, "Y")
        x_unit_index = (
            self._resolve_column(x_unit_column, header_names, "X unit")
            if x_unit_column is not None
            else None
        )
        y_unit_index = (
            self._resolve_column(y_unit_column, header_names, "Y unit")
            if y_unit_column is not None
            else None
        )

        selected_indices = [period_index, x_index, y_index]
        if x_unit_index is not None:
            selected_indices.append(x_unit_index)
        if y_unit_index is not None:
            selected_indices.append(y_unit_index)
        if len(set(selected_indices)) != len(selected_indices):
            raise AnnualXYAggregationError(
                "columns_overlap",
                "Period, X, Y, and unit selectors must reference distinct columns.",
            )

        period_name = header_names[period_index]
        x_name = header_names[x_index]
        y_name = header_names[y_index]
        if not period_name or not x_name or not y_name:
            raise AnnualXYAggregationError(
                "missing_selected_header",
                "The selected period, X, and Y columns must have non-empty headers.",
            )

        input_row_count = len(rows)
        blank_rows_skipped = 0
        missing_rows_skipped = 0
        skipped_row_numbers: list[int] = []
        accepted: list[_InputRow] = []

        for position, row in enumerate(rows):
            row_number = table.row_numbers[position]
            if all(self._is_blank(value) for value in row):
                blank_rows_skipped += 1
                skipped_row_numbers.append(row_number)
                continue

            period_value = row[period_index] if period_index < len(row) else None
            x_raw = row[x_index] if x_index < len(row) else None
            y_raw = row[y_index] if y_index < len(row) else None
            x_unit_raw = row[x_unit_index] if x_unit_index is not None and x_unit_index < len(row) else None
            y_unit_raw = row[y_unit_index] if y_unit_index is not None and y_unit_index < len(row) else None

            required_values = [period_value, x_raw, y_raw]
            if x_unit_index is not None:
                required_values.append(x_unit_raw)
            if y_unit_index is not None:
                required_values.append(y_unit_raw)
            if any(self._is_blank(value) for value in required_values):
                if missing_value_policy == "reject":
                    raise AnnualXYAggregationError(
                        "missing_required_value",
                        "A data row has a missing period, X/Y value, or configured unit. "
                        "Use missing_value_policy='skip_rows' only when dropping the entire row is intended.",
                        row_numbers=(row_number,),
                    )
                missing_rows_skipped += 1
                skipped_row_numbers.append(row_number)
                continue

            year, normalized_period = self._parse_period(period_value, row_number)
            x_value = self._parse_number(x_raw, "X", row_number)
            y_value = self._parse_number(y_raw, "Y", row_number)
            x_unit = self._normalize_unit(x_unit_raw, "X", row_number) if x_unit_index is not None else None
            y_unit = self._normalize_unit(y_unit_raw, "Y", row_number) if y_unit_index is not None else None
            accepted.append(
                _InputRow(
                    source_row=row_number,
                    year=year,
                    normalized_period=normalized_period,
                    x_value=x_value,
                    y_value=y_value,
                    x_unit=x_unit,
                    y_unit=y_unit,
                )
            )

        if not accepted:
            raise AnnualXYAggregationError(
                "no_usable_rows",
                "No rows with a usable period and both numeric X/Y values remain.",
            )

        duplicates = Counter(item.normalized_period for item in accepted)
        duplicate_period_count = sum(count - 1 for count in duplicates.values() if count > 1)
        if duplicate_period_count and duplicate_period_policy == "reject":
            duplicate_row_numbers = tuple(
                item.source_row
                for item in accepted
                if duplicates[item.normalized_period] > 1
            )
            raise AnnualXYAggregationError(
                "duplicate_periods",
                "Duplicate normalized periods were found. Resolve them or explicitly set duplicate_period_policy='include'.",
                row_numbers=duplicate_row_numbers,
            )

        x_unit, y_unit = self._validate_units(accepted, x_unit_index is not None, y_unit_index is not None)
        unit_status = (
            "verified_from_columns"
            if x_unit_index is not None and y_unit_index is not None
            else "partially_verified_from_columns"
            if x_unit_index is not None or y_unit_index is not None
            else "not_provided"
        )

        annual: dict[int, list[_InputRow]] = defaultdict(list)
        for row in accepted:
            annual[row.year].append(row)

        annual_rows = tuple(
            AnnualXYRow(
                year=year,
                x_value=self._aggregate_decimal([item.x_value for item in year_rows], operation),
                y_value=self._aggregate_decimal([item.y_value for item in year_rows], operation),
                x_unit=x_unit,
                y_unit=y_unit,
                period_count=len({item.normalized_period for item in year_rows}),
                input_row_count=len(year_rows),
            )
            for year, year_rows in sorted(annual.items())
        )

        caveats: list[str] = []
        if unit_status == "not_provided":
            caveats.append("No unit columns were provided; within-column unit consistency cannot be independently verified.")
        elif unit_status == "partially_verified_from_columns":
            caveats.append("Only one metric has an explicit source unit column; no unit conversion was attempted.")
        if blank_rows_skipped:
            caveats.append(f"Skipped {blank_rows_skipped} fully blank data row(s).")
        if missing_rows_skipped:
            caveats.append(f"Skipped {missing_rows_skipped} row(s) with missing required values.")
        if duplicate_period_count:
            caveats.append(
                f"Included {duplicate_period_count} duplicate period occurrence(s) under the explicit include policy."
            )

        destination = self._resolve_output_path(source, output_path)
        if destination == source:
            raise AnnualXYAggregationError("source_overwrite_blocked", "The output path cannot be the source file.")
        if destination.exists():
            raise FileExistsError(destination)

        summary_header = (
            "Year",
            f"{self._excel_literal(x_name)} ({operation})",
            f"{self._excel_literal(y_name)} ({operation})",
            "X unit",
            "Y unit",
            "Distinct periods",
            "Input rows",
        )
        summary_values: tuple[tuple[object, ...], ...] = (
            summary_header,
            *(
                (
                    item.year,
                    self._excel_number(item.x_value),
                    self._excel_number(item.y_value),
                    self._excel_literal(item.x_unit) if item.x_unit else None,
                    self._excel_literal(item.y_unit) if item.y_unit else None,
                    item.period_count,
                    item.input_row_count,
                )
                for item in annual_rows
            ),
        )

        report_values: tuple[tuple[object, ...], ...] = (
            ("Metric", "Value"),
            ("source_file_name", self._excel_literal(source.name)),
            ("source_type", source_type),
            ("source_sheet", self._excel_literal(resolved_sheet) if resolved_sheet else None),
            ("period_column", self._excel_literal(period_name)),
            ("x_column", self._excel_literal(x_name)),
            ("y_column", self._excel_literal(y_name)),
            ("operation", operation),
            ("input_rows", input_row_count),
            ("accepted_rows", len(accepted)),
            ("blank_rows_skipped", blank_rows_skipped),
            ("missing_rows_skipped", missing_rows_skipped),
            ("skipped_row_numbers", ",".join(str(item) for item in skipped_row_numbers)),
            ("year_count", len(annual_rows)),
            ("years", ",".join(str(item.year) for item in annual_rows)),
            ("duplicate_period_count", duplicate_period_count),
            ("duplicate_period_policy", duplicate_period_policy),
            ("missing_value_policy", missing_value_policy),
            ("x_unit", self._excel_literal(x_unit) if x_unit else None),
            ("y_unit", self._excel_literal(y_unit) if y_unit else None),
            ("unit_validation_status", unit_status),
            ("caveats", " | ".join(caveats) if caveats else "None"),
            ("source_files", self._excel_literal(source.name)),
            ("output_verification", "pending"),
        )

        created_output = False
        try:
            self.adapter.create(
                destination,
                sheets=(output_sheet, _VALIDATION_SHEET),
                overwrite=False,
            )
            created_output = True
            self.adapter.write_range(
                destination,
                sheet=output_sheet,
                start_cell="A1",
                values=summary_values,
            )
            self.adapter.write_range(
                destination,
                sheet=_VALIDATION_SHEET,
                start_cell="A1",
                values=report_values,
            )

            self._verify_summary_output(destination, output_sheet, annual_rows)
            verification_row = len(report_values)  # header is row 1; status is last row
            self.adapter.write_range(
                destination,
                sheet=_VALIDATION_SHEET,
                start_cell=f"B{verification_row}",
                values=(("passed",),),
            )
            self._verify_summary_output(destination, output_sheet, annual_rows)
            report_table = self.adapter.read_table(
                destination,
                sheet=_VALIDATION_SHEET,
                header_row=1,
                max_data_rows=256,
                max_columns=8,
            )
            report_rows = {
                str(row[0]): row[1]
                for row in report_table.rows
                if len(row) >= 2 and row[0] is not None
            }
            if report_rows.get("output_verification") != "passed":
                raise RuntimeError("Validation report did not persist the passed output-verification state.")
        except Exception:
            if created_output and destination.exists():
                try:
                    destination.unlink()
                except OSError:
                    pass
            raise

        return AnnualXYAggregationResult(
            source_file_name=source.name,
            source_type=source_type,
            sheet=resolved_sheet,
            output_path=destination,
            output_sheet=output_sheet,
            period_column=period_name,
            x_column=x_name,
            y_column=y_name,
            operation=operation,
            rows=annual_rows,
            input_rows=input_row_count,
            accepted_rows=len(accepted),
            blank_rows_skipped=blank_rows_skipped,
            missing_rows_skipped=missing_rows_skipped,
            skipped_row_numbers=tuple(skipped_row_numbers),
            duplicate_period_count=duplicate_period_count,
            duplicate_period_policy=duplicate_period_policy,
            missing_value_policy=missing_value_policy,
            unit_validation_status=unit_status,
            caveats=tuple(caveats),
            output_verified=True,
            source_files=(source.name,),
        )

    def aggregate_folder(
        self,
        source_dir: str | Path,
        *,
        period_column: str | int,
        x_column: str | int,
        y_column: str | int,
        operation: AggregationOperation = "sum",
        sheet: str | None = None,
        header_row: int = 1,
        x_unit_column: str | int | None = None,
        y_unit_column: str | int | None = None,
        duplicate_period_policy: DuplicatePeriodPolicy = "reject",
        missing_value_policy: MissingValuePolicy = "reject",
        output_path: str | Path | None = None,
        output_sheet: str = "Annual Summary",
    ) -> AnnualXYAggregationResult:
        """Aggregate all approved top-level XLSX/CSV inputs in a folder.

        Every file must have the same normalized header schema. Sources are
        merged into a short-lived CSV inside the approved folder, then sent
        through the same validation, calculation and read-back verification
        path as single-file aggregation. The temporary source is always
        removed; the source files remain untouched.
        """
        if not isinstance(source_dir, (str, Path)) or not str(source_dir).strip():
            raise AnnualXYAggregationError("invalid_source_path", "A source folder path is required.")
        try:
            folder = Path(source_dir).expanduser().resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise AnnualXYAggregationError("source_not_found", "The source folder could not be resolved.") from exc
        if not folder.is_dir():
            raise AnnualXYAggregationError("source_not_directory", "The source path must be a directory.")
        if not any(folder.is_relative_to(root) for root in self.adapter.allowed_roots):
            raise PermissionError("The source folder is outside all configured Excel allowed roots.")

        sources = tuple(
            sorted(
                (
                    item for item in folder.iterdir()
                    if item.is_file()
                    and item.suffix.casefold() in {".xlsx", ".csv"}
                    and not item.name.startswith(".agent-annual-xy-")
                    and not re.search(
                        r"-annual-xy-summary(?:-\d+)?\.xlsx$",
                        item.name,
                        re.IGNORECASE,
                    )
                ),
                key=lambda item: item.name.casefold(),
            )
        )
        if not sources:
            raise AnnualXYAggregationError(
                "no_supported_input_files",
                "The folder contains no supported .xlsx or .csv input files.",
            )
        if len(sources) > 100:
            raise AnnualXYAggregationError(
                "too_many_source_files",
                "The folder exceeds the configured 100-file source budget.",
            )

        total_bytes = 0
        for path in sources:
            resolved = self._resolve_input_path(path)
            size = resolved.stat().st_size
            if size > self.MAX_FILE_BYTES:
                raise AnnualXYAggregationError(
                    "file_too_large",
                    f"An input file exceeds the configured {self.MAX_FILE_BYTES // (1024 * 1024)} MiB per-file budget.",
                )
            total_bytes += size
        if total_bytes > 128 * 1024 * 1024:
            raise AnnualXYAggregationError(
                "folder_too_large",
                "The source folder exceeds the configured 128 MiB aggregate input budget.",
            )

        self._positive_int(header_row, "header_row")
        output_sheet = self._validate_output_sheet(output_sheet)

        merged_headers: tuple[str, ...] | None = None
        merged_rows: list[tuple[object, ...]] = []
        source_row_map: dict[int, tuple[str, int]] = {}
        source_sheets: list[str | None] = []
        expected_schema: tuple[str, ...] | None = None

        # Temporary CSV uses one header row, so record 2 maps to the first
        # source data row regardless of each input file's own header offset.
        for path in sources:
            resolved = self._resolve_input_path(path)
            source_type = resolved.suffix.casefold()
            if source_type == ".xlsx":
                table, resolved_sheet = self._read_xlsx(resolved, sheet, header_row)
                source_sheets.append(resolved_sheet)
            else:
                table = self._read_csv(resolved, header_row)
                source_sheets.append(None)

            headers, rows = self._normalize_table_shape(table)
            header_names = tuple(
                str(value).strip() if value is not None else ""
                for value in headers
            )
            if not header_names:
                raise AnnualXYAggregationError(
                    "missing_header",
                    f"An input file ({resolved.name}) has no header row.",
                )
            self._validate_header_row(header_names, rows, table.row_numbers)
            schema = tuple(self._header_key(name) for name in header_names)
            if expected_schema is None:
                expected_schema = schema
                merged_headers = header_names
            elif schema != expected_schema:
                raise AnnualXYAggregationError(
                    "source_schema_mismatch",
                    "All source files must have the same normalized header names in the same order. "
                    f"Schema mismatch in input file: {resolved.name}.",
                )

            if len(merged_rows) + len(rows) > self.MAX_DATA_ROWS:
                raise AnnualXYAggregationError(
                    "too_many_rows",
                    "Combined source files exceed the configured 100,000-row budget.",
                )
            for row, original_row_number in zip(rows, table.row_numbers):
                merged_rows.append(tuple(row))
                temp_record_number = len(merged_rows) + 1
                source_row_map[temp_record_number] = (
                    resolved.name,
                    original_row_number,
                )

        if merged_headers is None or not merged_rows:
            raise AnnualXYAggregationError(
                "no_usable_rows",
                "The selected source files contain no data rows.",
            )

        if output_path is None:
            candidate = folder / f"{folder.name}-annual-xy-summary.xlsx"
            suffix = 2
            while candidate.exists():
                candidate = folder / f"{folder.name}-annual-xy-summary-{suffix}.xlsx"
                suffix += 1
            destination = candidate.resolve(strict=False)
        else:
            destination = Path(output_path).expanduser().resolve(strict=False)
        if destination.suffix.casefold() != ".xlsx":
            raise AnnualXYAggregationError(
                "invalid_output_type",
                "The output path must use the .xlsx extension.",
            )
        if not any(destination.is_relative_to(root) for root in self.adapter.allowed_roots):
            raise PermissionError("The output path is outside all configured Excel allowed roots.")
        if destination in {path.resolve(strict=True) for path in sources}:
            raise AnnualXYAggregationError(
                "source_overwrite_blocked",
                "The output path cannot be one of the source files.",
            )
        if destination.exists():
            raise FileExistsError(destination)

        temp_path: Path | None = None
        result: AnnualXYAggregationResult | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=folder,
                prefix=".agent-annual-xy-",
                suffix=".csv",
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(merged_headers)
                for row in merged_rows:
                    writer.writerow([
                        "" if value is None else self._csv_safe_value(value)
                        for value in row
                    ])

            if temp_path.stat().st_size > self.MAX_FILE_BYTES:
                raise AnnualXYAggregationError(
                    "combined_source_too_large",
                    "The normalized combined source exceeds the configured 32 MiB processing budget.",
                )

            try:
                result = self.aggregate(
                    temp_path,
                    period_column=period_column,
                    x_column=x_column,
                    y_column=y_column,
                    operation=operation,
                    sheet=None,
                    header_row=1,
                    x_unit_column=x_unit_column,
                    y_unit_column=y_unit_column,
                    duplicate_period_policy=duplicate_period_policy,
                    missing_value_policy=missing_value_policy,
                    output_path=destination,
                    output_sheet=output_sheet,
                )
            except AnnualXYAggregationError as exc:
                if not exc.row_numbers:
                    raise
                details = []
                original_row_numbers = []
                for temp_row in exc.row_numbers:
                    source_info = source_row_map.get(temp_row)
                    if source_info is None:
                        continue
                    file_name, original_row = source_info
                    details.append(f"{file_name}: row {original_row}")
                    original_row_numbers.append(original_row)
                if not details:
                    raise
                raise AnnualXYAggregationError(
                    exc.code,
                    f"{exc}. Source locations: " + "; ".join(dict.fromkeys(details)),
                    row_numbers=tuple(original_row_numbers),
                ) from exc

            report = self.adapter.read_table(
                result.output_path,
                sheet=_VALIDATION_SHEET,
                header_row=1,
                max_data_rows=256,
                max_columns=8,
            )
            report_values = [
                list(row) if len(row) == 2 else [*row, *([None] * (2 - len(row)))]
                for row in report.rows
            ]
            report_row_indices = {
                str(row[0]): position
                for position, row in enumerate(report_values)
                if row and row[0] is not None
            }
            file_names = tuple(path.name for path in sources)
            file_type_names = {path.suffix.casefold()[1:] for path in sources}
            source_type_summary = (
                next(iter(file_type_names))
                if len(file_type_names) == 1
                else "mixed"
            )
            sheet_names = {name for name in source_sheets if name is not None}
            source_sheet_summary = (
                next(iter(sheet_names))
                if len(sheet_names) == 1 and all(name is not None for name in source_sheets)
                else "multiple/CSV"
                if sheet_names
                else None
            )
            result_source_file_name = (
                file_names[0]
                if len(file_names) == 1
                else f"{len(file_names)} source files"
            )
            report_updates = {
                "source_file_name": self._excel_literal(result_source_file_name),
                "source_type": source_type_summary,
                "source_sheet": (
                    self._excel_literal(source_sheet_summary)
                    if source_sheet_summary
                    else None
                ),
                "source_files": "; ".join(
                    self._excel_literal(name)
                    for name in file_names
                ),
            }
            for key, value in report_updates.items():
                position = report_row_indices.get(key)
                if position is not None:
                    report_values[position][1] = value
            self.adapter.write_range(
                result.output_path,
                sheet=_VALIDATION_SHEET,
                start_cell="A1",
                values=tuple(tuple(row) for row in (
                    [list(report.headers), *report_values]
                )),
            )
            # Confirm the report still says the annual output passed and that
            # it now lists only original source files, never the temporary CSV.
            persisted_report = self.adapter.read_table(
                result.output_path,
                sheet=_VALIDATION_SHEET,
                header_row=1,
                max_data_rows=256,
                max_columns=8,
            )
            persisted = {
                str(row[0]): row[1]
                for row in persisted_report.rows
                if len(row) >= 2 and row[0] is not None
            }
            if (
                persisted.get("output_verification") != "passed"
                or persisted.get("source_files") != report_updates["source_files"]
            ):
                raise RuntimeError("The output validation report failed its source-list read-back check.")
            self._verify_summary_output(result.output_path, output_sheet, result.rows)

            return replace(
                result,
                source_file_name=result_source_file_name,
                source_type=source_type_summary,
                sheet=source_sheet_summary,
                source_files=file_names,
            )
        except Exception:
            if result is not None and result.output_path.exists():
                try:
                    result.output_path.unlink()
                except OSError:
                    pass
            raise
        finally:
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    @staticmethod
    def _csv_safe_value(value: object) -> str | int | float:
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if value is None:
            return ""
        if isinstance(value, (str, int, float, Decimal)):
            return value
        return str(value)

    def _resolve_input_path(self, path: str | Path) -> Path:
        if not isinstance(path, (str, Path)) or not str(path).strip():
            raise AnnualXYAggregationError("invalid_source_path", "A source file path is required.")
        try:
            resolved = Path(path).expanduser().resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise AnnualXYAggregationError("source_not_found", "The source file could not be resolved.") from exc
        if not resolved.is_file():
            raise AnnualXYAggregationError("source_not_file", "The source path must identify a file.")
        if not any(resolved.is_relative_to(root) for root in self.adapter.allowed_roots):
            raise PermissionError("The source path is outside all configured Excel allowed roots.")
        if resolved.suffix.casefold() not in {".xlsx", ".csv"}:
            raise AnnualXYAggregationError("unsupported_file_type", "Only .xlsx and .csv inputs are supported.")
        return resolved

    def _read_xlsx(
        self,
        source: Path,
        sheet: str | None,
        header_row: int,
    ) -> tuple[ExcelTable, str]:
        if sheet is None:
            summary = self.adapter.inspect(source)
            if len(summary.sheet_names) != 1:
                raise AnnualXYAggregationError(
                    "ambiguous_sheet",
                    "The workbook contains multiple sheets; supply the sheet name explicitly.",
                )
            sheet = summary.sheet_names[0]
        try:
            table = self.adapter.read_table(
                source,
                sheet=sheet,
                header_row=header_row,
                max_data_rows=self.MAX_DATA_ROWS,
                max_columns=self.MAX_COLUMNS,
            )
        except (ValueError, KeyError) as exc:
            raise AnnualXYAggregationError("invalid_xlsx_table", str(exc)) from exc
        return table, table.sheet

    def _read_csv(self, source: Path, header_row: int) -> ExcelTable:
        try:
            with source.open("r", encoding="utf-8-sig", newline="") as handle:
                sample = handle.read(self.MAX_CSV_SAMPLE_BYTES)
                handle.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                except csv.Error:
                    dialect = csv.excel
                reader = csv.reader(handle, dialect)
                headers: tuple[object, ...] | None = None
                rows: list[tuple[object, ...]] = []
                row_numbers: list[int] = []
                record_number = 0
                for values in reader:
                    record_number += 1
                    if record_number < header_row:
                        continue
                    if record_number == header_row:
                        headers = tuple(value.strip() for value in values)
                        if len(headers) > self.MAX_COLUMNS:
                            raise AnnualXYAggregationError("too_many_columns", "The CSV exceeds the configured column budget.")
                        continue
                    if not values:
                        values = []
                    if len(values) > self.MAX_COLUMNS:
                        raise AnnualXYAggregationError("too_many_columns", "The CSV exceeds the configured column budget.")
                    if len(rows) >= self.MAX_DATA_ROWS:
                        raise AnnualXYAggregationError("too_many_rows", "The CSV exceeds the configured data-row budget.")
                    rows.append(tuple(value if value.strip() else None for value in values))
                    row_numbers.append(record_number)
                if headers is None:
                    raise AnnualXYAggregationError("missing_header", "The requested CSV header row does not exist.")
        except UnicodeDecodeError as exc:
            raise AnnualXYAggregationError("invalid_encoding", "The CSV must be UTF-8 encoded.") from exc
        except csv.Error as exc:
            raise AnnualXYAggregationError("invalid_csv", "The CSV could not be parsed.") from exc

        return ExcelTable(
            sheet="CSV",
            header_row=header_row,
            headers=headers,
            rows=tuple(rows),
            row_numbers=tuple(row_numbers),
        )

    @staticmethod
    def _normalize_table_shape(
        table: ExcelTable,
    ) -> tuple[tuple[object, ...], tuple[tuple[object, ...], ...]]:
        headers = list(table.headers)
        rows = [tuple(row) for row in table.rows]
        max_width = max([len(headers), *(len(row) for row in rows)], default=0)
        if len(headers) < max_width:
            headers.extend([None] * (max_width - len(headers)))
        normalized_rows = [
            row + (None,) * (max_width - len(row))
            for row in rows
        ]
        # Drop trailing unnamed columns only when they carry no data.
        while headers and (headers[-1] is None or not str(headers[-1]).strip()):
            last_index = len(headers) - 1
            if any(last_index < len(row) and not ExcelAnnualXYAggregationService._is_blank(row[last_index]) for row in normalized_rows):
                raise AnnualXYAggregationError(
                    "data_without_header",
                    "The source contains data in a column with no header.",
                )
            headers.pop()
            normalized_rows = [row[:-1] for row in normalized_rows]
        return tuple(headers), tuple(normalized_rows)

    @staticmethod
    def _validate_header_row(
        headers: tuple[str, ...],
        rows: tuple[tuple[object, ...], ...],
        row_numbers: tuple[int, ...],
    ) -> None:
        normalized = [
            ExcelAnnualXYAggregationService._header_key(header)
            for header in headers
            if header
        ]
        if not normalized:
            raise AnnualXYAggregationError("missing_header", "The source has no non-empty column headers.")
        duplicates = {name for name, count in Counter(normalized).items() if count > 1}
        if duplicates:
            raise AnnualXYAggregationError("duplicate_headers", "The source contains duplicate column headers.")
        for index, header in enumerate(headers):
            if header:
                continue
            if any(index < len(row) and not ExcelAnnualXYAggregationService._is_blank(row[index]) for row in rows):
                raise AnnualXYAggregationError("data_without_header", "The source contains data in an unnamed column.")

    @classmethod
    def _resolve_column(
        cls,
        selector: str | int,
        headers: tuple[str, ...],
        role: str,
    ) -> int:
        if isinstance(selector, int) and not isinstance(selector, bool):
            if selector < 1 or selector > len(headers):
                raise AnnualXYAggregationError("column_out_of_range", f"The selected {role} column number is out of range.")
            index = selector - 1
        elif isinstance(selector, str) and selector.strip():
            target = cls._header_key(selector)
            matches = [
                index for index, header in enumerate(headers)
                if header and cls._header_key(header) == target
            ]
            if len(matches) != 1:
                code = "ambiguous_column" if len(matches) > 1 else "unknown_column"
                raise AnnualXYAggregationError(code, f"The selected {role} header is not uniquely present in the source.")
            index = matches[0]
        else:
            raise AnnualXYAggregationError("invalid_column_selector", f"The selected {role} column must be a non-empty name or 1-based integer.")
        if not headers[index]:
            raise AnnualXYAggregationError("missing_selected_header", f"The selected {role} column has an empty header.")
        return index

    @staticmethod
    def _parse_period(value: object, row_number: int) -> tuple[int, str]:
        candidate = value
        if isinstance(candidate, datetime):
            parsed_date = candidate.date()
            if not _YEAR_MIN <= parsed_date.year <= _YEAR_MAX:
                raise AnnualXYAggregationError(
                    "invalid_period",
                    "The year is outside the supported 1900–2200 range.",
                    row_numbers=(row_number,),
                )
            return parsed_date.year, f"date:{parsed_date.isoformat()}"
        if isinstance(candidate, date):
            if not _YEAR_MIN <= candidate.year <= _YEAR_MAX:
                raise AnnualXYAggregationError(
                    "invalid_period",
                    "The year is outside the supported 1900–2200 range.",
                    row_numbers=(row_number,),
                )
            return candidate.year, f"date:{candidate.isoformat()}"
        if isinstance(candidate, bool):
            raise AnnualXYAggregationError("invalid_period", "The period value is not a supported date/year.", row_numbers=(row_number,))
        if isinstance(candidate, (int, float, Decimal)):
            try:
                number = Decimal(str(candidate))
            except InvalidOperation as exc:
                raise AnnualXYAggregationError("invalid_period", "The period value is not a supported date/year.", row_numbers=(row_number,)) from exc
            if number == number.to_integral_value() and _YEAR_MIN <= int(number) <= _YEAR_MAX:
                year = int(number)
                return year, f"year:{year}"
            raise AnnualXYAggregationError("ambiguous_numeric_period", "Numeric periods must be a whole year; use an Excel date or an ISO date/month string for other periods.", row_numbers=(row_number,))

        text = str(candidate).strip()

        # ExcelWorkbookAdapter intentionally serializes date-like cells to
        # ISO strings. Preserve year provenance for both date-only and
        # datetime ISO forms rather than treating them as arbitrary labels.
        try:
            parsed_datetime = datetime.fromisoformat(
                text[:-1] + "+00:00" if text.endswith("Z") else text
            )
        except ValueError:
            parsed_datetime = None
        if parsed_datetime is not None:
            parsed_date = parsed_datetime.date()
            if not _YEAR_MIN <= parsed_date.year <= _YEAR_MAX:
                raise AnnualXYAggregationError(
                    "invalid_period",
                    "The year is outside the supported 1900–2200 range.",
                    row_numbers=(row_number,),
                )
            return parsed_date.year, f"date:{parsed_date.isoformat()}"

        if _NUMERIC_TEXT.fullmatch(text):
            raise AnnualXYAggregationError(
                "ambiguous_numeric_period",
                "Numeric periods must be a whole year; use an Excel date or an ISO date/month string for other periods.",
                row_numbers=(row_number,),
            )

        match = _YEAR_TEXT.fullmatch(text)
        if match:
            year = int(match.group(1))
            if _YEAR_MIN <= year <= _YEAR_MAX:
                return year, f"year:{year}"
            raise AnnualXYAggregationError("invalid_period", "The year is outside the supported 1900–2200 range.", row_numbers=(row_number,))

        match = _YEAR_MONTH_TEXT.fullmatch(text)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            if _YEAR_MIN <= year <= _YEAR_MAX and 1 <= month <= 12:
                return year, f"month:{year:04d}-{month:02d}"
            raise AnnualXYAggregationError("invalid_period", "The year/month value is outside the supported range.", row_numbers=(row_number,))

        match = _MONTH_YEAR_TEXT.fullmatch(text)
        if match:
            month, year = int(match.group(1)), int(match.group(2))
            if _YEAR_MIN <= year <= _YEAR_MAX and 1 <= month <= 12:
                return year, f"month:{year:04d}-{month:02d}"
            raise AnnualXYAggregationError("invalid_period", "The month/year value is outside the supported range.", row_numbers=(row_number,))

        match = _YEAR_MONTH_DAY_TEXT.fullmatch(text)
        if match:
            year, month, day_value = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                parsed_date = date(year, month, day_value)
            except ValueError as exc:
                raise AnnualXYAggregationError("invalid_period", "The date value is invalid.", row_numbers=(row_number,)) from exc
            if not _YEAR_MIN <= parsed_date.year <= _YEAR_MAX:
                raise AnnualXYAggregationError("invalid_period", "The year is outside the supported 1900–2200 range.", row_numbers=(row_number,))
            return parsed_date.year, f"date:{parsed_date.isoformat()}"

        # European day-first formats are accepted only when their interpretation
        # is explicit by the date format. Ambiguous 01/02/2025 is rejected above
        # only if neither exact month/year nor ISO format matched.
        for fmt in ("%d.%m.%Y", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(text, fmt).date()
            except ValueError:
                continue
            if _YEAR_MIN <= parsed.year <= _YEAR_MAX:
                return parsed.year, f"date:{parsed.isoformat()}"

        raise AnnualXYAggregationError(
            "ambiguous_or_invalid_period",
            "Period must be a year, year-month, month/year, ISO date, or explicit day-first date (DD.MM.YYYY or DD/MM/YYYY).",
            row_numbers=(row_number,),
        )

    @staticmethod
    def _parse_number(value: object, field: str, row_number: int) -> Decimal:
        if isinstance(value, bool):
            raise AnnualXYAggregationError("invalid_numeric_value", f"{field} must be numeric, not boolean.", row_numbers=(row_number,))
        if isinstance(value, Decimal):
            number = value
        elif isinstance(value, (int, float)):
            try:
                number = Decimal(str(value))
            except InvalidOperation as exc:
                raise AnnualXYAggregationError("invalid_numeric_value", f"{field} must be a finite number.", row_numbers=(row_number,)) from exc
        elif isinstance(value, str):
            text = value.strip()
            if not _NUMERIC_TEXT.fullmatch(text):
                raise AnnualXYAggregationError("invalid_numeric_value", f"{field} must be a simple decimal number; thousands separators and formulas are not inferred.", row_numbers=(row_number,))
            try:
                number = Decimal(text.replace(",", "."))
            except InvalidOperation as exc:
                raise AnnualXYAggregationError("invalid_numeric_value", f"{field} must be a finite number.", row_numbers=(row_number,)) from exc
        else:
            raise AnnualXYAggregationError("invalid_numeric_value", f"{field} must be numeric.", row_numbers=(row_number,))
        if not number.is_finite():
            raise AnnualXYAggregationError("invalid_numeric_value", f"{field} must be finite.", row_numbers=(row_number,))
        return number

    @classmethod
    def _validate_units(
        cls,
        rows: list[_InputRow],
        has_x_unit: bool,
        has_y_unit: bool,
    ) -> tuple[str | None, str | None]:
        x_units = {cls._header_key(item.x_unit) for item in rows if item.x_unit}
        y_units = {cls._header_key(item.y_unit) for item in rows if item.y_unit}
        if has_x_unit and len(x_units) != 1:
            raise AnnualXYAggregationError(
                "incompatible_x_units",
                "The X unit column contains missing or incompatible units; conversion rules are not inferred.",
            )
        if has_y_unit and len(y_units) != 1:
            raise AnnualXYAggregationError(
                "incompatible_y_units",
                "The Y unit column contains missing or incompatible units; conversion rules are not inferred.",
            )
        return (
            next((item.x_unit for item in rows if item.x_unit), None),
            next((item.y_unit for item in rows if item.y_unit), None),
        )

    @staticmethod
    def _normalize_unit(value: object, field: str, row_number: int) -> str:
        if not isinstance(value, (str, int, float, Decimal)) or isinstance(value, bool):
            raise AnnualXYAggregationError("invalid_unit", f"{field} unit must be a non-empty string/value.", row_numbers=(row_number,))
        normalized = str(value).strip()
        if not normalized or len(normalized) > 64:
            raise AnnualXYAggregationError("invalid_unit", f"{field} unit must contain 1–64 characters.", row_numbers=(row_number,))
        return normalized

    @staticmethod
    def _aggregate_decimal(values: list[Decimal], operation: AggregationOperation) -> Decimal:
        if not values:
            raise AnnualXYAggregationError("no_usable_rows", "An annual group has no numeric values.")
        if operation == "sum":
            return sum(values, Decimal(0))
        if operation == "mean":
            return sum(values, Decimal(0)) / Decimal(len(values))
        if operation == "min":
            return min(values)
        if operation == "max":
            return max(values)
        raise AnnualXYAggregationError("invalid_operation", "Unsupported aggregation operation.")

    @staticmethod
    def _excel_number(value: Decimal) -> int | float:
        if not value.is_finite():
            raise AnnualXYAggregationError("invalid_aggregate", "The aggregate is not finite.")
        if value == value.to_integral_value():
            return int(value)
        result = float(value)
        if result == float("inf") or result == float("-inf"):
            raise AnnualXYAggregationError("aggregate_out_of_range", "The aggregate exceeds Excel's supported numeric range.")
        return result

    def _verify_summary_output(
        self,
        path: Path,
        output_sheet: str,
        expected_rows: tuple[AnnualXYRow, ...],
    ) -> None:
        summary = self.adapter.read_table(
            path,
            sheet=output_sheet,
            header_row=1,
            max_data_rows=self.MAX_DATA_ROWS,
            max_columns=16,
        )
        if len(summary.rows) != len(expected_rows):
            raise RuntimeError("The saved annual summary has an unexpected row count.")
        for actual, expected in zip(summary.rows, expected_rows):
            if len(actual) < 3:
                raise RuntimeError("The saved annual summary is missing expected columns.")
            if actual[0] != expected.year:
                raise RuntimeError("The saved annual summary year does not match the computed result.")
            if not self._excel_numeric_match(actual[1], expected.x_value):
                raise RuntimeError("The saved annual X value failed read-back verification.")
            if not self._excel_numeric_match(actual[2], expected.y_value):
                raise RuntimeError("The saved annual Y value failed read-back verification.")
            if len(actual) < 7 or actual[5] != expected.period_count or actual[6] != expected.input_row_count:
                raise RuntimeError("The saved annual summary counts failed read-back verification.")

    @staticmethod
    def _excel_numeric_match(actual: object, expected: Decimal) -> bool:
        if isinstance(actual, bool) or not isinstance(actual, (int, float, Decimal)):
            return False
        try:
            return abs(Decimal(str(actual)) - expected) <= max(Decimal("0.00000001"), abs(expected) * Decimal("0.000000000001"))
        except InvalidOperation:
            return False

    def _resolve_output_path(
        self,
        source: Path,
        output_path: str | Path | None,
    ) -> Path:
        if output_path is None:
            base = source.with_name(f"{source.stem}-annual-xy-summary.xlsx")
            candidate = base
            suffix = 2
            while candidate.exists():
                candidate = source.with_name(f"{source.stem}-annual-xy-summary-{suffix}.xlsx")
                suffix += 1
        else:
            candidate = Path(output_path).expanduser().resolve(strict=False)
        if candidate == source:
            raise AnnualXYAggregationError(
                "source_overwrite_blocked",
                "The output path cannot be the source file.",
            )
        if candidate.suffix.casefold() != ".xlsx":
            raise AnnualXYAggregationError("invalid_output_type", "The output path must use the .xlsx extension.")
        if not any(candidate.is_relative_to(root) for root in self.adapter.allowed_roots):
            raise PermissionError("The output path is outside all configured Excel allowed roots.")
        if candidate.exists():
            raise FileExistsError(candidate)
        return candidate

    @staticmethod
    def _operation(value: str) -> AggregationOperation:
        if not isinstance(value, str) or value.strip().casefold() not in _ALLOWED_OPERATIONS:
            raise AnnualXYAggregationError("invalid_operation", "Operation must be one of: sum, mean, min, max.")
        return value.strip().casefold()  # type: ignore[return-value]

    @staticmethod
    def _duplicate_policy(value: str) -> DuplicatePeriodPolicy:
        if not isinstance(value, str) or value.strip().casefold() not in _ALLOWED_DUPLICATE_POLICIES:
            raise AnnualXYAggregationError("invalid_duplicate_policy", "Duplicate-period policy must be reject or include.")
        return value.strip().casefold()  # type: ignore[return-value]

    @staticmethod
    def _missing_policy(value: str) -> MissingValuePolicy:
        if not isinstance(value, str) or value.strip().casefold() not in _ALLOWED_MISSING_POLICIES:
            raise AnnualXYAggregationError("invalid_missing_policy", "Missing-value policy must be reject or skip_rows.")
        return value.strip().casefold()  # type: ignore[return-value]

    @staticmethod
    def _positive_int(value: object, name: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise AnnualXYAggregationError("invalid_parameter", f"{name} must be a positive integer.")

    @staticmethod
    def _validate_output_sheet(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AnnualXYAggregationError("invalid_output_sheet", "Output sheet name must not be empty.")
        normalized = value.strip()
        if len(normalized) > 31 or any(character in normalized for character in ":\\/?*[]"):
            raise AnnualXYAggregationError("invalid_output_sheet", "Output sheet name violates Excel naming rules.")
        if normalized.casefold() == _VALIDATION_SHEET.casefold():
            raise AnnualXYAggregationError("invalid_output_sheet", "Output sheet name conflicts with the Validation Report sheet.")
        return normalized

    @staticmethod
    def _is_blank(value: object) -> bool:
        return value is None or (isinstance(value, str) and not value.strip())

    @staticmethod
    def _header_key(value: object) -> str:
        text = "" if value is None else str(value).strip()
        decomposed = unicodedata.normalize("NFKC", text).casefold()
        return " ".join(decomposed.split())

    @staticmethod
    def _excel_literal(value: str) -> str:
        """Prevent imported text from becoming a formula in the output workbook."""
        normalized = value.strip()
        if normalized.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + normalized
        return normalized
