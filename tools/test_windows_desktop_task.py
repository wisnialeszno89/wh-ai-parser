"""Create a disposable Desktop folder via Explorer and save a table via native Notepad."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.visual.windows_driver import literal_keys

TABLE = (
    "Pozycja\tSzerokosc_mm\tWysokosc_mm\tSztuki\n"
    "Okno DKR\t1000\t1000\t1\n"
    "Okno DKL/DKR\t1500\t1400\t2\n"
)


def verify_table(path):
    data = path.read_bytes()
    encoding = "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
    actual = data.decode(encoding).replace("\r\n", "\n").rstrip("\n")
    if actual != TABLE.rstrip("\n"):
        raise ValueError("Zapisana tabela różni się od zadania.")
    return {"data_rows": 2, "columns": 4}


def wait_for(read, description, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = read()
        if value:
            return value
        time.sleep(.25)
    raise RuntimeError("Upłynął czas oczekiwania: " + description)


def execute_task(trace_path, report):
    import ctypes

    from pywinauto import Application, Desktop
    from pywinauto.keyboard import send_keys
    import win32com.client
    import win32gui
    import win32process

    desktop_buffer = ctypes.create_unicode_buffer(260)
    result = ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, desktop_buffer)
    if result != 0:
        raise RuntimeError("Nie udało się ustalić rzeczywistego folderu Pulpit.")
    desktop_path = Path(desktop_buffer.value)
    if not desktop_path.is_dir():
        raise RuntimeError("Nie znaleziono folderu Pulpit.")
    folder = desktop_path / ("NaviMind-Test-" + uuid4().hex[:10])
    target = folder / "tabela-okien.txt"
    report.update(folder=str(folder), file=str(target), stage="explorer")
    shell = win32com.client.Dispatch("Shell.Application")

    def explorer_window():
        matches = []
        for window in shell.Windows():
            try:
                if os.path.normcase(str(window.Document.Folder.Self.Path)) == os.path.normcase(str(desktop_path)):
                    matches.append(window)
            except Exception:
                continue
        if len(matches) > 1:
            raise RuntimeError("Otwartych jest kilka okien Eksploratora z folderem Pulpit. Zostaw jedno i ponów test.")
        return matches[0] if matches else None

    if explorer_window() is None:
        subprocess.Popen(["explorer.exe", str(desktop_path)])
    explorer = wait_for(explorer_window, "Eksplorator z folderem Pulpit")
    explorer_hwnd = int(explorer.HWND)
    explorer_control = Application(backend="win32").connect(handle=explorer_hwnd).window(handle=explorer_hwnd)

    def focus(window):
        window.set_focus()
        if win32gui.GetForegroundWindow() != window.handle:
            raise RuntimeError("Okno zadania nie uzyskało fokusu.")

    def keys(window, sequence):
        focus(window)
        send_keys(sequence, pause=.04)

    def evidence(window, name):
        focus(window)
        window.capture_as_image().save(trace_path / (name + ".png"))

    evidence(explorer_control, "01-desktop-before")
    if str(explorer.Document.Folder.Self.Path).casefold() != str(desktop_path).casefold():
        raise RuntimeError("Eksplorator zmienił folder przed utworzeniem katalogu.")
    if folder.exists():
        raise RuntimeError("Folder zadania już istnieje.")
    keys(explorer_control, "^+n")
    time.sleep(.7)
    keys(explorer_control, literal_keys(folder.name) + "{ENTER}")
    wait_for(folder.is_dir, "folder utworzony w Eksploratorze")
    evidence(explorer_control, "02-folder-created")
    print("DESKTOP_FOLDER_RESULT=verified PATH=" + str(folder), flush=True)

    report["stage"] = "notepad"
    notepad_exe = Path(os.environ["SystemRoot"]) / "System32" / "notepad.exe"
    process = subprocess.Popen([str(notepad_exe)])
    app = Application(backend="win32").connect(process=process.pid, timeout=15)

    def notepad_window():
        windows = [window for window in app.windows() if window.is_visible() and window.class_name() == "Notepad"]
        if len(windows) > 1:
            raise RuntimeError("Proces Notatnika ma kilka okien. Przerwano wybór.")
        return windows[0] if windows else None

    notepad = wait_for(notepad_window, "nowe okno klasycznego Notatnika")
    if win32process.GetWindowThreadProcessId(notepad.handle)[1] != process.pid:
        raise RuntimeError("Okno nie należy do uruchomionego Notatnika.")
    edits = notepad.descendants(class_name="Edit")
    if len(edits) != 1:
        raise RuntimeError("Nie znaleziono jednoznacznego pola tekstu Notatnika.")
    focus(notepad)
    edits[0].set_edit_text(TABLE.replace("\n", "\r\n"))
    if edits[0].window_text().replace("\r\n", "\n").rstrip("\n") != TABLE.rstrip("\n"):
        raise RuntimeError("Odczyt pola Notatnika nie potwierdził tabeli.")
    evidence(notepad, "03-table-in-notepad")
    keys(notepad, "^s")

    def save_dialog():
        windows = Desktop(backend="win32").windows(process=process.pid, class_name="#32770", visible_only=True)
        if len(windows) > 1:
            raise RuntimeError("Znaleziono kilka okien dialogowych zapisu.")
        return windows[0] if windows else None

    dialog = wait_for(save_dialog, "okno zapisu Notatnika")
    uia_dialog = Application(backend="uia").connect(handle=dialog.handle).window(handle=dialog.handle)
    filename_fields = [field for field in uia_dialog.descendants(control_type="Edit")
                       if field.element_info.automation_id == "1001"]
    if len(filename_fields) != 1:
        raise RuntimeError("Nie znaleziono jednoznacznego pola nazwy pliku w oknie zapisu.")
    focus(dialog)
    filename_fields[0].set_edit_text(str(target))
    evidence(dialog, "04-save-dialog")
    keys(dialog, "{ENTER}")
    def saved_table():
        try:
            return verify_table(target)
        except (OSError, ValueError, UnicodeError):
            return None

    report["verification"] = wait_for(saved_table, "plik z poprawną zawartością zapisany przez Notatnik")
    wait_for(lambda: save_dialog() is None, "zamknięcie okna zapisu")
    evidence(notepad, "05-saved-notepad")
    report.update(status="verified", stage="finished")
    print("DESKTOP_TABLE_RESULT=verified ROWS=2 COLUMNS=4", flush=True)
    print("DESKTOP_TASK_FILE=" + str(target), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args(argv)
    if os.name != "nt":
        print("DESKTOP_TASK_RESULT=review Windows required")
        return 2
    if not args.execute_live:
        print("PLAN=Explorer creates a new Desktop folder; Notepad types and saves tabela-okien.txt; file readback verifies contents.")
        print("Run with --execute-live to execute.")
        return 0
    trace_path = Path(tempfile.gettempdir()) / ("navimind-desktop-task-" + uuid4().hex[:10])
    trace_path.mkdir()
    report = {"status": "review", "mode": "native_windows_ui", "stage": "initializing"}
    print("DESKTOP_TASK_TRACE_DIR=" + str(trace_path), flush=True)
    try:
        execute_task(trace_path, report)
        print("DESKTOP_TASK_RESULT=verified", flush=True)
        return 0
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        print(f"DESKTOP_TASK_RESULT=review STAGE={report['stage']}\n{report['error']}", flush=True)
        return 6
    finally:
        (trace_path / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
