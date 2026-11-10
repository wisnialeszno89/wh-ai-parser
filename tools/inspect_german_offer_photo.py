"""Read a German offer image with local Tesseract and produce a technical draft."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.german_offer_photo import read_german_offer_photo_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--tesseract", default="tesseract", help="Tesseract executable or its full path.")
    parser.add_argument("--insect-screen-service", action="store_true",
                        help="Prepare a replacement draft from invoice items marked with a blue X.")
    parser.add_argument("--output", type=Path, help="Save the technical draft as UTF-8 JSON.")
    args = parser.parse_args()

    try:
        if args.output and args.output.resolve() == args.image.resolve():
            raise ValueError("Wskaż osobny plik wyjściowy JSON.")
        if args.insect_screen_service:
            from app.agent.intake.insect_screen_service_photo import read_insect_screen_service_photo

            draft = read_insect_screen_service_photo(args.image, tesseract=args.tesseract)
        else:
            draft = read_german_offer_photo_file(args.image, tesseract=args.tesseract)
        output = json.dumps(draft, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(output + "\n", encoding="utf-8")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"PHOTO_OFFER_RESULT=review\n{exc}", file=sys.stderr)
        return 2

    print(f"PHOTO_OFFER_RESULT={draft['status']}")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
