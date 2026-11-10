"""Read a draft from a German enquiry with explicitly named position lines."""

import re

_PIECES = r"(?<![\w.,+-])(\d+)\s*(?:Stk\.?|Stück)(?!\w)"
_POSITION = re.compile(
    rf"^(?:{_PIECES}\s+)?(Haustür|Haustuer|Fenster|Kipp-?fenster|(?:Rundbogen|Segmentbogen|Bogen)fenster|(?:PSK|HST)[- ]T[üu]r|Schiebet[üu]r)\b\s*:?\s*(.*)$",
    re.IGNORECASE,
)
_QUANTITY = re.compile(_PIECES, re.IGNORECASE)
_LAYOUT = re.compile(r"\b[A-Z][A-Z0-9]*(?:[ \t]*\+[ \t]*[A-Z][A-Z0-9]*)+\b", re.IGNORECASE)
_OPENING = re.compile(r"(?<![\w-])(?:DKL|DKR|RUP|RUL|LUP|DL|DR|RU|R|L)(?![\w-])", re.IGNORECASE)
_SPLIT = re.compile(r"\bTeilung\s*:?\s*(\d+)\s*mm\s+von\s+links\b", re.IGNORECASE)
_F004 = re.compile(r"\bF004\s+DK-Fenster\b", re.IGNORECASE)
_TILT_ONLY = re.compile(r"(?<![\w-])(?:kipp-?fenster|nur[ \t]+kippbar)\b", re.IGNORECASE)
_TURN_TILT = re.compile(r"\b(?:Dreh[ -]?Kipp|Kipp[ -]?Dreh)(?:-?fenster)?\b", re.IGNORECASE)
_NEGATED_TILT = re.compile(r"\b(?:nicht|kein\w*)[ \t]+" + _TILT_ONLY.pattern, re.IGNORECASE)
_KIPP = re.compile(r"(?<![\w-])kipp(?![\w-])", re.IGNORECASE)
_NEGATED_KIPP = re.compile(r"\b(?:nicht|kein\w*)[ \t]+kipp\b", re.IGNORECASE)
_SINGLE_SASH = re.compile(r"\b(?:einfl[üu]gelig|1[ -]fl[üu]gelig)\b", re.IGNORECASE)
_MULTIPLE_SASHES = re.compile(r"\b(?:(?:zwei|drei|vier)fl[üu]gelig|[2-9][ -]fl[üu]gelig)\b", re.IGNORECASE)
_PSK = re.compile(r"\b(?:PSK|Parallel[- ]Schiebe[- ]Kipp)\b", re.IGNORECASE)
_HST = re.compile(r"\b(?:HST|Hebe[- ]Schiebe)\b", re.IGNORECASE)
_NEGATED_SLIDING = re.compile(r"\b(?:nicht|kein\w*)[ \t]+(?:PSK|HST)\b", re.IGNORECASE)
_ARCH = re.compile(r"\b(?:Rundbogen|Segmentbogen|Bogen)fenster\b", re.IGNORECASE)
_ARCH_RISE = re.compile(r"\bStichh[öo]he\s*:?\s*(\d+)\s*mm\b", re.IGNORECASE)
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


def _opening_codes(block, product):
    if product == "sliding_door":
        return set()
    left, right = ("DL", "DR") if product == "entrance_door" else ("DKL", "DKR")
    aliases = {"RUL": "DKL", "LUP": "DKL", "RUP": "DKR", "L": left, "R": right}
    tokens = (token.upper() for token in _OPENING.findall(_LAYOUT.sub("", block)))
    return {aliases.get(token, token) for token in tokens}


def _stulp_line(line):
    suffix = _STULP_SUFFIX.search(line)
    if suffix is None:
        return None
    size = _SIZE.fullmatch(line[:suffix.start()])
    if size is None:
        return None
    requirement = "without_movable" if (suffix.group(1) or "").casefold() == "ohne" else "movable"
    return tuple(map(int, size.groups())), requirement


_SHADING = re.compile(
    r"^(?:Macht\s+ihr\s+)?(?:"
    r"(?P<zip>ZIP(?:[-\s]?(?:Anlagen?|Screens?))|Senkrecht[- ]?Markisen?)"
    r"|(?P<roller>Roll(?:l)?l[aä]den|Roll(?:l)?laden))\b\s*:?(?P<details>.*)$",
    re.IGNORECASE,
)
_REMOTE = re.compile(r"\b(\d+)\s*[- ]?\s*Kanal\s*[- ]?\s*Fernbedie\w*", re.IGNORECASE)
_SIGNOFF = re.compile(r"^(?:besten dank|vielen dank|mit freundlichen gr[üu][ßs]en)\b", re.IGNORECASE)
_SHADING_LABELS = {"zip": "ZIP-Anlage (Senkrechtmarkise)", "roller": "Rollladen"}


def _shading_positions(heading, notes):
    match = _SHADING.fullmatch(heading)
    kind = "zip" if match["zip"] else "roller"
    label = _SHADING_LABELS[kind]
    details = re.sub(r"^\(Senkrecht[- ]?Markisen?\)\s*[?!.]*\s*", "", match["details"].strip(), flags=re.IGNORECASE)
    common, items, remotes = [], [], {}
    # Keep individual dimension lines, including repeats and their own alternatives.
    for line in ([details] if details and re.search(r"\w", details) else []) + notes:
        if _SIGNOFF.match(line):
            break
        remote = _REMOTE.search(line)
        sizes = list(_SIZE.finditer(line))
        if remote and not sizes and kind == "roller":
            remotes.setdefault(int(remote[1]), []).append(line)
        elif sizes:
            items.append([line])
        elif re.match(r"^alle\b", line, re.IGNORECASE):
            common.append(line)
        elif items and (kind == "roller" or not _QUANTITY.fullmatch(line)):
            items[-1].append(line)
        else:
            common.append(line)

    quantities = {int(value) for line in common for value in _QUANTITY.findall(line)}
    for item in items or [[]]:
        sizes = [match for line in item for match in _SIZE.finditer(line)]
        width, height = map(int, sizes[0].groups()) if len(sizes) == 1 else (None, None)
        explicit = {int(value) for line in item for value in _QUANTITY.findall(line)}
        if len(items) <= 1:
            explicit.update(quantities)
        quantity = _unique(explicit) if explicit else None
        if not explicit and not quantities and kind == "roller" and len(sizes) == 1:
            quantity = 1
        yield {
            "product_type": "manual_shading",
            "description": " · ".join([label, *item, *common]),
            "quantity": quantity,
            "width_mm": width,
            "height_mm": height,
            "source_lines": [heading, *common, *item],
        }
    for channels, variants in remotes.items():
        base = [line for line in variants if not re.search(r"\balternativ\b", line, re.IGNORECASE)]
        yield {
            "product_type": "manual_shading",
            "description": " · ".join([f"Rollladen-Zubehör: {channels}-Kanal-Fernbedienung", *variants]),
            "quantity": _unique(int(value) for line in base for value in _QUANTITY.findall(line)),
            "source_lines": variants,
        }


def _expand_stulp_pairs(blocks):
    """Split an explicit same-size with/without Stulp pair, keeping its common notes."""
    for group, (heading, *notes) in enumerate(blocks, 1):
        match = _POSITION.fullmatch(heading)
        if match is None:
            yield [heading, *notes], None, None
            continue
        _, name, description = match.groups()
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
        line = source_line.strip().strip("*\\").strip()
        if _POSITION.fullmatch(line) or _SHADING.fullmatch(line):
            blocks.append([line])
        elif line and blocks:
            blocks[-1].append(line)

    positions = []
    for (heading, *notes), variant_group, mullion_requirement in _expand_stulp_pairs(blocks):
        if _SHADING.fullmatch(heading):
            positions.extend(_shading_positions(heading, notes))
            continue
        _, name, description = _POSITION.fullmatch(heading).groups()
        product = "entrance_door" if name.casefold() in {"haustür", "haustuer"} else "window"
        if name.casefold().startswith(("psk", "hst", "schiebet")):
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
        opening_codes = _opening_codes(block, product)

        position = {
            "product_type": product,
            "width_mm": width,
            "height_mm": height,
            "quantity": _unique(map(int, _QUANTITY.findall(block))) if variant_group is None else None,
            "layout": _unique(layouts) if product != "entrance_door" else None,
            "construction": construction,
            "opening": _unique(opening_codes),
            "split_from_left_mm": _unique(map(int, _SPLIT.findall(block))) if product != "entrance_door" else None,
            "profile": None,
            "color_inside": "white" if white else None,
            "color_outside": "white" if white else None,
            "source_lines": [heading, *notes],
            "proposed_variants": variants,
        }
        if len(opening_codes) > 1:
            position["opening_mode"] = "conflicting"
        code = position["opening"]
        if code is not None:
            position["opening_spec"] = {
                "type": "turn" if code in {"DL", "DR"} else "tilt_turn",
                "direction": {"L": "LEFT", "R": "RIGHT"}.get(code[-1]) if code != "RU" else None,
            }
        if product == "window" and (_TILT_ONLY.search(block) or _KIPP.search(_TURN_TILT.sub("", block))):
            conflicting = (
                layouts or construction or opening_codes or _TURN_TILT.search(block)
                or _NEGATED_TILT.search(block) or _NEGATED_KIPP.search(block) or variant_group is not None
            )
            position["opening_mode"] = "conflicting" if conflicting else "tilt_only"
            position["single_sash_confirmed"] = bool(_SINGLE_SASH.search(block) and not _MULTIPLE_SASHES.search(block))
            if not conflicting:
                position["opening_spec"] = {"type": "tilt", "direction": None}
        psk, hst = bool(_PSK.search(block)), bool(_HST.search(block))
        if product != "entrance_door" and (psk or hst):
            conflicting = (
                position.get("opening_mode") or _OPENING.search(block) or _F004.search(block)
                or _TURN_TILT.search(block) or (psk and hst) or _NEGATED_SLIDING.search(block)
                or variant_group is not None
            )
            position.update(
                opening_mode="conflicting" if conflicting else ("psk" if psk else "hst"),
                slide_direction=_unique("LEFT" if value.casefold() == "links" else "RIGHT"
                                        for value in _SLIDE_DIRECTION.findall(block)),
                view=_unique("inside" if value.casefold() == "innenansicht" else "outside"
                             for value in _SLIDE_VIEW.findall(block)),
            )
        if _ARCH.search(heading):
            position.update(shape="arch", arch_rise_mm=_unique(map(int, _ARCH_RISE.findall(block))))
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
