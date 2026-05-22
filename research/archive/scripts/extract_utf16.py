from pathlib import Path
import re
import zlib


INPUT_FILE = "templates/ofr_2008.ofr"

OUTPUT_DIR = Path("research/extracted")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================
# FIND & DECOMPRESS ZLIB
# ============================================

def decompress_ofr(data: bytes):

    for i in range(len(data)):

        try:
            decompressed = zlib.decompress(data[i:])

            print(f"[+] ZLIB offset: {i}")

            return decompressed

        except:
            pass

    raise Exception("[-] Nie znaleziono zlib")


# ============================================
# EXTRACT UTF16 STRINGS
# ============================================

def extract_utf16_strings(data: bytes):

    matches = re.findall(
        rb"(?:[\x20-\x7E]\x00){4,}",
        data
    )

    decoded = []

    for s in matches:

        try:
            decoded.append(
                s.decode("utf-16-le")
            )

        except:
            pass

    return decoded


# ============================================
# MAIN
# ============================================

def main():

    data = Path(INPUT_FILE).read_bytes()

    decompressed = decompress_ofr(data)

    # save raw payload
    payload_path = OUTPUT_DIR / "payload.bin"

    payload_path.write_bytes(decompressed)

    print(f"[+] Payload saved: {payload_path}")

    strings = extract_utf16_strings(decompressed)

    utf16_path = OUTPUT_DIR / "utf16_strings.txt"

    utf16_path.write_text(
        "\n".join(strings),
        encoding="utf-8"
    )

    print(f"[+] UTF16 strings: {utf16_path}")

    # IMPORTANT CLASSES
    print("\n========== KLASY ==========\n")

    keywords = [
        "CKwatera",
        "COsciez",
        "CSzyba",
        "CSlupek",
        "CPosition"
    ]

    for s in strings:

        for k in keywords:

            if k in s:
                print(s)


if __name__ == "__main__":
    main()