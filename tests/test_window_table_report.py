from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from tools.window_table_report import aggregate, write_xlsx, verify_xlsx, write_preview, q
from tools.run_navimind_desktop_bridge import TableExecutor, render_table, validate_task

ROWS = [
    {'label': 'Okno DKR', 'width_mm': 1000, 'height_mm': 1000, 'quantity': 2},
    {'label': 'Okno dwuskrzydłowe', 'width_mm': 1500, 'height_mm': 1400, 'quantity': 1},
]


class Writer:
    def save(self, path, text, previous, trace):
        path.write_text(text, encoding='utf-8')
    def open_report(self, path, preview):
        assert path.is_file() and preview.is_file()
        return {'open_status': 'requested', 'opened_with': 'browser_preview'}


def source(folder, rows):
    return {'folder': folder, 'file_name': 'tabela-okien.txt', 'rows': rows}


def make_executor(tmp_path):
    for name, rows in [('A', ROWS), ('B', [{**ROWS[0], 'label': ' okno   dkr ', 'quantity': 3}])]:
        directory = tmp_path / name
        directory.mkdir()
        (directory / 'tabela-okien.txt').write_text(render_table(rows), encoding='utf-8')
    return TableExecutor(tmp_path, Writer())


def report_job(executor, job_id='report-job-123456', name='zestawienie.xlsx'):
    return {'id': job_id, 'expectedRevision': None, 'task': {
        'kind': 'aggregate_window_tables', 'sources': [{k: t[k] for k in ['folder', 'file_name', 'revision']} for t in executor.catalog()],
        'folder': 'Raporty', 'file_name': name, 'open_result': True,
    }}


def test_totals_and_repeats_preserve_quantities_and_source_order():
    entries, summary = aggregate([source('A', ROWS), source('B', [{**ROWS[0], 'label': ' okno   dkr ', 'quantity': 3}])])
    assert summary == {'files': 2, 'positions': 3, 'quantity': 6, 'area_m2': '7.1', 'duplicate_rows': 2, 'duplicate_groups': 1}
    assert [r['source'] for r in entries] == ['A/tabela-okien.txt', 'A/tabela-okien.txt', 'B/tabela-okien.txt']
    assert entries[0]['duplicate'] == entries[2]['duplicate'] == 'D1'
    assert not entries[1]['duplicate']
    assert entries[2]['quantity'] == 3


def test_workbook_readback_checks_formulas_caches_provenance_and_safe_strings(tmp_path):
    entries, summary = aggregate([source('A', [{**ROWS[0], 'label': '=HYPERLINK("bad") <script>alert(1)</script>'}])])
    path, preview = tmp_path/'report.xlsx', tmp_path/'report.html'
    write_xlsx(path, entries, summary)
    assert verify_xlsx(path, entries, summary)
    write_preview(preview, entries, summary)
    with ZipFile(path) as archive:
        cells = {node.attrib['r']: node for node in ET.fromstring(archive.read('xl/worksheets/sheet1.xml')).iter(q('c'))}
        assert cells['D8'].attrib['t'] == 'inlineStr'
        assert cells['D8'].find(q('f')) is None
        assert cells['H8'].findtext(q('f')) == 'E8*F8/1000000'
        assert cells['I8'].findtext(q('f')) == 'H8*G8'
        assert cells['K2'].findtext(q('f')) == 'SUM(I8:I8)'
    assert '<script>' not in preview.read_text()
    assert '&lt;script&gt;' in preview.read_text()


def test_runtime_aggregate_never_modifies_sources_and_has_repeatable_result(tmp_path):
    executor = make_executor(tmp_path)
    before = {path: path.read_bytes() for path in tmp_path.glob('*/*.txt')}
    body = report_job(executor)
    result = executor.execute(body)
    assert result['status'] == 'verified', result
    assert result['summary']['quantity'] == 6
    assert Decimal(result['summary']['area_m2']) == Decimal('7.1')
    assert result['opened_with'] == 'browser_preview'
    assert Path(result['file']).suffix == '.xlsx'
    assert Path(result['preview']).suffix == '.html'
    assert all(path.read_bytes() == data for path, data in before.items())
    assert executor.execute(body) == result
    assert executor.reports() == [{'folder': 'Raporty', 'file_name': 'zestawienie.xlsx'}]
    assert executor.current() is None  # report does not silently select an input for later edits


def test_stale_source_and_existing_output_stop_without_overwriting(tmp_path):
    executor = make_executor(tmp_path)
    body = report_job(executor)
    first = executor.execute(body)
    assert first['status'] == 'verified'
    original = Path(first['file']).read_bytes()
    duplicate = report_job(executor, 'report-again-12345')
    assert executor.execute(duplicate)['status'] == 'review'
    assert Path(first['file']).read_bytes() == original
    stale = report_job(executor, 'stale-report-12345', 'nowy.xlsx')
    changed = tmp_path/'A'/'tabela-okien.txt'
    changed.write_text(render_table([{**ROWS[0], 'quantity': 8}]), encoding='utf-8')
    assert executor.execute(stale)['status'] == 'review'
    assert not (tmp_path/'Raporty'/'nowy.xlsx').exists()


def test_duplicate_refs_paths_and_unsupported_exports_are_rejected(tmp_path):
    executor = make_executor(tmp_path)
    body = report_job(executor)
    body['task']['sources'].append(body['task']['sources'][0])
    with pytest.raises(ValueError): validate_task(body['task'])
    for filename in ['../outside.xlsx', 'report.exe']:
        task = report_job(executor)['task']
        task['file_name'] = filename
        with pytest.raises(ValueError): validate_task(task)


def test_no_open_request_does_not_launch_a_program(tmp_path):
    executor = make_executor(tmp_path)
    body = report_job(executor)
    body['task']['open_result'] = False
    result = executor.execute(body)
    assert result['status'] == 'verified'
    assert result['open_status'] == 'not_requested'


def test_unsaved_owned_editor_stops_report_before_publication(tmp_path):
    executor = make_executor(tmp_path)
    def dirty(): raise RuntimeError('Notatnik ma niezapisane zmiany.')
    executor.writer.assert_clean = dirty
    result = executor.execute(report_job(executor))
    assert result['status'] == 'review'
    assert not list(tmp_path.glob('Raporty/*.xlsx'))
