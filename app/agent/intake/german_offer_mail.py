"""Read a draft from a German enquiry with explicitly named position lines."""

import re

_POSITION = re.compile(r"^(Haustür|Haustuer|Fenster)\b\s*:?\s*(.*)$", re.IGNORECASE)
_SIZE = re.compile(
    r"(?<![\w.,+-])([1-9][0-9]{1,4})\s*[x×]\s*([1-9][0-9]{1,4})(?![\d.,])"
    r"(?:\s*mm\b)?(?!\w|\s*(?:cm|m)\b)",
    re.IGNORECASE,
)

# Sales proposals for the reviewed size. Feasibility depends on the chosen system.
_WINDOW_VARIANTS = {
    (1500, 1000): (
        "Dwa skrzydła, słupek ruchomy",
        "Dwa skrzydła, słupek stały",
    ),
}


def inspect_german_offer_mail(text: str) -> list[dict]:
    """Separate positions and attach proposals without selecting a configuration."""
    blocks: list[list[str]] = []
    for source_line in text.splitlines():
        line = source_line.strip()
        if _POSITION.fullmatch(line):
            blocks.append([line])
        elif line and blocks:
            blocks[-1].append(line)

    positions = []
    for heading, *notes in blocks:
        name, description = _POSITION.fullmatch(heading).groups()
        product = "window" if name.casefold() == "fenster" else "entrance_door"
        details = [line for line in [description, *notes] if line]
        sizes = [match for line in details for match in _SIZE.finditer(line)]
        width, height = map(int, sizes[0].groups()) if len(sizes) == 1 else (None, None)
        white = any(re.fullmatch(r"weiss\s*/\s*weiss", line.casefold()) for line in details)
        variants = ()
        if product == "window" and len(details) == 1 and _SIZE.fullmatch(details[0]):
            variants = _WINDOW_VARIANTS.get((width, height), ())

        positions.append({
            "product_type": product,
            "width_mm": width,
            "height_mm": height,
            "quantity": None,
            "profile": None,
            "color_inside": "white" if white else None,
            "color_outside": "white" if white else None,
            "source_lines": [heading, *notes],
            "proposed_variants": variants,
        })
    return positions
