"""Shared positive expectations must be possible in the real lab markup."""
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SelectOptions(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = None
        self.options = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'select':
            self.active = attrs.get('id')
            self.options[self.active] = set()
        elif tag == 'option' and self.active:
            self.options[self.active].add(attrs.get('value', ''))

    def handle_endtag(self, tag):
        if tag == 'select':
            self.active = None


def test_shared_fixture_expectations_exist_in_real_lab_and_preserve_other_fields():
    suite = json.loads((ROOT / 'contracts/browser-regression-v1.json').read_text(encoding='utf-8'))
    parser = SelectOptions()
    parser.feed((ROOT / 'tools/navimind_browser_lab.html').read_text(encoding='utf-8'))
    fields = {'customer', 'width', 'height', 'color', 'opening'}
    seen = set()
    for scenario in suite['scenarios']:
        previous = scenario['seed']
        for phase in scenario['phases']:
            id = scenario['id']+'/'+phase['id']
            assert id not in seen
            seen.add(id)
            assert set(phase['allowed_write_fields']) <= fields
            if phase['expected']:
                assert set(phase['expected']) == fields
                assert phase['terminal_decisions'] == ['done']
                for key in ['color', 'opening']:
                    assert phase['expected'][key] in parser.options[key], (id, key)
                if previous:
                    for key in fields-set(phase['allowed_write_fields']):
                        assert previous[key] == phase['expected'][key], (id, key)
                previous = phase['expected']
            else:
                assert 'done' not in phase['terminal_decisions']
                assert phase['probe']
    assert len(seen) == 9
