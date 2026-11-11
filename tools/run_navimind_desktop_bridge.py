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


def validate_task(task):
    if not isinstance(task, dict):
        raise ValueError("Nieprawidłowe zadanie.")
    if task.get('kind') == 'create_window_table':
        if set(task) != {'kind', 'folder', 'rows'}:
            raise ValueError("Nieprawidłowe pola zadania.")
        folder_name(task['folder'])
        rows = task['rows']
        if not isinstance(rows, list) or not 1 <= len(rows) <= 50:
            raise ValueError("Tabela musi zawierać 1–50 pozycji.")
        for row in rows:
            if not isinstance(row, dict) or set(row) != {'label', 'width_mm', 'height_mm', 'quantity'}:
                raise ValueError("Nieprawidłowa pozycja.")
            label = row['label']
            if not isinstance(label, str) or not label.strip() or len(label) > 120 or any(ord(c) < 32 for c in label):
                raise ValueError("Nieprawidłowy opis pozycji.")
            integer(row['width_mm'], 100, 10000)
            integer(row['height_mm'], 100, 10000)
            integer(row['quantity'], 1, 999)
    elif task.get('kind') == 'update_window_width':
        if set(task) != {'kind', 'row_number', 'width_mm'}:
            raise ValueError("Nieprawidłowe pola korekty.")
        integer(task['row_number'], 1, 50)
        integer(task['width_mm'], 100, 10000)
    else:
        raise ValueError("Ten wykonawca obsługuje tworzenie tabeli okien i korektę szerokości.")
    return task


def render_table(rows):
    return HEADER + ''.join(f"{r['label']}\t{r['width_mm']}\t{r['height_mm']}\t{r['quantity']}\n" for r in rows)


def read_text(path):
    data = path.read_bytes()
    encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    return data.decode(encoding).replace('\r\n', '\n').rstrip('\n') + '\n'


def revision(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


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

    def save(self, path, text, previous, trace):
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
        def keys(control, sequence):
            control.set_focus()
            if win32gui.GetForegroundWindow() != control.handle:
                raise RuntimeError('Okno zadania utraciło fokus.')
            send_keys(sequence, pause=.05)

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
        window.capture_as_image().save(trace / 'before.png')
        edit.set_edit_text(text.replace('\n', '\r\n'))
        if edit.window_text().replace('\r\n', '\n').rstrip('\n') != text.rstrip('\n'):
            raise RuntimeError('Nie potwierdzono tekstu w Notatniku.')
        keys(window, '^s')
        if previous is None:
            def dialog_window():
                windows = Desktop(backend='win32').windows(process=process.pid, class_name='#32770', visible_only=True)
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

    def current(self):
        if not self.active:
            return None
        path, rows, expected = self.active
        if path.is_symlink() or path.resolve().parent.parent != self.root.resolve() or read_text(path) != render_table(rows):
            raise ValueError('Plik zmieniono poza agentem. Utwórz nową tabelę lub uruchom ponownie wykonawcę.')
        return {'folder': path.parent.name, 'rows': rows, 'revision': expected, 'file': str(path)}

    def status(self):
        return {'status': 'ready', 'protocol': 1, 'capabilities': ['create_window_table', 'update_window_width'], 'currentTable': self.current()}

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
            # Reserve before side effects; failures are never re-executed silently.
            result = {'status': 'review', 'message': 'Zadanie rozpoczęto. Nie ponawiaj automatycznie.'}
            self.results[job_id] = (fingerprint, result)
            reserved = True
            previous = None
            if task['kind'] == 'create_window_table':
                if body['expectedRevision'] is not None:
                    raise ValueError('Tworzenie tabeli nie wymaga wersji poprzedniej.')
                target_dir = self.root / folder_name(task['folder'])
                if target_dir.exists() or target_dir.is_symlink():
                    raise ValueError('Folder już istnieje. Podaj inną nazwę; agent nie zastąpi istniejącej oferty.')
                self.root.mkdir(parents=True, exist_ok=True)
                if self.root.is_symlink() or (hasattr(self.root, 'is_junction') and self.root.is_junction()) or target_dir.resolve().parent != self.root.resolve():
                    raise ValueError('Folder znajduje się poza obszarem pracy.')
                target_dir.mkdir()
                path = target_dir / 'tabela-okien.txt'
                rows = json.loads(json.dumps(task['rows']))
            else:
                current = self.current()
                if not current or body['expectedRevision'] != current['revision']:
                    raise ValueError('Tabela lub jej wersja nie zgadza się z poleceniem. Połącz ponownie i spróbuj jeszcze raz.')
                path, old_rows, _ = self.active
                rows = json.loads(json.dumps(old_rows))
                index = task['row_number'] - 1
                if index >= len(rows):
                    raise ValueError('Wskazana pozycja nie istnieje.')
                previous = render_table(old_rows)
                rows[index]['width_mm'] = task['width_mm']
            trace = self.root / '.traces' / job_id
            trace.mkdir(parents=True)
            text = render_table(rows)
            self.writer.save(path, text, previous, trace)
            if read_text(path) != text:
                raise RuntimeError('Zapisana tabela nie zgadza się z poleceniem.')
            self.active = (path, rows, revision(text))
            result = {'status': 'verified', 'message': 'Zapisano i sprawdzono tabelę.' if previous is None else 'Zmieniono szerokość wskazanej pozycji. Pozostałe dane zachowano.', 'file': str(path), 'rows': rows, 'revision': revision(text)}
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
