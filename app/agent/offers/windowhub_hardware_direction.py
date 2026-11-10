"""Decide whether a verified hardware direction needs inversion."""


def plan_hardware_inversion(desired: str, observed: str | None, checked: bool | None) -> bool | None:
    """Return the required checkbox state, or None when no write is needed."""
    if desired not in {"LEFT", "RIGHT"} or observed not in {"LEFT", "RIGHT"}:
        raise ValueError("Brak jednoznacznego kierunku okucia.")
    if desired == observed:
        return None
    if type(checked) is not bool:
        raise ValueError("Brak jednoznacznego stanu pola Inwersja.")
    return not checked
