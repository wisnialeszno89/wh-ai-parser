"""Persistent private NaviMind conversation configuration.

Usage:
  python -m tools.configure_navimind_chat --check
  python -m tools.configure_navimind_chat --setup

Gateway setup tests synthetic chat before replacing its local configuration.
Chat setup preserves V2 settings. Diagnostics omit credentials.
"""
from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

from app.agent.runtime.navimind_conversational_provider import (
    CHAT_CONFIG_KEYS as KEYS, DEFAULT_GATEWAY_MODEL, VERCEL_GATEWAY_CHAT_URL,
    ChatConfig, probe_chat,
)

ROOT = Path(__file__).resolve().parents[1]
DOTENV = ROOT / ".env"


def status(*, values=None, persisted=None):
    values = values if values is not None else os.environ
    if persisted is None:
        from dotenv import dotenv_values
        persisted = dotenv_values(DOTENV, interpolate=False) if DOTENV.is_file() else {}
    missing = [key for key in KEYS if not str(values.get(key) or "").strip()]
    permanent_missing = [
        key for key in KEYS if not str(persisted.get(key) or "").strip()
    ]
    if missing:
        return "missing", missing, permanent_missing
    try:
        ChatConfig.from_values(values)
    except (ValueError, TypeError):
        return "invalid", [], permanent_missing
    return "configured", [], permanent_missing


def _secure_save(entries: dict[str, str], *, path: Path | None = None):
    import shutil
    from tempfile import NamedTemporaryFile
    from dotenv import set_key

    target = DOTENV if path is None else path
    with NamedTemporaryFile(dir=target.parent, prefix=".env.navimind-", suffix=".tmp", delete=False) as handle:
        pending = Path(handle.name)
    try:
        if target.is_file():
            shutil.copyfile(target, pending)
        for key, value in entries.items():
            if not set_key(str(pending), key, value, quote_mode="always")[0]:
                raise OSError("local_settings_write_failed")
        pending.replace(target)
    finally:
        pending.unlink(missing_ok=True)


def setup_gateway(*, read=input, secret_read=getpass.getpass):
    print("NAVIMIND_CHAT_SETUP=vercel_gateway")
    try:
        model = read(f"Model Gateway [{DEFAULT_GATEWAY_MODEL}]: ").strip() or DEFAULT_GATEWAY_MODEL
        key = secret_read("Klucz AI Gateway z panelu Vercel: ").strip()
        config = ChatConfig(VERCEL_GATEWAY_CHAT_URL, model, key)
    except (EOFError, KeyboardInterrupt):
        print("NAVIMIND_CHAT_SETUP=cancelled")
        return 2
    except (ValueError, TypeError):
        print("NAVIMIND_CHAT_SETUP=invalid_configuration")
        return 2
    return _verify_and_save(config)


def _verify_and_save(config: ChatConfig) -> int:
    result = probe_chat(config)
    print("NAVIMIND_CHAT_PROBE_RESULT=" + result)
    if result != "chat_probe_verified":
        return 4
    try:
        _secure_save(dict(zip(KEYS, (config.url, config.model, config.api_key))))
    except (OSError, ValueError):
        print("NAVIMIND_CHAT_SETUP=save_failed")
        return 3
    print("NAVIMIND_CHAT_SETUP=saved_to_private_env")
    print("NAVIMIND_CHAT_NETWORK_VERIFIED=True")
    return 0


def setup(*, read=input, secret_read=getpass.getpass):
    print("NAVIMIND_CHAT_SETUP=interactive_private")
    print("Wymagany adres HTTPS zakonczony /v1/chat/completions.")
    print("Wybierz adres i nazwe modelu dostawcy, z ktorego korzystasz.")
    print("Danych wpisanych tutaj nie wysylaj do czatu ChatGPT.")
    url = read("Endpoint CHAT (HTTPS): ").strip()
    model = read("Model CHAT: ").strip()
    key = secret_read("Klucz API CHAT (ukryty): ").strip()
    try:
        config = ChatConfig(url=url, model=model, api_key=key)
    except (ValueError, TypeError):
        print("NAVIMIND_CHAT_SETUP=invalid_configuration")
        return 2
    return _verify_and_save(config)


def main(argv=None):
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--setup", action="store_true")
    group.add_argument("--setup-gateway", action="store_true")
    group.add_argument("--probe", action="store_true")
    args = parser.parse_args(argv)
    if args.setup:
        return setup()
    if args.setup_gateway:
        return setup_gateway()
    from dotenv import dotenv_values
    persisted = dotenv_values(DOTENV, interpolate=False)
    effective = persisted if all((persisted.get(key) or "").strip() for key in KEYS) else os.environ
    result, missing, permanent_missing = status(values=effective, persisted=persisted)
    if args.probe and result == "configured":
        outcome = probe_chat(ChatConfig.from_values(effective))
        verified = outcome == "chat_probe_verified"
        print("NAVIMIND_CHAT_PROBE_RESULT=" + outcome)
        print("NAVIMIND_CHAT_NETWORK_VERIFIED=" + str(verified))
        return 0 if verified else 4
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
