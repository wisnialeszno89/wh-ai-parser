from copy import deepcopy
import json

import pytest

from app.agent.intake.window_offer_specification import (
    CONTRACTS, read_offer_specification, validate_offer_specification, prepare_pagen_specification,
)
from tools.run_pagen_order import main


def example():
    return json.loads((CONTRACTS / 'window-offer-v1.example.json').read_text(encoding='utf-8'))


def test_shared_export_prepares_an_order_without_losing_position_identity():
    spec = example()
    before = deepcopy(spec)
    result = prepare_pagen_specification(spec)
    assert result['status'] == 'ready_for_form'
    assert result['source_sha256'] == spec['source']['sha256']
    assert result['source_positions'] == ['1']
    assert result['order']['positions'] == [dict(window_type='Okno stałe', quantity=2, width_mm=1230, height_mm=1478)]
    assert result['order']['color'] == 'Biały dwustronny'
    assert result['sales_review_required'] and not result['submitted'] and not result['wh_offer_created']
    assert spec == before


@pytest.mark.parametrize('field,value', [('kind','entrance_door'),('opening','DKR'),
    ('requirements',['Elektrozaczep tylko w tych drzwiach']),('glazing_panes',3),
    ('ug',0.6),('transport_extension_mm',30),('color_outside','anthracite')])
def test_unsupported_requirements_stop_before_any_browser_action(field, value):
    spec=example();p=spec['positions'][0];p[field]=value
    if field in p['field_status']:
        p['field_status'][field]='reported'
    result=prepare_pagen_specification(spec)
    assert result['status']=='review' and result['order'] is None
    assert any(i['position_id']=='1' for i in result['issues'])


def test_one_incompatible_position_blocks_the_whole_order_instead_of_disappearing():
    spec=example();second=deepcopy(spec['positions'][0]);second.update(id='2',source_id='2',opening='DKL');spec['positions'].append(second)
    result=prepare_pagen_specification(spec)
    assert result['source_positions']==['1','2'] and result['order'] is None
    assert any(i['position_id']=='2' and i['field']=='opening' for i in result['issues'])


def test_shared_settings_do_not_propagate_to_unspecified_positions():
    spec=example();second=deepcopy(spec['positions'][0]);second.update(id='2',source_id='2',color_inside=None,color_outside=None)
    second['field_status'].update(color_inside='missing',color_outside='missing');spec['positions'].append(second)
    assert any(i['field']=='color' for i in prepare_pagen_specification(spec)['issues'])


@pytest.mark.parametrize('mutation',[
    lambda s:s.update(executed=True),
    lambda s:s['positions'].append(s['positions'][0]),
    lambda s:s['positions'][0].update(width_mm=None),
    lambda s:s['positions'][0]['field_status'].update(width_mm='corrected'),
    lambda s:s['positions'][0].update(unexpected='cannot be dropped'),
    lambda s:s['source'].update(pages=2),
    lambda s:s['positions'][0]['field_status'].update(opening='conflict'),
])
def test_invalid_or_falsely_ready_export_is_rejected(mutation):
    spec=example();mutation(spec)
    with pytest.raises(ValueError):validate_offer_specification(spec)


def test_corrected_dimension_must_match_the_target_and_preserve_its_prior_value():
    spec=example();spec['positions'][0]['width_mm']=1240;spec['positions'][0]['field_status']['width_mm']='corrected'
    correction=dict(position_id='1',source_id='1',field='width_mm',before=1230,value=1240,quote='W pozycji 1 szerokość 1240 mm')
    spec['corrections']=[correction]
    assert validate_offer_specification(spec)['corrections'][0]['before']==1230
    correction['position_id']='99'
    with pytest.raises(ValueError):validate_offer_specification(spec)


def test_cli_reads_shared_specification_directly_and_blocks_lossy_overrides(tmp_path,capsys):
    file=tmp_path/'specification.json';file.write_text(json.dumps(example()),encoding='utf-8')
    assert main(['--specification-file',str(file)])==0
    assert 'PAGEN_SPECIFICATION=prepared' in capsys.readouterr().out
    with pytest.raises(SystemExit):main(['--specification-file',str(file),'--glazing','Standardowa'])
    spec=example();spec['positions'][0]['requirements']=['Naświetle 300 mm'];file.write_text(json.dumps(spec),encoding='utf-8')
    assert main(['--specification-file',str(file),'--execute-live'])==6
    assert 'specification_review' in capsys.readouterr().out


def test_duplicate_json_keys_cannot_hide_a_requirement(tmp_path):
    file=tmp_path/'duplicated.json';file.write_text('{"executed":true,"executed":false}',encoding='utf-8')
    with pytest.raises(ValueError,match='DUPLICATE_SPECIFICATION_KEY'):read_offer_specification(file)


def test_v2_commercial_fields_are_validated_without_losing_source_and_v1_stays_readable():
    spec=json.loads((CONTRACTS/'window-offer-v2.example.json').read_text(encoding='utf-8'))
    assert validate_offer_specification(spec)==spec
    assert validate_offer_specification(example())['schema_version']=='window-offer/1'
    result=prepare_pagen_specification(spec)
    assert result['status']=='review' and result['order'] is None
    assert any(i['field']=='opening' for i in result['issues'])
    assert any(i['field']=='color' for i in result['issues'])
    assert not result['submitted'] and not result['wh_offer_created']


def test_v2_quantity_correction_can_reach_the_existing_fixed_window_adapter():
    spec=example();spec['schema_version']='window-offer/2'
    spec['positions'][0]['quantity']=4;spec['positions'][0]['field_status']['quantity']='corrected'
    spec['corrections']=[dict(position_id='1',source_id='1',field='quantity',before=2,value=4,quote='Pozycja 1: ilość 4 szt.')]
    result=prepare_pagen_specification(spec)
    assert result['status']=='ready_for_form'
    assert result['order']['positions'][0]['quantity']==4
    assert result['source_sha256']==spec['source']['sha256']
    spec['schema_version']='window-offer/1'
    with pytest.raises(ValueError):validate_offer_specification(spec)


@pytest.mark.parametrize('mutate',[
    lambda s:s['corrections'][0].update(value='4'),
    lambda s:s['corrections'][0].update(before='two'),
    lambda s:s['corrections'][1].update(value=7016),
    lambda s:s['corrections'][2].update(value='RIGHT'),
    lambda s:s['corrections'][0].update(field='profile_reference'),
    lambda s:s.update(schema_version=[]),
])
def test_v2_rejects_wrong_field_types_and_unknown_versions(mutate):
    spec=json.loads((CONTRACTS/'window-offer-v2.example.json').read_text(encoding='utf-8'));mutate(spec)
    with pytest.raises(ValueError):validate_offer_specification(spec)
