"""Small local catalog memory for explicitly taught, read-back-verified choices.

Only generic catalog labels are stored. No customer/order information, no
coordinates or native Windows RuntimeIds are persisted.
"""
from __future__ import annotations

import json
from pathlib import Path

VERSION = 1
FIELDS = frozenset({"profile_color", "glazing_package"})


def default_skill_file() -> Path:
    return Path.home() / ".windowhub_agent" / "verified_catalog_skills.json"


def _clean(label: str) -> str:
    if (not isinstance(label, str) or not 0 < len(label.strip()) <= 120
            or any(ord(ch) < 32 for ch in label)):
        raise ValueError("invalid_catalog_label")
    return " ".join(label.strip().split())


def skill_key(*, outside: str | None = None,
              inside: str | None = None,
              glazing_panes: int | None = None) -> tuple[str, str]:
    if glazing_panes is not None:
        if glazing_panes not in (2, 3):
            raise ValueError("invalid_glazing_panecount")
        return "glazing_package", str(glazing_panes)
    if outside is None or inside is None:
        raise ValueError("missing_sided_color")
    return "profile_color", _clean(outside).casefold() + "|" + _clean(inside).casefold()


def read_skill(field: str, key: str, *, path: Path | None = None) -> str | None:
    if field not in FIELDS or not isinstance(key, str):
        return None
    file = path or default_skill_file()
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(data, dict) or data.get("version") != VERSION:
        return None
    values = data.get("skills", {})
    if not isinstance(values, dict):
        return None
    group = values.get(field, {})
    item = group.get(key) if isinstance(group, dict) else None
    if not isinstance(item, str):
        return None
    try:
        return _clean(item)
    except ValueError:
        return None


def record_skill(field: str, key: str, observed_label: str, *,
                 human_confirmed: bool, readback_verified: bool,
                 path: Path | None = None) -> bool:
    """Promote a demonstrated choice only after independent UI readback + approval."""
    if field not in FIELDS or not isinstance(key, str) or not key.strip():
        raise ValueError("invalid_catalog_skill_key")
    if human_confirmed is not True or readback_verified is not True:
        return False
    exact = _clean(observed_label)
    file = path or default_skill_file()
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") != VERSION:
            raise ValueError("invalid_saved_catalog")
    except FileNotFoundError:
        data = {"version": VERSION, "skills": {}}
    except (OSError, ValueError, TypeError):
        # Never overwrite a malformed local memory without the user's review.
        return False
    groups = data.get("skills", {})
    if not isinstance(groups, dict):
        return False
    for name in FIELDS:
        if not isinstance(groups.get(name, {}), dict):
            return False
    groups.setdefault(field, {})[key] = exact
    data["skills"] = groups
    file.parent.mkdir(parents=True, exist_ok=True)
    # Atomic local update, no secrets saved.
    tmp = file.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(file)
    return True
