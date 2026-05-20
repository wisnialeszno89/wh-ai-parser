from pathlib import Path

from app.ofr.utf16_extractor import extract_utf16_strings


data = Path("outputs/payload.bin").read_bytes()

strings = extract_utf16_strings(data)

for s in strings:
    print(s)