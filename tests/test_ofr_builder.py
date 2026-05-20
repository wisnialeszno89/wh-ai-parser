from app.services.ofr_builder import (
    build_ofr_offer
)


TEXT = """
FIX RU
2090x1440

RU RU
1500x1500

HST
3500x2300
"""


results = build_ofr_offer(
    TEXT
)


for item in results:

    print()
    print("==========")
    print()

    print(item)