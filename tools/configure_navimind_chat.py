"""Persistent private NaviMind conversation configuration.

Usage:
  python -m tools.configure_navimind_chat --check
  python -m tools.configure_navimind_chat --setup

Never prints URLs, model names, keys or secrets. Setup stores all three chat
settings in .env using python-dotenv. V2 settings remain untouched.
"""
from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOTENV = ROOT / ".env"
KEYS = ("NAVIMIND_CHAT_URL", "NAVIMIND_CHAT_MODEL", "NAVIMIND_CHAT_API_KEY")


def status(*, values=None, persisted=None):
    from app.agent.runtime.navimind_conversational_provider import ChatConfig
    values = values if values is not None else os.environ
    if persisted is None:
        from dotenv import dotenv_values
        persisted = dotenv_values(DOTENV) if DOTENV.is_file() else {}
    missing = [key for key in KEYS if not str(values.get(key) or "").strip()]
    permanent_missing = [
        key for key in KEYS if not str(persisted.get(key) or "").strip()
    ]
    if missing:
        return "missing", missing, permanent_missing
    try:
        ChatConfig(
            url=str(values["NAVIMIND_CHAT_URL"]),
            model=str(values["NAVIMIND_CHAT_MODEL"]),
            api_key=str(values["NAVIMIND_CHAT_API_KEY"]),
        )
    except (ValueError, TypeError):
        return "invalid", [], permanent_missing
    return "configured", [], permanent_missing


def _secure_save(entries: dict[str, str]):
    from dotenv import set_key
    DOTENV.touch(exist_ok=True)
    for key in KEYS:
        if key in entries:
            set_key(str(DOTENV), key, entries[key], quote_mode="always")


def setup(*, read=input, secret_read=getpass.getpass):
    from app.agent.runtime.navimind_conversational_provider import ChatConfig
    print("NAVIMIND_CHAT_SETUP=interactive_private")
    print("Wymagany adres HTTPS zakonczony /v1/chat/completions.")
    print("Wybierz adres i nazwe modelu dostawcy, z ktorego korzystasz.")
    print("Danych wpisanych tutaj nie wysylaj do czatu ChatGPT.")
    url = read("Endpoint CHAT (HTTPS): ").strip()
    model = read("Model CHAT: ").strip()
    key = secret_read("Klucz API CHAT (ukryty): ").strip()
    try:
        ChatConfig(url=url, model=model, api_key=key)
    except (ValueError, TypeError):
        print("NAVIMIND_CHAT_SETUP=invalid_configuration")
        return 2
    try:
        _secure_save(dict(zip(KEYS, (url, model, key))))
    except (OSError, ValueError):
        print("NAVIMIND_CHAT_SETUP=save_failed")
        return 3
    # Do not preserve previous per-process CHAT values for this setup.
    print("NAVIMIND_CHAT_SETUP=saved_to_private_env")
    print("NAVIMIND_CHAT_SETUP_RESTART_REQUIRED=True")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--setup", action="store_true")
    args = parser.parse_args(argv)
    if args.setup:
        return setup()
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=DOTENV, override=False)
    result, missing, permanent_missing = status()
    print("NAVIMIND_CHAT_STATUS=" + result)
    for key in missing:
        print("NAVIMIND_CHAT_MISSING=" + key)
    if permanent_missing:
        print("NAVIMIND_CHAT_PERSISTED=False")
        for key in permanent_missing:
            print("NAVIMIND_CHAT_NOT_IN_PRIVATE_ENV=" + key)
    else:
        print("NAVIMIND_CHAT_PERSISTED=True")
    print("NAVIMIND_CHAT_NETWORK_VERIFIED=False")
    return 0 if result == "configured" else 2


if __name__ == "__main__":
    raise SystemExit(main())
