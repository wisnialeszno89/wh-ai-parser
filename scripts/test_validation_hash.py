from app.wh.validation import (
    calculate_md5
)


FILE = (
    "research/payloads/fix_ru_fix/"
    "OFR-2044-TT.OFR"
)


with open(FILE, "rb") as f:

    data = f.read()


hash_value = calculate_md5(
    data
)


print(
    "\n========== MD5 ==========\n"
)

print(hash_value)