from app.parsers.semantic_offer_parser import (
    parse_offer_text
)

from app.services.construction_matcher import (
    match_construction
)


TEXT = """
FIX RU
2090x1440
antracyt
"""


schema = parse_offer_text(
    TEXT
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