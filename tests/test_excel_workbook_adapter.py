from app.agent.adapters.excel_workbook_adapter import (
    ExcelWorkbookAdapter,
)


def test_excel_adapter_creates_inspects_and_reads_workbook(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = ExcelWorkbookAdapter(
        allowed_roots=(root,)
    )

    path = root / "cennik.xlsx"
    summary = adapter.create(
        path,
        sheets=("Cennik", "Dane"),
    )

    assert summary.sheet_names == ("Cennik", "Dane")

    written = adapter.write_range(
        path,
        sheet="Cennik",
        start_cell="A1",
        values=(
            ("Produkt", "Cena"),
            ("Okno PVC", 1250),
        ),
    )

    assert written.values == (
        ("Produkt", "Cena"),
        ("Okno PVC", 1250),
    )

    inspected = adapter.inspect(path)
    assert inspected.sheet_names == ("Cennik", "Dane")
    assert inspected.max_rows == 2
    assert inspected.max_columns == 2


def test_excel_adapter_appends_rows_and_creates_sheet(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = ExcelWorkbookAdapter(
        allowed_roots=(root,)
    )

    path = adapter.create(
        root / "oferta.xlsx",
        sheets=("Oferta",),
    )

    adapter.write_range(
        path,
        sheet="Oferta",
        start_cell="A1",
        values=(("Klient", "Kowalski"),),
    )

    appended = adapter.append_rows(
        path,
        sheet="Oferta",
        rows=(
            ("Ilość", 6),
            ("Kolor", "antracyt"),
        ),
    )

    assert appended.values == (
        ("Ilość", 6),
        ("Kolor", "antracyt"),
    )

    summary = adapter.create_sheet(
        path,
        sheet="Notatki",
    )
    assert "Notatki" in summary.sheet_names


def test_excel_adapter_rejects_outside_root_and_non_xlsx(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = ExcelWorkbookAdapter(
        allowed_roots=(root,)
    )

    try:
        adapter.create(
            root / "bad.txt",
        )
    except ValueError as exc:
        assert ".xlsx" in str(exc)
    else:
        raise AssertionError("Non-xlsx path was accepted.")

    try:
        adapter.exists(tmp_path / "outside.xlsx")
    except PermissionError:
        pass
    else:
        raise AssertionError("Outside path was accepted.")


def test_excel_adapter_requires_explicit_overwrite(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = ExcelWorkbookAdapter(
        allowed_roots=(root,)
    )

    path = root / "test.xlsx"
    adapter.create(path)

    try:
        adapter.create(path)
    except FileExistsError:
        pass
    else:
        raise AssertionError("Existing workbook was overwritten.")
