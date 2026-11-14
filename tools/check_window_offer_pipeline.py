"""Local contract -> compatibility -> optional public-form readback check.

Default data is synthetic. Each invocation owns a fresh report directory;
an older successful report can never prove the current invocation succeeded.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.window_offer_specification import read_offer_specification, prepare_pagen_specification
from app.agent.offers.catalog_control_binding import normalized_label
from app.agent.offers.pagen_configurator import PagenOrder, fill_pagen_order

DEFAULT_SPECIFICATION = ROOT / 'contracts/window-offer-two-fix.example.json'


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def verify_readback(report, order):
    """Compare observed form fields to the source projection, never just a success word."""
    if (report.get('status') != 'form_verified' or report.get('evidence') != 'browser_dom_readback'
            or report.get('submitted') is not False or report.get('wh_offer_created') is not False
            or report.get('sales_review_required') is not True):
        raise ValueError('FORM_READBACK_NOT_VERIFIED')
    profile = report.get('profile', {})
    if (normalized_label(profile.get('observed_label', '')) != normalized_label(order.profile)
            or not profile.get('observed_value')):
        raise ValueError('PROFILE_READBACK_MISMATCH')
    rows = report.get('positions', [])
    if len(rows) != len(order.positions):
        raise ValueError('POSITION_COUNT_READBACK_MISMATCH')
    for index, (row, expected) in enumerate(zip(rows, order.positions), 1):
        observed = row.get('observed', {})
        if type(row.get('position')) is not int or row['position'] != index or normalized_label(observed.get('window_type_label', '')) != normalized_label(expected.window_type):
            raise ValueError(f'POSITION_{index}_TYPE_READBACK_MISMATCH')
        for field in ('quantity', 'width_mm', 'height_mm'):
            if type(observed.get(field)) is not int or observed[field] != getattr(expected.dimensions, field):
                raise ValueError(f'POSITION_{index}_{field.upper()}_READBACK_MISMATCH')
    for field in ('color', 'glazing'):
        requested = getattr(order, field)
        actual = report.get('shared_options', {}).get(field, {})
        if requested is None:
            if actual.get('status') != 'not_requested':
                raise ValueError(f'{field.upper()}_DEFAULT_IS_NOT_A_REQUIREMENT')
        elif (actual.get('status') != 'verified' or actual.get('scope') != 'whole_form'
                or normalized_label(actual.get('observed_label', '')) != normalized_label(requested)):
            raise ValueError(f'{field.upper()}_READBACK_MISMATCH')


def check_expected_blocks():
    base = read_offer_specification(DEFAULT_SPECIFICATION)
    results = []
    for name, field, value in (
        ('precise_glazing', 'glazing_panes', 3),
        ('electric_strike', 'requirements', ['Elektrozaczep tylko w pozycji 2']),
        ('unsupported_opening', 'opening', 'DKR'),
    ):
        spec = deepcopy(base)
        p = spec['positions'][1]
        p[field] = value
        if field in p['field_status']:
            p['field_status'][field] = 'reported'
        result = prepare_pagen_specification(spec)
        if (result['status'] != 'review' or result['order'] is not None
                or not any(issue['position_id'] == '2' for issue in result['issues'])):
            raise ValueError('UNSUPPORTED_REQUIREMENT_NOT_BLOCKED_' + name)
        results.append(dict(case=name, status='blocked_as_expected', position_id='2'))
    return results


def execute_browser(order, directory, *, headed, keep_open):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        try:
            context = browser.new_context(locale='pl-PL', service_workers='block')
            page = context.new_page()
            try:
                report = fill_pagen_order(page, order)
                verify_readback(report, order)
                page.screenshot(path=str(directory / 'form.jpg'), full_page=True, type='jpeg')
                write_json(directory / 'form-readback.json', report)
                verify_readback(json.loads((directory / 'form-readback.json').read_text(encoding='utf-8')), order)
                return report
            except Exception as problem:
                write_json(directory / 'browser-error.json', dict(error_type=type(problem).__name__, message=str(problem)[:2000]))
                print('BROWSER_STEP=review ' + str(problem)[:1000], flush=True)
                raise
            finally:
                if keep_open:
                    input('Inspect Chromium. Press Enter to close the test window: ')
        finally:
            browser.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--specification-file', type=Path, default=DEFAULT_SPECIFICATION)
    parser.add_argument('--output-directory', type=Path, default=ROOT / '.artifacts/offer-lab')
    parser.add_argument('--execute-live', action='store_true')
    parser.add_argument('--headed', action='store_true')
    parser.add_argument('--keep-open', action='store_true')
    args = parser.parse_args(argv)
    if args.keep_open and not (args.execute_live and args.headed):
        parser.error('--keep-open requires --execute-live --headed')

    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:10]
    directory = args.output_directory.resolve() / run_id
    try:
        directory.mkdir(parents=True, exist_ok=False)
    except OSError as problem:
        print('WINDOW_OFFER_LAB=report_directory_error ' + type(problem).__name__)
        return 2
    summary = dict(run_id=run_id, status='running', live_requested=args.execute_live, browser_attempted=False,
                   python_version=platform.python_version(), platform=platform.system(),
                   submitted=False, wh_offer_created=False, sales_review_required=True)
    write_json(directory / 'result.json', summary)
    result_code = 2
    try:
        summary['expected_blocks'] = check_expected_blocks()
        spec = read_offer_specification(args.specification_file)
        write_json(directory / 'specification.json', spec)
        reloaded = read_offer_specification(directory / 'specification.json')
        if reloaded != spec:
            raise ValueError('SPECIFICATION_FILE_ROUNDTRIP_MISMATCH')
        summary['specification_file_sha256'] = hashlib.sha256((directory / 'specification.json').read_bytes()).hexdigest()
        plan = prepare_pagen_specification(reloaded)
        write_json(directory / 'compatibility.json', plan)
        summary.update(source_positions=plan['source_positions'], source_sha256=plan['source_sha256'],
                       specification_sha256=plan['specification_sha256'])
        if plan['status'] != 'ready_for_form':
            summary.update(status='review', issues=plan['issues'])
            result_code = 6
        else:
            order = PagenOrder.from_dict(plan['order'])
            write_json(directory / 'prepared-order.json', order.to_dict())
            summary.update(status='offline_passed')
            if args.execute_live:
                summary['browser_attempted'] = True
                summary['status'] = 'browser_in_progress'
                write_json(directory / 'result.json', summary)
                readback = execute_browser(order, directory, headed=args.headed, keep_open=args.keep_open)
                verify_readback(readback, order)
                summary.update(status='form_verified', observed_positions=len(readback['positions']),
                               screenshot='form.jpg', readback='form-readback.json')
            result_code = 0
    except (Exception, KeyboardInterrupt) as problem:
        # This diagnostic stays on the user's own computer. The latest summary
        # always says review; a prior report is in a different run directory.
        summary.update(status='review', error_type=type(problem).__name__,
                       message=str(problem)[:2000])
        result_code = 130 if isinstance(problem, KeyboardInterrupt) else 6
    finally:
        summary['finished_at'] = datetime.now(timezone.utc).isoformat()
        write_json(directory / 'result.json', summary)
    print('WINDOW_OFFER_LAB=' + summary['status'])
    print('LIVE_FORM=' + ('verified' if summary['status'] == 'form_verified' else 'not_verified'))
    print('REPORT_DIRECTORY=' + str(directory))
    print('SUBMITTED=False WH_OFFER_CREATED=False')
    if summary.get('issues'):
        for issue in summary['issues']:
            print(f"REVIEW_POSITION={issue['position_id']} FIELD={issue['field']} {issue['message']}")
    if summary.get('message'):
        print('REVIEW_REASON=' + summary['message'])
    return result_code


if __name__ == '__main__':
    raise SystemExit(main())
