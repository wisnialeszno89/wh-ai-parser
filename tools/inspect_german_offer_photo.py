"""Read a German offer image with local Tesseract and produce a technical draft."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.german_offer_photo import read_german_offer_photo


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--tesseract", default="tesseract", help="Tesseract executable or its full path.")
    parser.add_argument("--output", type=Path, help="Save the technical draft as UTF-8 JSON.")
    args = parser.parse_args()

    try:
        if not args.image.is_file():
            raise ValueError(f"Brak pliku zdjęcia: {args.image}")
        if args.output and args.output.resolve() == args.image.resolve():
            raise ValueError("Wskaż osobny plik wyjściowy JSON.")
        executable = shutil.which(args.tesseract)
        if not executable:
            raise ValueError("Nie znaleziono Tesseract. Użyj --tesseract ze ścieżką do tesseract.exe.")
        result = subprocess.run(
            [executable, str(args.image.resolve()), "stdout", "--psm", "11", "-l", "eng", "tsv"],
            check=True, capture_output=True, encoding="utf-8", timeout=60,
        )
        draft = read_german_offer_photo(result.stdout)
        output = json.dumps(draft, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(output + "\n", encoding="utf-8")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"PHOTO_OFFER_RESULT=review\n{exc}", file=sys.stderr)
        return 2

    print("PHOTO_OFFER_RESULT=technical_draft")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
