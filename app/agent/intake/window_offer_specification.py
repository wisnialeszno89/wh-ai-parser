"""Shared, versioned boundary between NaviMind readings and local offer tools."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator

from app.agent.offers.catalog_control_binding import normalized_label
from app.agent.offers.pagen_configurator import PagenOrder

CONTRACTS = Path(__file__).resolve().parents[3] / 'contracts'
SCHEMA = json.loads((CONTRACTS / 'window-offer-v1.schema.json').read_text(encoding='utf-8'))
VALIDATOR = Draft202012Validator(SCHEMA)
SCHEMA_V2 = json.loads((CONTRACTS / 'window-offer-v2.schema.json').read_text(encoding='utf-8'))
VALIDATOR_V2 = Draft202012Validator(SCHEMA_V2)
FIELDS = tuple(SCHEMA['properties']['positions']['items']['properties']['field_status']['properties'])


def validate_offer_specification(value):
    version = value.get('schema_version') if isinstance(value, dict) else None
    validator = {'window-offer/1': VALIDATOR, 'window-offer/2': VALIDATOR_V2}.get(version) if isinstance(version, str) else None
    if validator is None or not validator.is_valid(value):
        raise ValueError('INVALID_OFFER_SPECIFICATION')
    spec = deepcopy(value)
    ids = {p['id'] for p in spec['positions']}
    if len(ids) != len(spec['positions']):
        raise ValueError('DUPLICATE_OFFER_POSITION')
    pdf, pages = spec['source']['kind'] == 'pdf', spec['source']['pages']
    if (pdf and pages is None) or (not pdf and pages is not None):
        raise ValueError('INVALID_OFFER_SOURCE')
    for p in spec['positions']:
        if any(isinstance(p[field], float) and not math.isfinite(p[field]) for field in FIELDS):
            raise ValueError('INVALID_SPECIFICATION_NUMBER')
        page_numbers = [p['source_page'], *[e['page'] for e in p['evidence']]]
        if (pdf and any(n is None or n > pages for n in page_numbers)) or (
                not pdf and any(n is not None for n in page_numbers)):
            raise ValueError('INVALID_OFFER_SOURCE')
        for field in FIELDS:
            state = p['field_status'][field]
            if (p[field] is None) != (state == 'missing'):
                raise ValueError('INVALID_OFFER_FIELD_STATUS')
            if state == 'corrected' and not any(c['position_id'] == p['id'] and
                    c['field'] == field and c['value'] == p[field] for c in spec['corrections']):
                raise ValueError('INVALID_OFFER_CORRECTION')
    if any(i['position_id'] is not None and i['position_id'] not in ids for i in spec['audit_issues']):
        raise ValueError('UNKNOWN_OFFER_POSITION')
    for c in spec['corrections']:
        p = next((p for p in spec['positions'] if p['id'] == c['position_id']), None)
        if not p or p['source_id'] != c['source_id'] or p[c['field']] != c['value']:
            raise ValueError('INVALID_OFFER_CORRECTION')
    unresolved = not spec['positions'] or spec['audit_issues'] or any(
        p['ambiguities'] or any(p[k] is None for k in ('quantity', 'width_mm', 'height_mm'))
        or 'conflict' in p['field_status'].values() for p in spec['positions'])
    if unresolved and not spec['requires_clarification']:
        raise ValueError('UNRESOLVED_OFFER_SPECIFICATION')
    return spec


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_SPECIFICATION_KEY')
        result[key] = value
    return result


def read_offer_specification(path: Path):
    if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('SPECIFICATION_FILE_MISSING_OR_TOO_LARGE')
    def invalid_constant(_):
        raise ValueError('INVALID_SPECIFICATION_NUMBER')
    return validate_offer_specification(json.loads(path.read_text(encoding='utf-8-sig'),
        object_pairs_hook=_unique_object, parse_constant=invalid_constant))


def prepare_pagen_specification(value):
    """Compile only losslessly supported fields; never execute, price or submit."""
    spec = validate_offer_specification(value)
    issues, rows, colors = [], [], []
    def issue(position, field, message):
        issues.append(dict(position_id=position, field=field, message=message))
    if spec['requires_clarification']:
        issue(None, 'source', 'Najpierw wyjaśnij rozbieżności i braki odczytu źródła.')
    if spec['notes']:
        issue(None, 'notes', 'Uwagi ogólne wymagają rozpatrzenia; adapter nie może pominąć ich przy konfiguracji.')
    if not 1 <= len(spec['positions']) <= 10:
        issue(None, 'positions', 'Adapter PAGEN obsługuje od 1 do 10 pozycji.')
    profiles = []
    white = {'white', 'weiß', 'weiss', 'biały', 'bialy'}
    for p in spec['positions']:
        pid = p['id']
        if p['kind'] != 'window':
            issue(pid, 'kind', 'Ten most obsługuje obecnie wyłącznie okna stałe FIX.')
        if p['opening'] != 'FIX':
            issue(pid, 'opening', 'Formularz nie potwierdza typu okucia i stron skrzydeł tej pozycji.')
        if not p['profile_reference']:
            issue(pid, 'profile_reference', 'Podaj dokładny profil; odniesienie do marki nie potwierdza zamiennika.')
        else:
            profiles.append(p['profile_reference'])
        for field in ('transport_extension_mm', 'glazing_panes', 'ug'):
            if p[field] is not None:
                issue(pid, field, 'Formularz nie potwierdza tego szczegółowego wymagania; nie pominięto go.')
        if p['requirements']:
            issue(pid, 'requirements', 'Dodatkowe wymagania nie mają jeszcze zweryfikowanej kontrolki w tym adapterze.')
        pair = [p['color_inside'], p['color_outside']]
        if pair == [None, None]:
            colors.append(None)
        elif all(isinstance(v, str) and normalized_label(v) in white for v in pair):
            colors.append('Biały dwustronny')
        else:
            issue(pid, 'color', 'Ten most nie potwierdza dokładnych kolorów po obu stronach; nie wybierze podobnej opcji.')
        if any(state == 'conflict' for state in p['field_status'].values()):
            issue(pid, 'source', 'Pola tej pozycji mają nierozstrzygniętą rozbieżność.')
        if any(p[k] is None for k in ('quantity', 'width_mm', 'height_mm')):
            issue(pid, 'dimensions', 'Uzupełnij ilość i oba wymiary produktu w mm.')
        rows.append(dict(window_type='Okno stałe', **{k:p[k] for k in ('quantity','width_mm','height_mm')}))
    if len({normalized_label(p) for p in profiles}) > 1:
        issue(None, 'profile_reference', 'PAGEN ma wspólny profil: różne profile wymagają osobnego przebiegu.')
    if len(set(colors)) > 1:
        issue(None, 'color', 'Wspólny kolor nie może rozszerzyć wymagania jednej pozycji na inne.')
    order = None
    if not issues:
        try:
            order = PagenOrder.from_dict(dict(profile=profiles[0], positions=rows,
                **({'color':colors[0]} if colors[0] is not None else {}))).to_dict()
        except ValueError:
            issue(None, 'dimensions', 'Wymiary lub ilości nie mieszczą się w ograniczeniach wykonawcy.')
    digest = hashlib.sha256(json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return dict(status='review' if issues else 'ready_for_form', target='pagen',
                source_sha256=spec['source']['sha256'], specification_sha256=digest,
                source_positions=[p['id'] for p in spec['positions']], issues=issues, order=order,
                submitted=False, wh_offer_created=False, sales_review_required=True,
                scope='form_prefill_only')
