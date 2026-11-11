import io
import json
from pathlib import Path

import pytest

from tools.run_navimind_desktop_bridge import TableExecutor, handler_for, render_table, validate_task

ROWS = [
    {'label': 'Okno DKR', 'width_mm': 1000, 'height_mm': 1000, 'quantity': 2},
    {'label': 'Okno dwuskrzydłowe', 'width_mm': 1500, 'height_mm': 1400, 'quantity': 1},
]


class Writer:
    def __init__(self):
        self.calls = 0

    def save(self, path, text, previous, trace):
        self.calls += 1
        if previous is not None:
            assert path.read_text(encoding='utf-8') == previous
        path.write_text(text, encoding='utf-8')


def job(kind='create_window_table', job_id='test-job-12345678', **kwargs):
    task = {'kind': kind, 'folder': 'Oferta Top Trans', 'rows': ROWS} if kind == 'create_window_table' else {'kind': kind, 'row_number': 1, 'width_mm': 1100}
    return {'id': job_id, 'task': task, 'expectedRevision': kwargs.get('revision')}


def test_create_then_correct_changes_only_requested_width_and_reads_back(tmp_path):
    writer = Writer()
    executor = TableExecutor(tmp_path, writer)
    first = executor.execute(job())
    assert first['status'] == 'verified'
    correction = job('update_window_width', 'correction-12345678', revision=first['revision'])
    result = executor.execute(correction)
    assert result['status'] == 'verified'
    assert result['rows'][0] == {**ROWS[0], 'width_mm': 1100}
    assert result['rows'][1] == ROWS[1]
    assert Path(result['file']).read_text(encoding='utf-8') == render_table(result['rows'])
    assert executor.execute(correction) == result
    assert writer.calls == 2  # lost-response retries cannot apply a second change


def test_stale_revision_and_external_changes_cannot_be_overwritten(tmp_path):
    executor = TableExecutor(tmp_path, Writer())
    first = executor.execute(job())
    assert executor.execute(job('update_window_width', 'stale-job-1234567', revision='a' * 64))['status'] == 'review'
    path = Path(first['file'])
    path.write_text('ręcznie poprawiona oferta', encoding='utf-8')
    assert executor.execute(job('update_window_width', 'external-job-1234', revision=first['revision']))['status'] == 'review'
    assert path.read_text(encoding='utf-8') == 'ręcznie poprawiona oferta'
    assert executor.status()['currentTable'] is None
    assert executor.status()['warning']
    assert executor.status()['status'] == 'ready'


def test_create_never_overwrites_and_unknown_tasks_are_refused(tmp_path):
    executor = TableExecutor(tmp_path, Writer())
    executor.execute(job())
    assert executor.execute(job(job_id='another-job-12345'))['status'] == 'review'
    with pytest.raises(ValueError):
        executor.execute({'id': 'unsupported-123456', 'task': {'kind': 'shell', 'command': 'anything'}, 'expectedRevision': None})


@pytest.mark.parametrize('name', ['../outside', 'folder/file', 'C:\\outside', 'CON', 'NUL.txt', '..', 'test.', 'test\nname'])
def test_path_traversal_and_device_names_are_rejected(name):
    task = job()['task'].copy()
    task['folder'] = name
    with pytest.raises(ValueError):
        validate_task(task)


def test_false_verification_from_writer_is_detected(tmp_path):
    class Broken:
        def save(self, path, text, previous, trace):
            path.write_text('incomplete', encoding='utf-8')
    executor = TableExecutor(tmp_path, Broken())
    result = executor.execute(job())
    assert result['status'] == 'review'
    assert executor.active is None


def test_id_cannot_be_reused_for_different_task(tmp_path):
    executor = TableExecutor(tmp_path, Writer())
    executor.execute(job())
    changed = job()
    changed['task'] = {**changed['task'], 'folder': 'Other'}
    assert executor.execute(changed)['status'] == 'review'
    assert executor.execute(job())['status'] == 'verified'
    assert not (tmp_path / 'Other').exists()


class FakeSocket:
    def __init__(self, request):
        self.input = io.BytesIO(request)
        self.output = io.BytesIO()
    def makefile(self, *_args, **_kwargs):
        return self.input
    def sendall(self, data):
        self.output.write(data)
    def settimeout(self, _):
        pass


def request(executor, method='GET', path='/status', origin='https://www.navimind.app', token='paired-token', body=None, host='127.0.0.1:43127', extra=''):
    payload = json.dumps(body).encode() if body is not None else b''
    raw = f'{method} {path} HTTP/1.1\r\nHost: {host}\r\nOrigin: {origin}\r\nAuthorization: Bearer {token}\r\nContent-Type: application/json\r\nContent-Length: {len(payload)}\r\n{extra}\r\n'.encode() + payload
    socket = FakeSocket(raw)
    handler_for(executor, 'paired-token')(socket, ('127.0.0.1', 9000), object())
    return socket.output.getvalue().decode()


def test_http_pairing_cors_host_and_result_recovery(tmp_path):
    executor = TableExecutor(tmp_path, Writer())
    assert '200 OK' in request(executor)
    for kwargs in [{'origin': 'https://evil.example'}, {'token': 'wrong'}, {'host': 'evil.example:43127'}, {'origin': 'null'}]:
        assert '403 Forbidden' in request(executor, **kwargs)
    response = request(executor, method='POST', path='/execute', body=job())
    assert '200 OK' in response and '"status": "verified"' in response
    recovered = request(executor, path='/result/test-job-12345678')
    assert '200 OK' in recovered and '"status": "verified"' in recovered
    assert '404 Not Found' in request(executor, path='/result/unknown-job-12345')
    assert '204 No Content' in request(executor, method='OPTIONS', extra='Access-Control-Request-Method: POST\r\nAccess-Control-Request-Headers: authorization,content-type\r\n')
    assert '403 Forbidden' in request(executor, method='OPTIONS', origin='https://evil.example', extra='Access-Control-Request-Method: POST\r\n')


def task_job(task, rev=None, suffix='1234567890123456'):
    return {'id': 'task-' + suffix, 'task': task, 'expectedRevision': rev}


def test_append_and_multi_field_edit_preserve_all_undeclared_data(tmp_path):
    writer = Writer()
    executor = TableExecutor(tmp_path, writer)
    first = executor.execute(job())
    extra = {'label': 'Okno dwuskrzydłowe', 'width_mm': 1500, 'height_mm': 1300, 'quantity': 2}
    body = task_job({'kind': 'append_window_rows', 'rows': [extra]}, first['revision'])
    added = executor.execute(body)
    assert added['status'] == 'verified'
    assert added['rows'] == ROWS + [extra]
    assert executor.execute(body) == added
    assert writer.calls == 2
    corrected = executor.execute(task_job({'kind': 'edit_window_rows', 'changes': [
        {'row_number': 1, 'fields': {'height_mm': 1200, 'quantity': 3}},
        {'row_number': 3, 'fields': {'label': 'Okno DKL', 'width_mm': 1600}},
    ]}, added['revision'], 'edit-123456789012'))
    assert corrected['status'] == 'verified'
    assert corrected['rows'] == [
        {**ROWS[0], 'height_mm': 1200, 'quantity': 3}, ROWS[1],
        {**extra, 'label': 'Okno DKL', 'width_mm': 1600},
    ]
    assert Path(corrected['file']).read_text(encoding='utf-8') == render_table(corrected['rows'])


def test_separate_variants_and_copy_keep_source_byte_for_byte(tmp_path):
    executor = TableExecutor(tmp_path, Writer())
    original = executor.execute(job())
    original_path = Path(original['file'])
    original_bytes = original_path.read_bytes()
    variants = [{**ROWS[0], 'label': f'Wariant testowy {i}', 'width_mm': 1000 + i * 50} for i in range(10)]
    created = executor.execute(task_job({'kind': 'create_window_table', 'folder': 'Oferta Top Trans', 'file_name': 'warianty-okien.txt', 'rows': variants}))
    assert created['status'] == 'verified'
    assert len(created['rows']) == 10
    assert original_path.read_bytes() == original_bytes
    copied = executor.execute(task_job({'kind': 'copy_window_table', 'folder': 'Oferta Top Trans', 'file_name': 'kopia-wariantow.txt'}, created['revision'], 'copy-123456789012'))
    assert copied['status'] == 'verified'
    assert Path(copied['file']).read_bytes() == Path(created['file']).read_bytes()
    assert original_path.read_bytes() == original_bytes


def test_restart_restores_active_and_open_switches_to_original_without_writing(tmp_path):
    class OpeningWriter(Writer):
        def open(self, path, text, trace):
            assert path.read_text(encoding='utf-8') == text
    writer = OpeningWriter()
    executor = TableExecutor(tmp_path, writer)
    first = executor.execute(job())
    executor.execute(task_job({'kind': 'create_window_table', 'folder': 'Oferta Top Trans', 'file_name': 'inne.txt', 'rows': [ROWS[0]]}))
    restarted = TableExecutor(tmp_path, writer)
    assert restarted.current()['file_name'] == 'inne.txt'
    before = Path(first['file']).read_bytes()
    calls = writer.calls
    opened = restarted.execute(task_job({'kind': 'open_window_table', 'folder': 'Oferta Top Trans', 'file_name': 'tabela-okien.txt'}, first['revision'], 'open-123456789012'))
    assert opened['status'] == 'verified'
    assert writer.calls == calls
    assert Path(first['file']).read_bytes() == before
    assert restarted.current()['rows'] == ROWS
    added = restarted.execute(task_job({'kind': 'append_window_rows', 'rows': [ROWS[0]]}, opened['revision'], 'again-12345678901'))
    assert added['status'] == 'verified'
    assert added['rows'] == ROWS + [ROWS[0]]


def test_v1_table_is_adopted_after_upgrade_and_ambiguous_tables_require_selection(tmp_path):
    folder = tmp_path / 'Oferta Top Trans'
    folder.mkdir()
    (folder / 'tabela-okien.txt').write_text(render_table(ROWS), encoding='utf-8')
    executor = TableExecutor(tmp_path, Writer())
    assert executor.current()['rows'] == ROWS
    (folder / 'inne.txt').write_text(render_table(ROWS), encoding='utf-8')
    executor = TableExecutor(tmp_path, Writer())
    assert executor.current() is None
    assert len(executor.status()['tables']) == 2


def test_invalid_patch_and_overflow_never_change_saved_file(tmp_path):
    executor = TableExecutor(tmp_path, Writer())
    first = executor.execute(job())
    before = Path(first['file']).read_bytes()
    for changes in [
        [{'row_number': 1, 'fields': {'quantity': True}}],
        [{'row_number': 1, 'fields': {'unknown': 'value'}}],
        [{'row_number': 1, 'fields': {'quantity': 3}}, {'row_number': 1, 'fields': {'width_mm': 1200}}],
    ]:
        with pytest.raises(ValueError):
            executor.execute(task_job({'kind': 'edit_window_rows', 'changes': changes}, first['revision']))
    overflow = executor.execute(task_job({'kind': 'append_window_rows', 'rows': [ROWS[0]] * 49}, first['revision']))
    assert overflow['status'] == 'review'
    assert Path(first['file']).read_bytes() == before


def test_catalog_does_not_adopt_arbitrary_text_or_symlinked_folders(tmp_path):
    folder = tmp_path / 'Offer'
    folder.mkdir()
    (folder / 'notes.txt').write_text('not a window table', encoding='utf-8')
    outside = tmp_path.parent / (tmp_path.name + '-outside')
    outside.mkdir()
    (outside / 'table.txt').write_text(render_table(ROWS), encoding='utf-8')
    (tmp_path / 'link').symlink_to(outside, target_is_directory=True)
    executor = TableExecutor(tmp_path, Writer())
    assert executor.catalog() == []
    with pytest.raises(ValueError):
        executor.safe_path('link', 'table.txt')
    for name in ['../outside.txt', 'other.exe', 'NUL.txt']:
        with pytest.raises(ValueError):
            validate_task({'kind': 'create_window_table', 'folder': 'Offer', 'file_name': name, 'rows': ROWS})
