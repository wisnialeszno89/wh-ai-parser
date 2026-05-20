from app.parsers.block_splitter import (
    split_offer_blocks
)


TEXT = """Okno VEKA Softline 82
1500x1500
antracyt

HST Aluplast
3500x2300
bialy

Drzwi Salamander
1100x2100
orzech"""


print()
print("========== RAW ==========")
print()

print(repr(TEXT))

blocks = split_offer_blocks(
    TEXT
)


for i, block in enumerate(blocks):

    print()

    print("==========")

    print(f"BLOCK {i+1}")

    print("==========")

    print()

    print(block)