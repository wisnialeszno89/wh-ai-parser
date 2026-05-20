from app.parsers.semantic_offer_parser import (
    parse_multiple_constructions
)


TEXT = """
Okno VEKA Softline 82
1500x1500
antracyt
3 szyby Ug=0.5

HST Aluplast
3500x2300
bialy

Drzwi Salamander
1100x2100
orzech
P4
"""


results = parse_multiple_constructions(
    TEXT
)


for i, item in enumerate(results):

    print()

    print("==========")

    print(f"CONSTRUCTION {i+1}")

    print("==========")

    print()

    print(item)