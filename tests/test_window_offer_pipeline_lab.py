from copy import deepcopy
import json

import pytest

from tools import check_window_offer_pipeline as lab
from app.agent.intake.window_offer_specification import read_offer_specification, prepare_pagen_specification
from app.agent.offers.pagen_configurator import PagenOrder


def example_order():
    spec=read_offer_specification(lab.DEFAULT_SPECIFICATION)
    return PagenOrder.from_dict(prepare_pagen_specification(spec)['order'])


def observed(order):
    return dict(status='form_verified', evidence='browser_dom_readback',
        submitted=False, wh_offer_created=False, sales_review_required=True,
        profile=dict(observed_label=order.profile,observed_value='profile-1'),
        positions=[dict(position=i,observed=dict(window_type_label=p.window_type,
            **{field:getattr(p.dimensions,field) for field in ('quantity','width_mm','height_mm')}))
            for i,p in enumerate(order.positions,1)],
        shared_options={field:dict(status='not_requested',scope='whole_form') if getattr(order,field) is None
            else dict(status='verified',scope='whole_form',observed_label=getattr(order,field))
            for field in ('color','glazing')})


def result_files(root):
    return sorted(root.glob('*/result.json'))


def test_offline_pipeline_checks_two_positions_and_expected_blocks_without_a_browser(tmp_path,monkeypatch,capsys):
    monkeypatch.setattr(lab,'execute_browser',lambda *a,**k:pytest.fail('offline launched a browser'))
    assert lab.main(['--output-directory',str(tmp_path)])==0
    result=json.loads(result_files(tmp_path)[0].read_text())
    assert result['status']=='offline_passed' and not result['browser_attempted']
    assert result['source_positions']==['1','2'] and len(result['expected_blocks'])==3
    assert all(c['status']=='blocked_as_expected' for c in result['expected_blocks'])
    folder=result_files(tmp_path)[0].parent
    assert read_offer_specification(folder/'specification.json')['positions'][1]['width_mm']==1100
    assert (folder/'prepared-order.json').is_file()
    assert not (folder/'form-readback.json').exists()
    assert 'LIVE_FORM=not_verified' in capsys.readouterr().out


def test_unsupported_customer_specification_does_not_start_browser_even_with_live_switch(tmp_path,monkeypatch):
    spec=read_offer_specification(lab.DEFAULT_SPECIFICATION)
    spec['positions'][1]['requirements']=['Naświetle 300 mm']
    source=tmp_path/'source.json';source.write_text(json.dumps(spec),encoding='utf-8')
    monkeypatch.setattr(lab,'execute_browser',lambda *a,**k:pytest.fail('unsupported order launched a browser'))
    output=tmp_path/'runs'
    assert lab.main(['--specification-file',str(source),'--output-directory',str(output),'--execute-live'])==6
    result=json.loads(result_files(output)[0].read_text())
    assert result['status']=='review' and not result['browser_attempted']
    assert any(i['position_id']=='2' and i['field']=='requirements' for i in result['issues'])


@pytest.mark.parametrize('change',[
    lambda r:r['positions'].pop(),
    lambda r:r['positions'][0]['observed'].update(width_mm=999),
    lambda r:r['positions'][0]['observed'].update(quantity=True),
    lambda r:r['positions'][1]['observed'].update(height_mm=1478),
    lambda r:r['positions'][0].update(position=True),
    lambda r:r['profile'].update(observed_label='Different profile'),
    lambda r:r['shared_options']['color'].update(observed_label='Duokolor'),
    lambda r:r['shared_options']['glazing'].update(status='verified'),
    lambda r:r.update(submitted=True),
    lambda r:r.update(sales_review_required=False),
])
def test_a_success_word_does_not_hide_lost_rows_reset_values_or_unrequested_defaults(change):
    order=example_order();report=observed(order);change(report)
    with pytest.raises(ValueError):lab.verify_readback(report,order)


def test_a_previous_success_cannot_be_reused_after_a_new_failure(tmp_path,monkeypatch):
    def success(order,directory,**kwargs):
        report=observed(order)
        lab.write_json(directory/'form-readback.json',report)
        return report
    monkeypatch.setattr(lab,'execute_browser',success)
    assert lab.main(['--output-directory',str(tmp_path),'--execute-live'])==0
    first=result_files(tmp_path)[0]
    first_contents=first.read_bytes()
    def failure(*args,**kwargs):raise RuntimeError('Simulated reset while adding row')
    monkeypatch.setattr(lab,'execute_browser',failure)
    assert lab.main(['--output-directory',str(tmp_path),'--execute-live'])==6
    results=[json.loads(p.read_text()) for p in result_files(tmp_path)]
    assert sorted(r['status'] for r in results)==['form_verified','review']
    assert len({r['run_id'] for r in results})==2 and first.read_bytes()==first_contents


def test_mismatched_live_readback_never_becomes_a_successful_run(tmp_path,monkeypatch):
    report=observed(example_order());report['positions'][1]['observed']['quantity']=2
    monkeypatch.setattr(lab,'execute_browser',lambda *a,**k:deepcopy(report))
    assert lab.main(['--output-directory',str(tmp_path),'--execute-live'])==6
    result=json.loads(result_files(tmp_path)[0].read_text())
    assert result['status']=='review' and 'QUANTITY_READBACK_MISMATCH' in result['message']
