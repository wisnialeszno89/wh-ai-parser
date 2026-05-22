import zlib
import re
from pathlib import Path

INPUT_FILE = "OFR-2008-.OFR"

with open(INPUT_FILE, "rb") as f:
    data = f.read()

print(f"[+] Rozmiar pliku: {len(data)}")

found = False

for i in range(len(data)):

    try:
        decompressed = zlib.decompress(data[i:])

        print(f"[+] ZLIB znaleziony na offset: {i}")

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        with open(output_dir / "dump.bin", "wb") as f:
            f.write(decompressed)

        # ============================================
        # ASCII
        # ============================================

        ascii_strings = re.findall(rb"[ -~]{4,}", decompressed)

        with open(output_dir / "ascii_strings.txt", "w", encoding="utf-8") as f:
            for s in ascii_strings:
                try:
                    f.write(s.decode("utf-8") + "\n")
                except:
                    pass

        # ============================================
        # UTF16
        # ============================================

        utf16_strings = re.findall(
            rb"(?:[\x20-\x7E]\x00){4,}",
            decompressed
        )

        with open(output_dir / "utf16_strings.txt", "w", encoding="utf-8") as f:
            for s in utf16_strings:
                try:
                    f.write(s.decode("utf-16-le") + "\n")
                except:
                    pass

        print("[+] Zapisano ascii_strings.txt")
        print("[+] Zapisano utf16_strings.txt")

        found = True
        break

    except:
        pass

if not found:
    print("[-] Nie znaleziono zlib")