"""Exercise the shared synthetic fixtures in real Chromium, without model calls.

Positive cases replay semantic fields. Negative cases check form capabilities only;
only the separate NaviMind real-model gate checks whether AI asks the right question.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets

try:
    from .navimind_browser import BrowserController
except ImportError:
    from navimind_browser import BrowserController

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'contracts/browser-regression-v1.json'
NAMES = {'width': 'Szerokość [mm]', 'height': 'Wysokość [mm]', 'color': 'Kolor zewnętrzny', 'opening': 'Otwieranie'}


def run_suite(headless=True):
    from playwright.sync_api import sync_playwright
    payload = FIXTURE.read_bytes()
    suite = json.loads(payload)
    report = {'version': suite['version'], 'fixture_sha256': hashlib.sha256(payload).hexdigest(),
              'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'running',
              'real_chromium': True, 'real_model': False, 'submitted': False, 'cases': []}
    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(headless=headless)
        try:
            for scenario in suite['scenarios']:
                page = browser.new_page(viewport={'width': 1280, 'height': 850})
                try:
                    page.set_content((ROOT / 'tools/navimind_browser_lab.html').read_text(encoding='utf-8'))
                    agent = BrowserController(page)

                    def step(kind, name, **fields):
                        for attempt in range(3):
                            before = agent.observe()
                            matches = [c for c in before['controls'] if c['name'] == name]
                            if len(matches) != 1:
                                raise RuntimeError('TARGET_NOT_UNIQUE ' + name)
                            result = agent.execute({'id': secrets.token_hex(16), 'task': {'kind': kind, 'ref': matches[0]['ref'], **fields}, 'expectedRevision': before['revision']})
                            # Match the frontend: reobserve at most twice only when
                            # STALE_PAGE guarantees the action did not start.
                            if result.get('code') == 'STALE_PAGE' and attempt < 2:
                                print('BROWSER_EXECUTOR_REOBSERVE TARGET='+name)
                                continue
                            if result['status'] != 'verified':
                                raise RuntimeError('EXECUTION_NOT_VERIFIED '+name+' '+result.get('code','')+' '+result['message']+' REQUESTED='+str(fields.get('value',''))+' OPTIONS='+str(matches[0].get('options',[])))
                            return result['browser']

                    def current():
                        return {'customer': page.locator('#chosen').inner_text().removeprefix('Wybrany klient: ') if page.locator('#chosen').inner_text().startswith('Wybrany klient: ') else '',
                                **{key: page.locator('#'+key).input_value() for key in NAMES}}

                    def fill_expected(expected, changed):
                        if 'customer' in changed:
                            step('browser_fill', 'Wyszukaj klienta', text=expected['customer'])
                            step('browser_click', expected['customer'])
                        for key in NAMES:
                            if key in changed:
                                step('browser_select' if key in ('color', 'opening') else 'browser_fill', NAMES[key], **({'value': expected[key]} if key in ('color', 'opening') else {'text': expected[key]}))

                    if scenario['seed']:
                        fill_expected(scenario['seed'], list(scenario['seed']))
                        step('browser_click', 'Pokaż podgląd')
                    for phase in scenario['phases']:
                        case = {'id': scenario['id']+'/'+phase['id'], 'status': 'running',
                                'coverage': 'executor_replay' if phase['expected'] else 'form_capability_only'}
                        report['cases'].append(case)
                        before = current()
                        if phase['expected']:
                            # A continuation must work even when its field is above the viewport.
                            if scenario['seed'] or phase != scenario['phases'][0]:
                                page.set_viewport_size({'width': 1280, 'height': 360})
                                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                            fill_expected(phase['expected'], phase['allowed_write_fields'])
                            if 'PODGLĄD GOTOWY' in page.locator('#summary').inner_text():
                                raise RuntimeError('STALE_PREVIEW_STILL_READY')
                            final = step('browser_click', 'Pokaż podgląd')
                            if current() != phase['expected']:
                                raise RuntimeError('FINAL_FIELDS_MISMATCH')
                            for text in ['PODGLĄD GOTOWY', 'Klient: '+phase['expected']['customer'], 'Szerokość: '+phase['expected']['width']+' mm', 'Wysokość: '+phase['expected']['height']+' mm', 'Kolor: '+phase['expected']['color'], 'Okucie: '+phase['expected']['opening']]:
                                if text not in final['text']:
                                    raise RuntimeError('PREVIEW_MISMATCH')
                        elif phase['probe'] == 'ambiguous_customer':
                            view = step('browser_fill', 'Wyszukaj klienta', text='Top')
                            choices = [c['name'] for c in view['controls'] if c['tag'] == 'button']
                            if not all(name in choices for name in ('Top Trans', 'Top Trans S.A.')) or current()['customer']:
                                raise RuntimeError('AMBIGUOUS_SEARCH_CAPABILITY_FAILED')
                        elif phase['probe'] == 'missing_height':
                            fill_expected({'customer':'Top Trans','width':'1100','color':'antracyt','opening':'DKR'}, phase['allowed_write_fields'])
                            view = step('browser_click', 'Pokaż podgląd')
                            if current()['height'] or 'PODGLĄD GOTOWY' in view['text']:
                                raise RuntimeError('INCOMPLETE_PREVIEW_ACCEPTED')
                        elif phase['probe'] == 'unavailable_color':
                            color = next(c for c in agent.observe()['controls'] if c['name'] == NAMES['color'])
                            if any('zielon' in o['label'].lower() or o['value'] == 'green' for o in color['options']):
                                raise RuntimeError('UNAVAILABLE_COLOR_FIXTURE_CHANGED')
                        else:
                            raise RuntimeError('UNKNOWN_PROBE')
                        after = current()
                        for key in before:
                            if key not in phase['allowed_write_fields'] and before[key] != after[key]:
                                raise RuntimeError('UNREQUESTED_FIELD_CHANGED '+key)
                        case['status'] = 'passed'
                        print('BROWSER_EXECUTOR_CASE=passed CASE='+case['id']+' COVERAGE='+case['coverage'])
                finally:
                    page.close()
        except Exception as problem:
            report['status'] = 'failed'
            if report['cases'] and report['cases'][-1]['status'] == 'running':
                report['cases'][-1]['status'] = 'failed'
            report['error'] = type(problem).__name__ + ': ' + str(problem)[:250]
        finally:
            browser.close()
    if report['status'] == 'running':
        report['status'] = 'passed'
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-live', action='store_true')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--report-directory', type=Path)
    args = parser.parse_args()
    if not args.execute_live:
        print('Pass --execute-live to open the owned Chromium laboratory.')
        return 2
    report = run_suite(args.headless)
    if args.report_directory:
        args.report_directory.mkdir(parents=True, exist_ok=True)
        target = args.report_directory / ('browser-regression-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(5)+'.json')
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        if json.loads(target.read_text(encoding='utf-8')) != report:
            raise RuntimeError('REPORT_READBACK_FAILED')
        print('BROWSER_REGRESSION_REPORT='+str(target.resolve()))
    print('BROWSER_EXECUTOR_SUITE='+report['status']+' CASES='+str(len(report['cases']))+' FIXTURE_SHA256='+report['fixture_sha256'])
    if report['status'] != 'passed':
        print('BROWSER_EXECUTOR_ERROR='+report.get('error', 'unknown'))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
