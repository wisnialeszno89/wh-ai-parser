from app.parsers.text_offer_parser import (
    parse_offer_text
)

from app.services.construction_matcher import (
    match_construction
)

from app.wh.template_resolver import (
    resolve_template
)


sample_text = """

Okno DKL/DKR
2090 x 1440
VEKA Softline 82
Ug=0.5

"""


schema = parse_offer_text(
    sample_text
)

match = match_construction(
    schema
)

construction = match[
    "construction"
]

template_path = resolve_template(
    construction["id"]
)

print()

print("========== MATCH ==========")
print()

print(construction["id"])

print()

print("========== TEMPLATE ==========")
print()

print(template_path)