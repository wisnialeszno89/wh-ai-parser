"""Owned Chromium session: bounded observations and one verified browser action at a time."""
from __future__ import annotations
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import secrets
import threading
from urllib.parse import urlsplit, urlunsplit

SELECTOR = 'a[href],button,input,textarea,select,[role="button"],[role="link"],[role="checkbox"]'
SENSITIVE = re.compile(r'refund|zwrot|payout|wypłat|wyplat|pay now|purchase|buy now|zapła|zaplac|checkout|delete|usuń|usun|remove|send|wyślij|wyslij|submit|confirm|potwierd|place order|zamawiam|subscribe|subskryb|transfer|przelew|password|hasło|haslo|sign in|log in|zaloguj|otp|2fa|card number|numer karty|cvv|cvc', re.I)
FIELDS = re.compile(r'password|hasło|haslo|otp|2fa|one.time|credit|card|karta|cvv|cvc|token|secret|api.key|ssn', re.I)


def public_url(value):
    if not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 32 for c in value):
        raise ValueError('Nieprawidłowy adres strony.')
    try:
        url = urlsplit(value)
        host = (url.hostname or '').lower()
        port = url.port
        if url.scheme not in {'https', 'http'} or not host or url.username or url.password or port not in {None, 80, 443}:
            raise ValueError()
        if host in {'localhost', 'localhost.localdomain'} or host.endswith(('.localhost', '.local', '.internal')) or '.' not in host:
            raise ValueError()
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address is None and all(re.fullmatch(r'(?:0x[0-9a-f]+|[0-9]+)', part) for part in host.split('.')):
            raise ValueError()
        if address is not None and not address.is_global:
            raise ValueError()
    except ValueError:
        raise ValueError('Użyj publicznego adresu http/https bez danych logowania i niestandardowego portu.') from None
    return value


def validate_browser_task(task):
    if not isinstance(task, dict):
        raise ValueError('Nieprawidłowy krok przeglądarki.')
    kind = task.get('kind')
    fields = {'browser_navigate': {'kind', 'url'}, 'browser_click': {'kind', 'ref'}, 'browser_fill': {'kind', 'ref', 'text'}, 'browser_select': {'kind', 'ref', 'value'}, 'browser_scroll': {'kind', 'direction'}, 'browser_back': {'kind'}}
    if kind not in fields or set(task) != fields[kind]:
        raise ValueError('Nieobsługiwany krok przeglądarki.')
    if 'url' in task:
        public_url(task['url'])
    if 'ref' in task and (not isinstance(task['ref'], str) or not re.fullmatch(r'e[0-9a-f]{16}', task['ref'])):
        raise ValueError('Wybierz element z aktualnego widoku.')
    for key in ('text', 'value'):
        if key in task and (not isinstance(task[key], str) or len(task[key]) > 2000 or '\x00' in task[key]):
            raise ValueError('Tekst kroku jest za długi lub nieprawidłowy.')
    if kind == 'browser_scroll' and task['direction'] not in {'up', 'down'}:
        raise ValueError('Nieprawidłowy kierunek przewijania.')
    return task


COLLECT = """els => {
 const clip = (s,n) => String(s || '').replace(/\\s+/g,' ').trim().slice(0,n);
 const controls = els.map((el,index) => {
  const r=el.getBoundingClientRect(), style=getComputedStyle(el);
  if(!r.width || !r.height || r.bottom<0 || r.top>innerHeight || style.visibility==='hidden' || style.display==='none' || el.type==='hidden') return null;
  const labelled=clip((el.getAttribute('aria-labelledby')||'').split(' ').map(id=>document.getElementById(id)?.innerText||'').join(' '),180);
  const name=clip(el.getAttribute('aria-label') || labelled || Array.from(el.labels||[]).map(l=>l.innerText).join(' ') || el.innerText || el.getAttribute('placeholder') || el.title || el.name,180);
  return {index,tag:el.tagName.toLowerCase(),role:el.getAttribute('role')||'',type:el.type||'',name,href:el.tagName==='A'?el.href:'',disabled:!!el.disabled || el.getAttribute('aria-disabled')==='true',checked:!!el.checked,
   autocomplete:el.autocomplete||'',context:clip(el.closest('form,[role="dialog"]')?.innerText,300),
   value:('value' in el)?String(el.value):null,
   options:el.tagName==='SELECT'?Array.from(el.options).slice(0,30).map(o=>({label:clip(o.label,100),value:o.value})):undefined};
 }).filter(Boolean).slice(0,80);
 return {title:clip(document.title,200),text:clip(document.body?.innerText,12000),scroll_y:Math.round(scrollY),controls};
}"""


class StalePage(ValueError):
    pass


class BrowserController:
    def __init__(self, page, results=None, test_mode=False):
        self.page = page
        self.results = results if results is not None else {}
        self.test_mode = test_mode
        self.lock = threading.Lock()
        self.refs = {}
        self.latest = None
        self.sequence = 0
        self.page.set_default_timeout(6000)
        self.page.set_default_navigation_timeout(12000)
        # Never accept Javascript dialogs or start downloading files for the model.
        self.page.on('dialog', lambda dialog: dialog.dismiss())
        self.page.on('download', lambda download: download.cancel())

    def _url(self, value):
        if self.test_mode and value == 'about:blank':
            return value
        return public_url(value)

    def _capture(self, register=False):
        if self.page.is_closed():
            raise ValueError('Okno NaviMind zostało zamknięte. Uruchom wykonawcę ponownie.')
        url = self.page.url
        if url != 'about:blank':
            self._url(url)
        handles = self.page.locator(SELECTOR).element_handles()
        data = self.page.evaluate(COLLECT, handles)
        data['url'] = url
        data['sequence'] = self.sequence
        fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        controls = []
        refs = {}
        for item in data['controls']:
            ref = 'e' + secrets.token_hex(8) if register else ''
            if register:
                refs[ref] = (handles[item['index']], item)
            # Field contents, form context and autocomplete are used locally, never sent to the model.
            control = {k: v for k, v in item.items() if k not in {'index', 'value', 'context', 'autocomplete'} and v is not None}
            if control.get('href'):
                link = urlsplit(control['href'])
                control['href'] = urlunsplit((link.scheme, link.netloc.split('@')[-1], link.path, '', ''))[:2048]
            control.update(ref=ref, value_present=bool(item['value']))
            controls.append(control)
        location = urlsplit(url)
        display_url = urlunsplit((location.scheme, location.netloc.split('@')[-1], location.path, '', ''))
        snapshot = {'revision': fingerprint, 'url': display_url, 'title': data['title'], 'text': data['text'], 'controls': controls, 'scope': 'owned_chromium_tab'}
        if register:
            for handle, _ in self.refs.values():
                handle.dispose()
            self.refs = refs
            self.latest = snapshot
        else:
            for handle in handles:
                handle.dispose()
        # Dispose non-visible handles as well.
        if register:
            visible = {item['index'] for item in data['controls']}
            for i, handle in enumerate(handles):
                if i not in visible:
                    handle.dispose()
        return snapshot

    def observe(self):
        return self._capture(register=True)

    def _target(self, task):
        if task['ref'] not in self.refs:
            raise ValueError('Element nie pochodzi z aktualnego widoku.')
        handle, meta = self.refs[task['ref']]
        if not handle.evaluate('(el) => el.isConnected') or not handle.is_visible() or not handle.is_enabled():
            raise StalePage('Element zmienił się albo nie jest dostępny. Odczytaj stronę ponownie.')
        if meta['disabled']:
            raise ValueError('Element jest wyłączony.')
        return handle, meta

    def _act(self, task):
        kind = task['kind']
        if kind == 'browser_navigate':
            self.page.goto(self._url(task['url']), wait_until='domcontentloaded')
            return 'Otworzono stronę i odczytano jej aktualny widok.'
        if kind == 'browser_back':
            self.page.go_back(wait_until='domcontentloaded')
            return 'Wrócono do poprzedniej strony i odczytano jej widok.'
        if kind == 'browser_scroll':
            self.page.evaluate('(d) => window.scrollBy(0,d*innerHeight*.75)', 1 if task['direction'] == 'down' else -1)
            self.page.wait_for_timeout(150)
            return 'Przewinięto stronę i odczytano widoczne elementy.'
        handle, meta = self._target(task)
        label = ' '.join([meta['name'], meta['autocomplete'], meta['context']])
        if kind == 'browser_fill':
            if meta['tag'] not in {'input', 'textarea'} or meta['type'] not in {'text', 'search', 'email', 'url', 'tel', 'number', 'textarea', ''} or FIELDS.search(label):
                raise ValueError('To pole wymaga ręcznego uzupełnienia. Agent nie wpisuje haseł, kodów ani danych płatniczych.')
            handle.fill(task['text'])
            if handle.input_value() != task['text']:
                raise ValueError('Nie potwierdzono treści pola po wpisaniu.')
            return 'Wpisano tekst i sprawdzono zawartość pola.'
        if kind == 'browser_select':
            if meta['tag'] != 'select' or SENSITIVE.search(label):
                raise ValueError('Ten wybór wymaga ręcznej obsługi.')
            if task['value'] not in {option['value'] for option in meta.get('options', [])}:
                raise ValueError('Opcja nie pochodzi z aktualnej listy.')
            handle.select_option(value=task['value'])
            if handle.input_value() != task['value']:
                raise ValueError('Nie potwierdzono wybranej opcji.')
            return 'Wybrano opcję i sprawdzono wartość pola.'
        if meta['tag'] in {'input', 'textarea', 'select'} or meta['type'] in {'submit', 'reset'} or SENSITIVE.search(label):
            raise ValueError('Ten przycisk wymaga ręcznej obsługi: zatwierdzanie formularzy, płatności, zwrotów, wysyłania i usuwania pozostaje użytkownikowi.')
        if meta['href']:
            self._url(meta['href'])
        handle.click(no_wait_after=True)
        self.page.wait_for_timeout(350)
        return 'Kliknięto wskazany element i odczytano stronę po kroku. Oceń efekt w nowym widoku.'

    def execute(self, body):
        if not isinstance(body, dict) or set(body) != {'id', 'task', 'expectedRevision'} or not isinstance(body['id'], str) or not re.fullmatch(r'[a-zA-Z0-9-]{16,80}', body['id']):
            raise ValueError('Nieprawidłowe zadanie przeglądarki.')
        task = validate_browser_task(body['task'])
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        with self.lock:
            cached = self.results.get(body['id'])
            if cached:
                if cached[0] != digest:
                    return {'status': 'review', 'message': 'Identyfikator należy do innego zadania.'}
                return cached[1]
            if len(self.results) >= 500:
                raise ValueError('Uruchom nową sesję wykonawcy.')
            result = {'status': 'review', 'message': 'Krok rozpoczęto; nie ponawiaj go automatycznie.'}
            self.results[body['id']] = (digest, result)
            try:
                if not self.latest or body['expectedRevision'] != self.latest['revision'] or self._capture()['revision'] != body['expectedRevision']:
                    raise StalePage('Strona zmieniła się od przygotowania kroku. Odczytaj ją ponownie.')
                message = self._act(task)
                self.sequence += 1
                snapshot = self.observe()
                result = {'status': 'verified', 'message': message, 'browser': snapshot}
            except Exception as exc:
                # Page text, credentials and request URLs are not persisted to trace files.
                message = str(exc)[:600] if isinstance(exc, ValueError) else 'Nie potwierdzono kroku przeglądarki. Sprawdź widoczne okno; zadania nie ponowiono. (' + type(exc).__name__ + ')'
                result = {'status': 'review', 'message': message, 'code': 'STALE_PAGE' if isinstance(exc, StalePage) else 'BROWSER_REVIEW'}
            self.results[body['id']] = (digest, result)
            return result


class DesktopWithBrowser:
    def __init__(self, tables, browser):
        self.tables, self.browser = tables, browser
        self.results = tables.results
        browser.results = self.results
        self.root = tables.root

    def status(self):
        return {**self.tables.status(), 'browser': {'available': not self.browser.page.is_closed(), 'scope': 'owned_chromium_tab'}}

    def browser_observe(self):
        try:
            return self.browser.observe()
        except ValueError:
            raise
        except Exception:
            raise ValueError('Nie udało się odczytać karty Chromium NaviMind. Sprawdź, czy okno jest otwarte i strona zakończyła ładowanie.') from None

    def execute(self, body):
        if isinstance(body, dict) and isinstance(body.get('task'), dict) and str(body['task'].get('kind', '')).startswith('browser_'):
            return self.browser.execute(body)
        return self.tables.execute(body)


def start_browser(profile):
    from playwright.sync_api import sync_playwright
    runtime = sync_playwright().start()
    try:
        context = runtime.chromium.launch_persistent_context(str(profile), headless=False, accept_downloads=False, viewport={'width': 1280, 'height': 850})
        page = context.pages[0] if context.pages else context.new_page()
        if page.url == 'about:blank':
            page.set_content(Path(__file__).with_name('navimind_browser_lab.html').read_text(encoding='utf-8'))
        # The controlled page is fixed; other pages and the user's usual browser are untouched.
        return runtime, context, BrowserController(page)
    except Exception:
        runtime.stop()
        raise
