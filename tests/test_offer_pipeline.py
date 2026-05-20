from app.services.offer_pipeline import (
    build_offer_pipeline
)


TEXT = """
FIX RU
2090x1440
antracyt

RU RU
1500x1500

HST
3500x2300
"""


results = build_offer_pipeline(
    TEXT
)


for i, item in enumerate(results):

    print()

    print("==========")

    print(f"OFFER ITEM {i+1}")

    print("==========")

    print()

    print(item)