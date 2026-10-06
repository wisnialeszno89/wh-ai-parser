from app.agent.adapters.filesystem_adapter import FileSystemAdapter


def test_filesystem_adapter_lists_and_reads_only_allowed_root(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    source = root / "offer.txt"
    source.write_text("Oferta testowa", encoding="utf-8")

    adapter = FileSystemAdapter(
        allowed_roots=(root,)
    )

    entries = adapter.list(root)
    assert entries[0].name == "offer.txt"
    assert entries[0].is_file is True
    assert adapter.exists(source)
    assert adapter.read_text(source) == "Oferta testowa"


def test_filesystem_adapter_rejects_path_outside_allowed_roots(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    adapter = FileSystemAdapter(
        allowed_roots=(root,)
    )

    try:
        adapter.read_text(outside)
    except PermissionError as exc:
        assert "outside all allowed filesystem roots" in str(exc)
    else:
        raise AssertionError("Outside path was read.")


def test_filesystem_adapter_writes_atomically_and_requires_explicit_overwrite(
    tmp_path,
):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = FileSystemAdapter(
        allowed_roots=(root,)
    )

    target = root / "note.txt"
    adapter.write_text(target, "first")

    assert target.read_text(encoding="utf-8") == "first"

    try:
        adapter.write_text(target, "second")
    except FileExistsError:
        pass
    else:
        raise AssertionError("Existing file was overwritten.")

    adapter.write_text(
        target,
        "second",
        overwrite=True,
    )
    assert target.read_text(encoding="utf-8") == "second"


def test_filesystem_adapter_copy_and_move_stay_inside_allowed_root(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    source = root / "source.txt"
    source.write_text("hello", encoding="utf-8")

    adapter = FileSystemAdapter(
        allowed_roots=(root,)
    )

    copied = adapter.copy(
        source,
        root / "copy.txt",
    )
    assert copied.read_text(encoding="utf-8") == "hello"

    moved = adapter.move(
        copied,
        root / "moved.txt",
    )
    assert moved.exists()
    assert not copied.exists()
