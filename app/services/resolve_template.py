from pathlib import Path


BASE_DIR = Path(
    "research/payloads"
)


def resolve_template(
    template_key: str
):

    template_dir = (
        BASE_DIR / template_key.lower()
    )

    if not template_dir.exists():

        return None

    files = list(
        template_dir.glob("*.OFR")
    )

    if not files:

        return None

    return str(files[0])