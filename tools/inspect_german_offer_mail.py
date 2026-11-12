"""Preview positions and suggested variants from a German offer enquiry."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.intake.german_offer_mail import inspect_german_offer_mail
from app.agent.intake.task_document import read_task_document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mail_file", type=Path)
    args = parser.parse_args()

    try:
        text = read_task_document(args.mail_file, max_chars=12_001)
        if len(text) > 12_000:
            raise ValueError("Tekst przekracza 12 000 znaków.")
        positions = inspect_german_offer_mail(text)
        if not positions:
            raise ValueError("Brak rozpoznanego nagłówka pozycji Haustür lub Fenster.")
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"MAIL_RESULT=invalid_input\n{exc}", file=sys.stderr)
        return 2

    print("MAIL_RESULT=review")
    print(json.dumps(positions, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
