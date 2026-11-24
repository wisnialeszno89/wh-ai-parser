"""Contract checks for opt-in owner-only Windows AI Gateway setup."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(name):
    return (ROOT / "tools" / name).read_text(encoding="utf-8")


def test_enrolment_does_not_write_plaintext_api_key():
    script = text("setup_navimind_owner_gateway.ps1")
    assert 'Read-Host "Klucz AI Gateway" -AsSecureString' in script
    assert "ConvertFrom-SecureString" in script
    assert "owner-gateway.dpapi" in script
    assert "Set-Content -LiteralPath $file -Value $encrypted" in script
    assert "Write-Host $secure" not in script
    assert "Set-Content -LiteralPath $file -Value $secure" not in script


def test_launcher_uses_gateway_compatible_chat_completions():
    script = text("start_navimind_owner.ps1")
    assert "https://ai-gateway.vercel.sh/v1/chat/completions" in script
    assert 'openai/gpt-4o-mini' in script
    assert "$env:NAVIMIND_CHAT_API_KEY = $secret" in script
    assert "ConvertTo-SecureString" in script
    assert "owner-gateway.dpapi" in script


def test_launcher_explicitly_does_not_enable_windowhub_actions():
    script = text("start_navimind_owner.ps1")
    assert '$env:COMPUTER_USE_LIVE = "0"' in script
    assert 'run_navimind_shared_control_center.py' in script
    assert "Remove-Item Env:\\NAVIMIND_CHAT_API_KEY" in script
    assert "Write-Host $secret" not in script


def test_scripts_have_no_hardcoded_gateway_key():
    for script in ("setup_navimind_owner_gateway.ps1", "start_navimind_owner.ps1"):
        value = text(script)
        assert "vck_" not in value
        assert "sk-proj-" not in value
