"""Paired loopback executor for NaviMind's window-table pilot (Windows 10 Notepad)."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
import time

PORT = 43127
ORIGINS = {"https://www.navimind.app", "https://navimind.app"}
HEADER = "Pozycja\tSzerokosc_mm\tWysokosc_mm\tSztuki\n"


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"Wymagana liczba całkowita {low}–{high}.")
    return value


def folder_name(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 60:
        raise ValueError("Podaj nazwę folderu (1–60 znaków).")
    if any(ord(c) < 32 or c in '<>:"/\\|?*' for c in value) or value != value.strip() or value.endswith('.'):
        raise ValueError("Nazwa folderu zawiera niedozwolone znaki.")
    if value in {'.', '..'} or re.match(r'^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)', value, re.I):
        raise ValueError("Niedozwolona nazwa folderu.")
    return value


CAPABILITIES = ['create_window_table', 'update_window_width', 'append_window_rows', 'edit_window_rows', 'open_window_table', 'copy_window_table']


def file_name(value):
    name = folder_name(value)
    if not name.lower().endswith('.txt') or len(name) <= 4:
        raise ValueError('Nazwa pliku musi kończyć się na .txt.')
    return name


def validate_fields(fields):
    if not isinstance(fields, dict) or not fields or not set(fields) <= {'label', 'width_mm', 'height_mm', 'quantity'}:
        raise ValueError('Nieprawidłowe pola korekty.')
    for key, value in fields.items():
        if key == 'label':
            if not isinstance(value, str) or not value.strip() or len(value) > 120 or any(ord(c) < 32 for c in value):
                raise ValueError('Nieprawidłowy opis pozycji.')
        elif key == 'quantity':
            integer(value, 1, 999)
        else:
            integer(value, 100, 10000)
    return fields


def validate_rows(rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 50:
        raise ValueError('Tabela musi zawierać 1–50 pozycji.')
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'label', 'width_mm', 'height_mm', 'quantity'}:
            raise ValueError('Nieprawidłowa pozycja.')
        validate_fields(row)
    return rows


def validate_task(task):
    if not isinstance(task, dict):
        raise ValueError('Nieprawidłowe zadanie.')
    kind = task.get('kind')
    if kind == 'create_window_table':
        if set(task) not in ({'kind', 'folder', 'rows'}, {'kind', 'folder', 'file_name', 'rows'}):
            raise ValueError('Nieprawidłowe pola zadania.')
        folder_name(task['folder'])
        file_name(task.get('file_name', 'tabela-okien.txt'))
        validate_rows(task['rows'])
    elif kind == 'append_window_rows':
        if set(task) != {'kind', 'rows'}:
            raise ValueError('Nieprawidłowe pola dopisywania.')
        validate_rows(task['rows'])
    elif kind == 'edit_window_rows':
        if set(task) != {'kind', 'changes'} or not isinstance(task['changes'], list) or not 1 <= len(task['changes']) <= 50:
            raise ValueError('Nieprawidłowa lista korekt.')
        indices = []
        for change in task['changes']:
            if not isinstance(change, dict) or set(change) != {'row_number', 'fields'}:
                raise ValueError('Nieprawidłowa korekta.')
            indices.append(integer(change['row_number'], 1, 50))
            validate_fields(change['fields'])
        if len(set(indices)) != len(indices):
            raise ValueError('Powtórzona pozycja w korekcie.')
    elif kind == 'update_window_width':
        if set(task) != {'kind', 'row_number', 'width_mm'}:
            raise ValueError('Nieprawidłowe pola korekty.')
        integer(task['row_number'], 1, 50)
        integer(task['width_mm'], 100, 10000)
    elif kind in {'open_window_table', 'copy_window_table'}:
        if set(task) != {'kind', 'folder', 'file_name'}:
            raise ValueError('Nieprawidłowe pola wyboru pliku.')
        folder_name(task['folder'])
        file_name(task['file_name'])
    else:
        raise ValueError('Zaktualizuj wykonawcę lub wybierz obsługiwane zadanie tabeli okien.')
    return task


def parse_table(text):
    if not text.startswith(HEADER):
        raise ValueError('Plik nie ma formatu tabeli okien NaviMind.')
    rows = []
    for line in text[len(HEADER):].splitlines():
        parts = line.split('\t')
        if len(parts) != 4 or any(not value.isdecimal() for value in parts[1:]):
            raise ValueError('Nieprawidłowy wiersz tabeli.')
        rows.append({'label': parts[0], 'width_mm': int(parts[1]), 'height_mm': int(parts[2]), 'quantity': int(parts[3])})
    validate_rows(rows)
    if render_table(rows) != text:
        raise ValueError('Niestandardowe formatowanie tabeli.')
    return rows


def render_table(rows):
    return HEADER + ''.join(f"{r['label']}\t{r['width_mm']}\t{r['height_mm']}\t{r['quantity']}\n" for r in rows)


def read_text(path):
    if path.stat().st_size > 65536:
        raise ValueError('Plik jest za duży dla pilota tabel.')
    data = path.read_bytes()
    encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    return data.decode(encoding).replace('\r\n', '\n').rstrip('\n') + '\n'


def revision(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def table_revision(path, text):
    return revision(json.dumps({'folder': path.parent.name, 'file_name': path.name, 'text': text}, ensure_ascii=False, sort_keys=True))


def wait_for(read, description, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = read()
        if value:
            return value
        time.sleep(.2)
    raise RuntimeError('Upłynął czas oczekiwania: ' + description)


class NotepadWriter:
    """Keep one owned editor; never replace an unsaved user edit."""
    def __init__(self):
        self.window = None
        self.path = None
        self.pid = None

    def prepare(self, path, previous):
        from pywinauto import Application, Desktop
        from pywinauto.keyboard import send_keys
        import win32gui
        import win32process

        if self.window is None or self.path != path or not win32gui.IsWindow(self.window.handle):
            if self.window is not None and win32gui.IsWindow(self.window.handle):
                edit = self.window.descendants(class_name='Edit')
                if len(edit) != 1 or win32gui.SendMessage(edit[0].handle, 0x00B8, 0, 0):
                    raise RuntimeError('Poprzednia tabela ma niezapisane zmiany. Zapisz ją przed kolejnym zadaniem.')
            process = subprocess.Popen([str(Path(os.environ['SystemRoot']) / 'System32/notepad.exe')] + ([str(path)] if previous is not None else []))
            app = Application(backend='win32').connect(process=process.pid, timeout=15)
            def owned_window():
                windows = [w for w in app.windows() if w.is_visible() and w.class_name() == 'Notepad']
                if len(windows) > 1:
                    raise RuntimeError('Niejednoznaczne okno Notatnika.')
                return windows[0] if windows else None
            self.window = wait_for(owned_window, 'Notatnik')
            self.path = path
            self.pid = process.pid
            if win32process.GetWindowThreadProcessId(self.window.handle)[1] != process.pid:
                raise RuntimeError('Okno nie należy do wykonawcy.')
        window = self.window
        if win32process.GetWindowThreadProcessId(window.handle)[1] != self.pid:
            raise RuntimeError('Zmienił się proces edytora. Uruchom ponownie wykonawcę.')
        if (previous is None and path.exists()) or (previous is not None and read_text(path) != previous):
            raise RuntimeError('Plik zmienił się przed zapisem. Przerwano korektę.')
        edits = window.descendants(class_name='Edit')
        if len(edits) != 1:
            raise RuntimeError('Nie znaleziono pola klasycznego Notatnika.')
        edit = edits[0]
        actual = edit.window_text().replace('\r\n', '\n').rstrip('\n')
        if actual != (previous or '').rstrip('\n'):
            raise RuntimeError('Treść Notatnika została zmieniona ręcznie. Zapisz zmiany i rozpocznij nowe zadanie.')
        window.set_focus()
        if win32gui.GetForegroundWindow() != window.handle:
            raise RuntimeError('Notatnik nie uzyskał fokusu.')
        return window, edit

    def open(self, path, text, trace):
        window, _ = self.prepare(path, text)
        window.capture_as_image().save(trace / 'opened.png')
        if read_text(path) != text:
            raise RuntimeError('Plik zmienił się podczas otwierania.')

    def save(self, path, text, previous, trace):
        from pywinauto import Application, Desktop
        from pywinauto.keyboard import send_keys
        import win32gui
        window, edit = self.prepare(path, previous)
        def keys(control, sequence):
            control.set_focus()
            if win32gui.GetForegroundWindow() != control.handle:
                raise RuntimeError('Okno zadania utraciło fokus.')
            send_keys(sequence, pause=.05)

        window.capture_as_image().save(trace / 'before.png')
        edit.set_edit_text(text.replace('\n', '\r\n'))
        if edit.window_text().replace('\r\n', '\n').rstrip('\n') != text.rstrip('\n'):
            raise RuntimeError('Nie potwierdzono tekstu w Notatniku.')
        keys(window, '^s')
        if previous is None:
            def dialog_window():
                windows = Desktop(backend='win32').windows(process=self.pid, class_name='#32770', visible_only=True)
                return windows[0] if len(windows) == 1 else None
            dialog = wait_for(dialog_window, 'okno zapisu')
            uia = Application(backend='uia').connect(handle=dialog.handle).window(handle=dialog.handle)
            fields = [f for f in uia.descendants(control_type='Edit') if f.element_info.automation_id == '1001']
            if len(fields) != 1:
                raise RuntimeError('Niejednoznaczne pole nazwy pliku.')
            dialog.set_focus()
            if win32gui.GetForegroundWindow() != dialog.handle:
                raise RuntimeError('Okno zapisu nie uzyskało fokusu.')
            fields[0].set_edit_text(str(path))
            keys(dialog, '{ENTER}')
        def saved():
            try:
                return read_text(path) == text
            except (OSError, UnicodeError):
                return False
        wait_for(saved, 'zapis i odczyt tabeli')
        window.capture_as_image().save(trace / 'after.png')


class TableExecutor:
    def __init__(self, root, writer):
        self.root = Path(root).absolute()
        self.writer = writer
        self.active = None
        self.results = {}
        self.lock = threading.Lock()
        self.startup_warning = None
        self.restore_active()

    def safe_path(self, folder, filename):
        path = self.root / folder_name(folder) / file_name(filename)
        if self.root.is_symlink() or (hasattr(self.root, 'is_junction') and self.root.is_junction()):
            raise ValueError('Obszar pracy nie może być dowiązaniem.')
        # Reject reparse points even when they redirect to a different folder inside the root.
        directory = path.parent
        if directory.is_symlink() or (hasattr(directory, 'is_junction') and directory.is_junction()):
            raise ValueError('Folder nie może być dowiązaniem.')
        if path.is_symlink() or path.resolve().parent.parent != self.root.resolve():
            raise ValueError('Plik znajduje się poza obszarem pracy.')
        return path

    def catalog(self):
        tables = []
        if self.root.is_dir():
            for directory in sorted(self.root.iterdir()):
                if not directory.is_dir() or directory.name.startswith('.'):
                    continue
                for candidate in sorted(directory.glob('*.txt')):
                    try:
                        path = self.safe_path(directory.name, candidate.name)
                        text = read_text(path)
                        rows = parse_table(text)
                        tables.append({'folder': directory.name, 'file_name': path.name, 'row_count': len(rows), 'revision': table_revision(path, text)})
                    except (OSError, ValueError, UnicodeError):
                        continue
                    if len(tables) >= 50:
                        return tables
        return tables

    def restore_active(self):
        state = self.root / '.active-table.json'
        try:
            if state.exists():
                if state.is_symlink() or state.stat().st_size > 4096:
                    raise ValueError('Nieprawidłowy zapis aktywnej tabeli.')
                saved = json.loads(state.read_text(encoding='utf-8'))
                path = self.safe_path(saved['folder'], saved['file_name'])
                text = read_text(path)
                if table_revision(path, text) != saved['revision']:
                    raise ValueError('Ostatni plik zmieniono poza agentem. Otwórz go ponownie poleceniem, aby wczytać zapisane dane.')
                self.active = (path, parse_table(text), saved['revision'])
            else:
                tables = self.catalog()
                if len(tables) == 1:
                    item = tables[0]
                    path = self.safe_path(item['folder'], item['file_name'])
                    text = read_text(path)
                    self.active = (path, parse_table(text), table_revision(path, text))
        except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
            self.startup_warning = str(exc)

    def remember(self):
        path, _, expected = self.active
        state = self.root / '.active-table.json'
        if state.is_symlink():
            raise ValueError('Nieprawidłowy plik stanu.')
        temporary = self.root / ('.active-' + secrets.token_hex(8) + '.tmp')
        try:
            temporary.write_text(json.dumps({'folder': path.parent.name, 'file_name': path.name, 'revision': expected}), encoding='utf-8')
            temporary.replace(state)
        finally:
            temporary.unlink(missing_ok=True)
        self.startup_warning = None

    def current(self):
        if not self.active:
            return None
        path, rows, expected = self.active
        if path != self.safe_path(path.parent.name, path.name) or read_text(path) != render_table(rows):
            raise ValueError('Plik zmieniono poza agentem. Otwórz go ponownie poleceniem, aby wczytać zapisane zmiany.')
        return {'folder': path.parent.name, 'file_name': path.name, 'rows': rows, 'revision': expected, 'file': str(path)}

    def status(self):
        warning = self.startup_warning
        try:
            current = self.current()
        except (ValueError, OSError, UnicodeError) as exc:
            current = None
            warning = str(exc)
        return {'status': 'ready', 'protocol': 1, 'capabilities': CAPABILITIES, 'currentTable': current, 'tables': self.catalog(), 'warning': warning}

    def execute(self, body):
        if not isinstance(body, dict) or set(body) != {'id', 'task', 'expectedRevision'}:
            raise ValueError('Nieprawidłowe żądanie wykonania.')
        job_id = body['id']
        if not isinstance(job_id, str) or not re.fullmatch(r'[a-zA-Z0-9-]{16,80}', job_id):
            raise ValueError('Nieprawidłowy identyfikator zadania.')
        task = validate_task(body['task'])
        fingerprint = revision(json.dumps(body, sort_keys=True, ensure_ascii=False))
        if not self.lock.acquire(blocking=False):
            raise RuntimeError('Agent wykonuje poprzednie zadanie. Poczekaj na wynik.')
        trace = None
        reserved = False
        try:
            if job_id in self.results:
                previous_fingerprint, result = self.results[job_id]
                if previous_fingerprint != fingerprint:
                    raise ValueError('Identyfikator wykorzystano do innego zadania.')
                return result
            if len(self.results) >= 500:
                raise ValueError('Zakończ tę sesję wykonawcy i uruchom nową.')
            result = {'status': 'review', 'message': 'Zadanie rozpoczęto. Nie ponawiaj automatycznie.'}
            self.results[job_id] = (fingerprint, result)
            reserved = True
            kind = task['kind']
            previous = None
            if kind == 'create_window_table':
                if body['expectedRevision'] is not None:
                    raise ValueError('Tworzenie tabeli nie wymaga wersji poprzedniej.')
                path = self.safe_path(task['folder'], task.get('file_name', 'tabela-okien.txt'))
                rows = json.loads(json.dumps(task['rows']))
                message = 'Utworzono i sprawdzono nową tabelę.'
            elif kind == 'open_window_table':
                path = self.safe_path(task['folder'], task['file_name'])
                text = read_text(path)
                rows = parse_table(text)
                if body['expectedRevision'] != table_revision(path, text):
                    raise ValueError('Plik zmienił się od wyboru zadania. Wybierz go ponownie.')
                message = 'Otworzono i odczytano tabelę. To aktywny plik do kolejnych zmian.'
            else:
                current = self.current()
                if not current or body['expectedRevision'] != current['revision']:
                    raise ValueError('Tabela lub jej wersja nie zgadza się z poleceniem. Wczytaj aktualny plik ponownie.')
                path, old_rows, _ = self.active
                rows = json.loads(json.dumps(old_rows))
                if kind == 'copy_window_table':
                    path = self.safe_path(task['folder'], task['file_name'])
                    message = 'Zapisano kopię tabeli w osobnym pliku. Plik źródłowy zachowano.'
                else:
                    previous = render_table(old_rows)
                    if kind == 'append_window_rows':
                        rows.extend(json.loads(json.dumps(task['rows'])))
                        validate_rows(rows)
                        message = f"Dopisano {len(task['rows'])} pozycji. Wcześniejsze pozycje zachowano."
                    else:
                        changes = task['changes'] if kind == 'edit_window_rows' else [{'row_number': task['row_number'], 'fields': {'width_mm': task['width_mm']}}]
                        for change in changes:
                            index = change['row_number'] - 1
                            if index >= len(rows):
                                raise ValueError('Wskazana pozycja nie istnieje.')
                            rows[index].update(change['fields'])
                        validate_rows(rows)
                        message = 'Zmieniono wskazane pola. Pozostałe dane i pozycje zachowano.'
            if kind in {'create_window_table', 'copy_window_table'}:
                if path.exists() or path.is_symlink():
                    raise ValueError('Plik już istnieje. Użyj dopisywania/edycji albo podaj nową nazwę pliku.')
                path.parent.mkdir(parents=True, exist_ok=True)
            trace = self.root / '.traces' / job_id
            trace.mkdir(parents=True)
            text = render_table(rows)
            if kind == 'open_window_table':
                self.writer.open(path, text, trace)
            else:
                self.writer.save(path, text, previous, trace)
            if read_text(path) != text:
                raise RuntimeError('Zapisana tabela nie zgadza się z poleceniem.')
            self.active = (path, rows, table_revision(path, text))
            self.remember()
            result = {'status': 'verified', 'message': message, 'file': str(path), 'rows': rows, 'revision': table_revision(path, text)}
        except Exception as exc:
            result = {'status': 'review', 'message': str(exc)}
        finally:
            try:
                if trace:
                    (trace / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
                if reserved:
                    self.results[job_id] = (fingerprint, result)
            finally:
                self.lock.release()
        return result


def handler_for(executor, token, port=PORT, origins=None):
    allowed = set(origins or ORIGINS)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Never log bearer tokens, task text or URL queries.

        def trusted(self):
            return (self.headers.get('Host') == f'127.0.0.1:{port}' and self.headers.get('Origin') in allowed)

        def send_json(self, status, body):
            payload = json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            if self.trusted():
                self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])
                self.send_header('Vary', 'Origin')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_OPTIONS(self):
            headers = {h.strip().lower() for h in self.headers.get('Access-Control-Request-Headers', '').split(',') if h.strip()}
            if not self.trusted() or (self.path not in {'/status', '/execute'} and not re.fullmatch(r'/result/[a-zA-Z0-9-]{16,80}', self.path)) or not headers <= {'authorization', 'content-type'} or self.headers.get('Access-Control-Request-Method') not in {'GET', 'POST'}:
                return self.send_json(403, {'error': 'ORIGIN_DENIED'})
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])
            self.send_header('Vary', 'Origin')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
            self.send_header('Access-Control-Allow-Private-Network', 'true')
            self.send_header('Content-Length', '0')
            self.end_headers()

        def authorized(self):
            return self.trusted() and hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token)

        def do_GET(self):
            if not self.authorized():
                return self.send_json(403, {'error': 'PAIRING_REQUIRED'})
            if self.path.startswith('/result/'):
                job_id = self.path.removeprefix('/result/')
                cached = executor.results.get(job_id)
                return self.send_json(200, cached[1]) if cached else self.send_json(404, {'status': 'review', 'message': 'Nie znaleziono wyniku w tej sesji wykonawcy. Sprawdź plik i okno PowerShell; zadania nie ponowiono.'})
            if self.path != '/status':
                return self.send_json(404, {'error': 'NOT_FOUND'})
            try:
                self.send_json(200, executor.status())
            except Exception as exc:
                self.send_json(409, {'status': 'review', 'message': str(exc)})

        def do_POST(self):
            if not self.authorized():
                return self.send_json(403, {'error': 'PAIRING_REQUIRED'})
            if self.path != '/execute':
                return self.send_json(404, {'error': 'NOT_FOUND'})
            try:
                if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    raise ValueError('Wymagany JSON.')
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 32768:
                    raise ValueError('Nieprawidłowy rozmiar zadania.')
                self.connection.settimeout(10)
                body = json.loads(self.rfile.read(size))
                result = executor.execute(body)
                self.send_json(200, result)
            except (ValueError, UnicodeError) as exc:
                self.send_json(400, {'status': 'review', 'message': str(exc)})
            except Exception as exc:
                self.send_json(409, {'status': 'review', 'message': str(exc)})
    return Handler


def desktop_path():
    buffer = ctypes.create_unicode_buffer(260)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buffer) != 0:
        raise RuntimeError('Nie znaleziono Pulpitu.')
    return Path(buffer.value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-live', action='store_true')
    args = parser.parse_args()
    if os.name != 'nt' or not args.execute_live:
        print('Uruchom na Windows: python tools/run_navimind_desktop_bridge.py --execute-live')
        return 2
    # Fail at startup, before pairing, if native automation dependencies are missing.
    import pywinauto  # noqa: F401
    import win32gui  # noqa: F401
    import pythoncom
    pythoncom.CoInitialize()
    token = secrets.token_urlsafe(32)
    executor = TableExecutor(desktop_path() / 'NaviMind-Praca', NotepadWriter())
    try:
        server = HTTPServer(('127.0.0.1', PORT), handler_for(executor, token))
    except OSError:
        print('DESKTOP_BRIDGE=port_busy Zamknij poprzednie okno wykonawcy i ponów.')
        return 6
    print('DESKTOP_BRIDGE=ready', flush=True)
    print('OBSZAR_PRACY=' + str(executor.root), flush=True)
    print('KOD_PAROWANIA=' + token, flush=True)
    try:
        subprocess.run(['powershell.exe', '-NoProfile', '-STA', '-Command', 'Set-Clipboard -Value ([Console]::In.ReadToEnd())'], input=token, text=True, check=True, capture_output=True)
        print('Kod skopiowano. W NaviMind kliknij Połącz komputer, wklej Ctrl+V i połącz.', flush=True)
    except Exception:
        print('Skopiuj kod parowania z tego okna do NaviMind. Nie wysyłaj go w rozmowie.', flush=True)
    print('Otwórz https://www.navimind.app/workspace. Zostaw to okno otwarte. Zatrzymanie: Ctrl+C.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
