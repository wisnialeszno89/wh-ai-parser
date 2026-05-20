import zlib

INPUT_FILE = "OFR-2008-.OFR"
OUTPUT_FILE = "MODIFIED.OFR"

# ============================================
# READ FILE
# ============================================

with open(INPUT_FILE, "rb") as f:
    data = f.read()

header = data[:9]

compressed = data[9:]

# ============================================
# DECOMPRESS
# ============================================

decompressed = zlib.decompress(compressed)

# ============================================
# REPLACE VALUES
# ============================================

# UTF16 replacements

old_dim = "1111x2222".encode("utf-16-le")
new_dim = "1555x2222".encode("utf-16-le")

decompressed = decompressed.replace(old_dim, new_dim)

old_prop = 'Val="1.111"'.encode("utf-16-le")
new_prop = 'Val="1.555"'.encode("utf-16-le")

decompressed = decompressed.replace(old_prop, new_prop)

# ============================================
# RECOMPRESS
# ============================================

recompressed = zlib.compress(decompressed)

# ============================================
# SAVE
# ============================================

with open(OUTPUT_FILE, "wb") as f:
    f.write(header + recompressed)

print(f"[+] Zapisano: {OUTPUT_FILE}")