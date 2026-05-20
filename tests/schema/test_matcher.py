from app.parsers.text_offer_parser import (
    parse_offer_text
)

from app.services.construction_matcher import (
    match_construction
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

result = match_construction(
    schema
)

print()

print("========== SCHEMA ==========")
print()

print(schema)

print()

print("========== MATCH ==========")
print()

print(result)