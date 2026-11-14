"""Synthetic coverage probe of the LOCAL German-mail parser, never an LLM score.

Nonzero exit means at least one expected field was missed. No GUI or API calls.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.german_offer_mail import inspect_german_offer_mail


WINDOW = dict(product_type='window', quantity=2, width_mm=1230,
              height_mm=1478, opening='DKR')
CASES = [
    ('de_explicit', 'Fenster 2 Stk. 1230x1478 mm DKR', [WINDOW]),
    ('de_numbered', 'Pos. 1: Fenster 2 Stk. 1230x1478 mm DKR', [WINDOW]),
    ('de_prose', 'Bitte bieten Sie 2 Fenster 1230x1478 mm DKR an.', [WINDOW]),
    ('pl_explicit', 'Okno 2 szt. 1230x1478 mm prawe rozwierno-uchylne', [WINDOW]),
    ('de_cm', 'Fenster 2 Stk. 123x147.8 cm DKR', [WINDOW]),
    ('de_turn_left', 'Fenster 2 Stk. 1230x1478 mm Dreh Links',
     [{**WINDOW, 'opening': 'DL'}]),
    ('de_color', 'Fenster 2 Stk. 1230x1478 mm DKR\ninnen weiß, außen anthrazit',
     [{**WINDOW, 'color_inside': 'white', 'color_outside': 'anthracite'}]),
    ('de_mixed', 'Haustür 1 Stk. 990x2120 mm DL\nFenster 2 Stk. 1230x1478 mm DKR',
     [dict(product_type='entrance_door', quantity=1, width_mm=990,
           height_mm=2120, opening='DL'), WINDOW]),
]


def run_benchmark():
    cases = []
    for name, text, expected in CASES:
        actual = inspect_german_offer_mail(text)
        mismatches = []
        if len(actual) != len(expected):
            mismatches.append(dict(field='position_count', expected=len(expected), observed=len(actual)))
        for index, wanted in enumerate(expected):
            for field, value in wanted.items():
                observed = actual[index].get(field) if index < len(actual) else None
                if observed != value:
                    mismatches.append(dict(position=index+1, field=field, expected=value, observed=observed))
        cases.append(dict(case=name, matched=not mismatches, mismatches=mismatches))
    return dict(scope='local_german_mail_parser_only', synthetic=True,
                model_requests=0, live_actions=0,
                cases=len(cases), matched=sum(c['matched'] for c in cases),
                results=cases, complete_offer_created=False)


if __name__ == '__main__':
    report = run_benchmark()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report['matched'] == report['cases'] else 1)
