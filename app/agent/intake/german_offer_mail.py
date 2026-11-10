"""Read a draft from a German enquiry with explicitly named position lines."""

import re

_PIECES = r"(?<![\w.,+-])(\d+)\s*(?:Stk\.?|Stück)(?!\w)"
_POSITION = re.compile(
    rf"^(?:{_PIECES}\s+)?(Haustür|Haustuer|Fenster|Kipp-?fenster|PSK[- ]T[üu]r|Schiebet[üu]r)\b\s*:?\s*(.*)$",
    re.IGNORECASE,
)
_QUANTITY = re.compile(_PIECES, re.IGNORECASE)
_LAYOUT = re.compile(r"\b[A-Z][A-Z0-9]*(?:[ \t]*\+[ \t]*[A-Z][A-Z0-9]*)+\b", re.IGNORECASE)
_OPENING = re.compile(r"\b(?:DKL|DKR)\b", re.IGNORECASE)
_SPLIT = re.compile(r"\bTeilung\s*:?\s*(\d+)\s*mm\s+von\s+links\b", re.IGNORECASE)
_F004 = re.compile(r"\bF004\s+DK-Fenster\b", re.IGNORECASE)
_TILT_ONLY = re.compile(r"(?<![\w-])(?:kipp-?fenster|nur[ \t]+kippbar)\b", re.IGNORECASE)
_TURN_TILT = re.compile(r"\b(?:Dreh[ -]?Kipp|Kipp[ -]?Dreh)(?:-?fenster)?\b", re.IGNORECASE)
_NEGATED_TILT = re.compile(r"\b(?:nicht|kein\w*)[ \t]+" + _TILT_ONLY.pattern, re.IGNORECASE)
_SINGLE_SASH = re.compile(r"\b(?:einfl[üu]gelig|1[ -]fl[üu]gelig)\b", re.IGNORECASE)
_MULTIPLE_SASHES = re.compile(r"\b(?:(?:zwei|drei|vier)fl[üu]gelig|[2-9][ -]fl[üu]gelig)\b", re.IGNORECASE)
_PSK = re.compile(r"\b(?:PSK|Parallel[- ]Schiebe[- ]Kipp)\b", re.IGNORECASE)
_PSK_CONFLICT = re.compile(r"\b(?:HST|Hebe[- ]Schiebe|(?:nicht|kein\w*)[ \t]+PSK)\b", re.IGNORECASE)
_SLIDE_DIRECTION = re.compile(
    r"\bSchieberichtung\s*:?\s*(?:nach\s+)?(links|rechts)\b"
    r"(?!\s*(?:/|oder)\s*(?:nach\s+)?(?:links|rechts)\b)", re.IGNORECASE,
)
_SLIDE_VIEW = re.compile(r"\b(Innenansicht|Au(?:ß|ss)enansicht)\b", re.IGNORECASE)
_SIZE = re.compile(
    r"(?<![\w.,+-])([1-9][0-9]{1,4})\s*[x×]\s*([1-9][0-9]{1,4})(?![\d.,])"
    r"(?:\s*mm\b)?(?!\w|\s*(?:cm|m)\b)",
    re.IGNORECASE,
)
_STULP_SUFFIX = re.compile(r"\s+(?:(ohne|mit)\s+)?stulp[.;]?$", re.IGNORECASE)
_THREE_PANES = re.compile(r"dreifach[-\s]*verglasung", re.IGNORECASE)
_NARROW_PROFILE = re.compile(r"schmales\s+profil", re.IGNORECASE)
_WHITE_ANTHRACITE = re.compile(r"(?:wei(?:ß|ss)\s*/\s*anthrazit|anthrazit\s*/\s*wei(?:ß|ss))", re.IGNORECASE)

# Sales proposals for the reviewed size. Feasibility depends on the chosen system.
_WINDOW_VARIANTS = {
    (1500, 1000): (
        "Dwa skrzydła, słupek ruchomy",
        "Dwa skrzydła, słupek stały",
    ),
}


def _unique(values):
    values = set(values)
    return next(iter(values)) if len(values) == 1 else None


def _stulp_line(line):
    suffix = _STULP_SUFFIX.search(line)
    if suffix is None:
        return None
    size = _SIZE.fullmatch(line[:suffix.start()])
    if size is None:
        return None
    requirement = "without_movable" if (suffix.group(1) or "").casefold() == "ohne" else "movable"
    return tuple(map(int, size.groups())), requirement


def _expand_stulp_pairs(blocks):
    """Split an explicit same-size with/without Stulp pair, keeping its common notes."""
    for group, (heading, *notes) in enumerate(blocks, 1):
        _, name, description = _POSITION.fullmatch(heading).groups()
        if name.casefold() == "fenster" and len(notes) >= 2:
            first, second = map(_stulp_line, notes[-2:])
            common = [description, *notes[:-2]]
            if (
                first and second and first[0] == second[0] and first[1] != second[1]
                and not any(_SIZE.search(line) for line in common)
            ):
                for line, (_, requirement) in zip(notes[-2:], (first, second)):
                    yield [heading, *notes[:-2], line], group, requirement
                continue
        yield [heading, *notes], None, None


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
    for (heading, *notes), variant_group, mullion_requirement in _expand_stulp_pairs(blocks):
        _, name, description = _POSITION.fullmatch(heading).groups()
        product = "entrance_door" if name.casefold() in {"haustür", "haustuer"} else "window"
        if name.casefold().startswith(("psk", "schiebet")):
            product = "sliding_door"
        details = [line for line in [description, *notes] if line]
        block = "\n".join([heading, *notes])
        sizes = [match for line in details for match in _SIZE.finditer(line)]
        width, height = map(int, sizes[0].groups()) if len(sizes) == 1 else (None, None)
        white = any(re.fullmatch(r"weiss\s*/\s*weiss", line.casefold()) for line in details)
        variants = ()
        if product == "window" and len(details) == 1 and _SIZE.fullmatch(details[0]):
            variants = _WINDOW_VARIANTS.get((width, height), ())
        layouts = ["".join(value.upper().split()) for value in _LAYOUT.findall(block)]
        construction = "F004 DK-Fenster" if product == "window" and not layouts and _F004.search(block) else None

        position = {
            "product_type": product,
            "width_mm": width,
            "height_mm": height,
            "quantity": _unique(map(int, _QUANTITY.findall(block))) if variant_group is None else None,
            "layout": _unique(layouts) if product != "entrance_door" else None,
            "construction": construction,
            "opening": _unique(value.upper() for value in _OPENING.findall(block)) if product == "window" else None,
            "split_from_left_mm": _unique(map(int, _SPLIT.findall(block))) if product != "entrance_door" else None,
            "profile": None,
            "color_inside": "white" if white else None,
            "color_outside": "white" if white else None,
            "source_lines": [heading, *notes],
            "proposed_variants": variants,
        }
        if product == "window" and _TILT_ONLY.search(block):
            conflicting = (
                layouts or construction or position["opening"] or _OPENING.search(block)
                or _TURN_TILT.search(block) or _NEGATED_TILT.search(block) or variant_group is not None
            )
            position["opening_mode"] = "conflicting" if conflicting else "tilt_only"
            position["single_sash_confirmed"] = bool(_SINGLE_SASH.search(block) and not _MULTIPLE_SASHES.search(block))
        if product != "entrance_door" and _PSK.search(block):
            conflicting = (
                position.get("opening_mode") or _OPENING.search(block) or _F004.search(block)
                or _TURN_TILT.search(block) or _PSK_CONFLICT.search(block) or variant_group is not None
            )
            position.update(
                opening_mode="conflicting" if conflicting else "psk",
                slide_direction=_unique("LEFT" if value.casefold() == "links" else "RIGHT"
                                        for value in _SLIDE_DIRECTION.findall(block)),
                view=_unique("inside" if value.casefold() == "innenansicht" else "outside"
                             for value in _SLIDE_VIEW.findall(block)),
            )
        if variant_group is not None:
            position.update(
                variant_group=variant_group,
                mullion_requirement=mullion_requirement,
                glazing_panes=3 if any(_THREE_PANES.fullmatch(line) for line in details) else None,
                profile_preference="narrow" if any(_NARROW_PROFILE.fullmatch(line) for line in details) else None,
                color_pair=_unique(line for line in details if _WHITE_ANTHRACITE.fullmatch(line)),
            )
        positions.append(position)
    return positions
