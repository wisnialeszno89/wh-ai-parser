from app.agent.adapters.word_document_adapter import (
    WordDocumentAdapter,
)


def test_word_document_adapter_creates_and_reads_docx(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = WordDocumentAdapter(
        allowed_roots=(root,)
    )

    path = adapter.create(
        root / "oferta.docx",
        title="Oferta dla klienta",
        paragraphs=(
            "Okno PVC 1230 x 1450 mm",
            "Kolor: antracyt",
        ),
    )

    assert path.exists()
    text = adapter.read_text(path)

    assert "Oferta dla klienta" in text
    assert "Okno PVC 1230 x 1450 mm" in text
    assert "Kolor: antracyt" in text


def test_word_document_adapter_appends_and_inspects_document(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = WordDocumentAdapter(
        allowed_roots=(root,)
    )

    path = adapter.create(
        root / "oferta.docx",
        paragraphs=("Pierwszy akapit",),
    )

    summary = adapter.append_paragraph(
        path,
        "Drugi akapit",
    )

    assert summary.paragraph_count == 2
    assert summary.table_count == 0
    assert "Drugi akapit" in adapter.read_text(path)


def test_word_document_adapter_rejects_non_docx_and_outside_root(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = WordDocumentAdapter(
        allowed_roots=(root,)
    )

    try:
        adapter.create(
            root / "oferta.txt",
            paragraphs=("test",),
        )
    except ValueError as exc:
        assert ".docx" in str(exc)
    else:
        raise AssertionError("Non-docx path was accepted.")

    outside = tmp_path / "outside.docx"

    try:
        adapter.exists(outside)
    except PermissionError:
        pass
    else:
        raise AssertionError("Outside path was accepted.")


def test_word_document_adapter_requires_explicit_overwrite(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = WordDocumentAdapter(
        allowed_roots=(root,)
    )

    path = root / "oferta.docx"
    adapter.create(
        path,
        paragraphs=("first",),
    )

    try:
        adapter.create(
            path,
            paragraphs=("second",),
        )
    except FileExistsError:
        pass
    else:
        raise AssertionError("Existing document was overwritten.")

    adapter.create(
        path,
        paragraphs=("second",),
        overwrite=True,
    )

    assert "second" in adapter.read_text(path)
    assert "first" not in adapter.read_text(path)
