"""Offline chat configuration regression; never reaches the network."""
import ast
from pathlib import Path

from tools.configure_navimind_chat import KEYS, status, _secure_save


def test_chat_missing_keys_are_explicit_and_no_secrets_leak():
    state, missing, persisted = status(values={}, persisted={})
    assert state == "missing"
    assert set(missing) == set(KEYS)
    assert set(persisted) == set(KEYS)


def test_persistent_chat_configuration_validated():
    env = {
        "NAVIMIND_CHAT_URL": "https://example.org/v1/chat/completions",
        "NAVIMIND_CHAT_MODEL": "demo-model",
        "NAVIMIND_CHAT_API_KEY": "not-a-real-key",
    }
    result, missing, persisted = status(values=env, persisted=env)
    assert result == "configured"
    assert not missing
    assert not persisted


def test_chat_rejects_v2_endpoint_as_chat_endpoint():
    values = {
        "NAVIMIND_CHAT_URL": "https://example.org/api/agent/task",
        "NAVIMIND_CHAT_MODEL": "demo-model",
        "NAVIMIND_CHAT_API_KEY": "private-placeholder",
    }
    assert status(values=values, persisted=values)[0] == "invalid"


def test_setup_preserves_existing_v2_secrets_and_writes_chat(monkeypatch, tmp_path):
    from dotenv import dotenv_values
    import tools.configure_navimind_chat as module
    dest = tmp_path / ".env"
    dest.write_text("NAVIMIND_AGENT_V2_SECRET=existing-test-secret\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOTENV", dest)
    module._secure_save({
        "NAVIMIND_CHAT_URL": "https://example.org/v1/chat/completions",
        "NAVIMIND_CHAT_MODEL": "test",
        "NAVIMIND_CHAT_API_KEY": "private-test-key",
    })
    saved = dotenv_values(dest)
    assert saved["NAVIMIND_AGENT_V2_SECRET"] == "existing-test-secret"
    assert saved["NAVIMIND_CHAT_API_KEY"] == "private-test-key"


def test_launcher_is_single_powershell_script_not_duplicate(monkeypatch):
    text = Path("tools/Start-NaviMind-TwoWindows.ps1").read_text(encoding="utf-8")
    assert text.count("[CmdletBinding()]") == 1
    assert text.count("param(") == 1
    assert "tools.configure_navimind_chat --check" in text
    assert not any(ord(char) > 127 for char in text)


def test_provider_loads_repo_root_env_not_cwd():
    from app.agent.runtime.navimind_conversational_provider import ChatConfig
    source = ast.get_source_segment(
        Path("app/agent/runtime/navimind_conversational_provider.py").read_text(encoding="utf-8"),
        next(node for node in ast.walk(ast.parse(
            Path("app/agent/runtime/navimind_conversational_provider.py").read_text(encoding="utf-8")
        )) if isinstance(node, ast.FunctionDef) and node.name == "from_environment")
    )
    assert "parents[3]" in source
    assert "dotenv_values(root_env, interpolate=False)" in source

def test_chat_reads_complete_local_tuple_before_stale_process_environment(monkeypatch):
    from app.agent.runtime.navimind_conversational_provider import ChatConfig

    for key, value in zip(KEYS, ("https://example.org/v1/chat/completions", "old", "old-key")):
        monkeypatch.setenv(key, value)
    local = dict(zip(KEYS, ("https://ai-gateway.vercel.sh/v1/chat/completions", "openai/model", "verified-key")))
    monkeypatch.setattr("dotenv.dotenv_values", lambda *_args, **_kwargs: local)
    config = ChatConfig.from_environment()
    assert config.model == "openai/model"
    assert config.api_key == "verified-key"
    assert "verified-key" not in repr(config)


def test_gateway_setup_retains_existing_config_on_http_401(monkeypatch, tmp_path, capsys):
    import tools.configure_navimind_chat as settings

    dest = tmp_path / ".env"
    original = "NAVIMIND_AGENT_V2_SECRET=private-v2-value\n"
    dest.write_text(original, encoding="utf-8")
    monkeypatch.setattr(settings, "DOTENV", dest)
    monkeypatch.setattr(settings, "probe_chat", lambda _: "chat_authentication_failed_401")
    assert settings.setup_gateway(read=lambda _: "", secret_read=lambda _: "rejected-key") == 4
    assert dest.read_text(encoding="utf-8") == original
    assert "rejected-key" not in capsys.readouterr().out
