from app.parsers.semantic_offer_parser import (
    parse_offer_text
)


TEST_CASES = [

    """
    Okno VEKA Softline 82
    1550x1435
    antracyt
    pakiet 3 szyby Ug=0.5
    roleta
    """,

    """
    HST Aluplast
    3500x2300
    bialy
    """,

    """
    Drzwi Salamander
    1100x2100
    orzech
    P4
    """,
]


for text in TEST_CASES:

    result = parse_offer_text(
        text
    )

    print()
    print("==========")
    print()

    print(result)