import pytest

from tools.test_windows_desktop_task import TABLE, verify_table


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "utf-16"])
def test_desktop_task_reads_back_saved_table_with_windows_line_endings(tmp_path, encoding):
    path = tmp_path / "table.txt"
    path.write_bytes(TABLE.replace("\n", "\r\n").encode(encoding))
    assert verify_table(path) == {"data_rows": 2, "columns": 4}


def test_desktop_task_does_not_accept_an_empty_or_incomplete_file(tmp_path):
    path = tmp_path / "table.txt"
    path.write_text(TABLE.splitlines()[0], encoding="utf-8")
    with pytest.raises(ValueError, match="różni się"):
        verify_table(path)
