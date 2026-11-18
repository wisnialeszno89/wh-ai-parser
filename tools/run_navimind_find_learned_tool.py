"""Find learned UI tool candidates by task wording, without moving the mouse.

Reads only local Explorer icon maps. OCR is untrusted evidence, not action
permission. Matching results NEVER authorize clicking or keyboard input.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import unicodedata


ALIASES = {
    "okucia": ("okucia", "okucie", "wybor typu okuc", "wybór typu okuć", "hardware"),
    "skrzydlo": ("skrzydlo", "skrzydłem", "skrzydlem", "sash", "oscieznica + skrzydlo"),
    "oscieznica": ("oscieznica", "oscieznicy", "rama", "frame"),
    "podzial": ("wiele pol", "rownooddalonych", "podzial", "division"),
    "nawietrzak": ("naszybowy", "nawietrzak", "vent"),
    "wymiarowanie": ("wymiarowanie", "wrebu", "dimensions"),
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def candidate_score(query: str, label: str, confidence: float | int | None):
    """Lexical discovery score only, never an execution confidence."""
    q, t = normalize(query), normalize(label)
    if not q or not t:
        return 0
    terms = [q]
    for name, synonyms in ALIASES.items():
        if q == name or q in [normalize(x) for x in synonyms]:
            terms.extend(normalize(x) for x in synonyms)
    match = max(
        (
            100 if t == term else
            85 if t.startswith(term + " ") else
            75 if term in t.split() else
            65 if (" " + term + " ") in (" " + t + " ") else
            50 if term in t else 0
        )
        for term in terms if term
    )
    if not match:
        return 0
    conf = max(0, min(100, float(confidence or 0)))
    return round(match * (0.8 + 0.2 * conf / 100), 1)


def find_candidates(icon_map: dict, query: str) -> list[dict]:
    if icon_map.get("schema") != "navimind.icon_map.unverified.v1":
        raise ValueError("icon_map_schema_unsupported")
    items = []
    for icon in icon_map.get("icons", []):
        if not isinstance(icon, dict):
            continue
        label = icon.get("label_hypothesis")
        if not isinstance(label, str) or not label.strip():
            continue
        if icon.get("evidence") != "ocr_candidate_unverified":
            continue
        score = candidate_score(query, label, icon.get("ocr_confidence"))
        if score <= 0:
            continue
        items.append({
            "label_hypothesis": label,
            "score": score,
            "relative_bounds": icon.get("relative_bounds"),
            "pointer": icon.get("pointer"),
            "behavior_verified": False,
        })
    return sorted(items, key=lambda item: item["score"], reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only semantic search in Explorer's tentative icon map")
    parser.add_argument("--map", required=True, type=Path)
    parser.add_argument("--find", required=True, help="Tool concept, e.g. okucia, skrzydlo, podzial")
    parser.add_argument("--limit", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        parser.error("--limit must be 1..20")
    if not args.map.is_file():
        print("TOOL_SEARCH_STOP=map_not_found")
        return 2
    data = json.loads(args.map.read_text(encoding="utf-8"))
    matches = find_candidates(data, args.find)
    print("TOOL_SEARCH_MODE=READ_ONLY")
    print("TOOL_SEARCH_QUERY=" + args.find)
    print("TOOL_SEARCH_MATCHES=" + str(len(matches)))
    for i, item in enumerate(matches[:args.limit]):
        print("MATCH_" + str(i) + "=" + json.dumps(item, ensure_ascii=False))
    print("TOOL_SEARCH_CLICKED=0")
    print("TOOL_SEARCH_BEHAVIOR_VERIFIED=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
