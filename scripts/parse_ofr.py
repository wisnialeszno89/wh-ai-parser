import zlib
import re

INPUT_FILE = "OFR-2008-.OFR"

# ============================================
# READ FILE
# ============================================

with open(INPUT_FILE, "rb") as f:
    data = f.read()

# ============================================
# FIND ZLIB
# ============================================

decompressed = None

for i in range(len(data)):

    try:
        decompressed = zlib.decompress(data[i:])
        print(f"[+] ZLIB offset: {i}")
        break

    except:
        pass

if decompressed is None:
    raise Exception("[-] Nie znaleziono zlib")

# ============================================
# EXTRACT UTF16 STRINGS
# ============================================

utf16_strings = re.findall(
    rb"(?:[\x20-\x7E]\x00){4,}",
    decompressed
)

decoded = []

for s in utf16_strings:

    try:
        decoded.append(s.decode("utf-16-le"))

    except:
        pass

# ============================================
# SEARCH DIMENSIONS
# ============================================

print("\n========== WYMIARY ==========\n")

for s in decoded:

    if re.search(r"\d+x\d+", s):
        print(s)

# ============================================
# SEARCH PROPS
# ============================================

print("\n========== PROPS ==========\n")

for s in decoded:

    if "<Prop" in s:
        print(s)

# ============================================
# SEARCH IMPORTANT CLASSES
# ============================================

print("\n========== KLASY ==========\n")

keywords = [
    "CKwatera",
    "COsciez",
    "CSzyba",
    "CSlupek",
    "CPosition"
]

for s in decoded:

    for k in keywords:

        if k in s:
            print(s)