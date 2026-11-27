"""V2 readiness is separate from conversational AI and WindowHub discovery."""
from pathlib import Path
from unittest.mock import patch

from app.agent.runtime.navimind_work_mission import BackgroundWorkMission

ROOT = Path(__file__).resolve().parents[1]


def test_reports_missing_v2_endpoint_not_generic_failure():
    with patch.dict("os.environ", {
        "NAVIMIND_AGENT_V2_URL": "",
        "NAVIMIND_AGENT_V2_SECRET": "",
        "NAVIMIND_AGENT_URL": "",
        "NAVIMIND_AGENT_SECRET": "",
        "NAVIMIND_CHAT_API_KEY": "chat-is-not-v2",
    }):
        assert BackgroundWorkMission._v2_configuration_blocker() == "v2_endpoint_missing"


def test_v2_secret_is_required_for_matching_endpoint():
    with patch.dict("os.environ", {
        "NAVIMIND_AGENT_V2_URL": "https://example.test/v2",
        "NAVIMIND_AGENT_V2_SECRET": "",
        "NAVIMIND_AGENT_URL": "",
        "NAVIMIND_AGENT_SECRET": "",
    }):
        assert BackgroundWorkMission._v2_configuration_blocker() == "v2_secret_missing"
    with patch.dict("os.environ", {
        "NAVIMIND_AGENT_V2_URL": "https://example.test/v2",
        "NAVIMIND_AGENT_V2_SECRET": "mock-secret",
        "NAVIMIND_AGENT_URL": "",
        "NAVIMIND_AGENT_SECRET": "",
    }):
        assert BackgroundWorkMission._v2_configuration_blocker() is None


def test_existing_application_is_detected_before_v2_planning():
    code = (ROOT / "tools/run_navimind_shared_control_center.py").read_text(
        encoding="utf-8"
    )
    assert "def windowhub_environment_precheck()" in code
    assert 'discover_windowhub_read_only()' in code
    assert "Uruchom program i zaloguj się osobiście" in code
    assert "Nie potrzebuję hasła w czacie" in code
    assert code.index("environment_blocker = windowhub_environment_precheck()") < code.index(
        "v2_blocker = background_work._v2_configuration_blocker()"
    )
    assert "return background_work.queue_and_plan()" in code


def test_v2_invalid_url_and_insecure_remote_transport_are_reported():
    with patch.dict("os.environ", {
        "NAVIMIND_AGENT_V2_URL": "http://not-local.example/api/agent/task",
        "NAVIMIND_AGENT_V2_SECRET": "mock",
        "NAVIMIND_AGENT_URL": "",
        "NAVIMIND_AGENT_SECRET": "",
    }):
        assert BackgroundWorkMission._v2_configuration_blocker() == "v2_endpoint_invalid"
    with patch.dict("os.environ", {
        "NAVIMIND_AGENT_V2_URL": "",
        "NAVIMIND_AGENT_V2_SECRET": "",
        "NAVIMIND_AGENT_URL": "https://example.test/wrong-path",
        "NAVIMIND_AGENT_SECRET": "mock",
    }):
        assert BackgroundWorkMission._v2_configuration_blocker() == "v2_endpoint_invalid"


def test_safe_shared_endpoint_and_localhost_v2_config_shape():
    with patch.dict("os.environ", {
        "NAVIMIND_AGENT_V2_URL": "",
        "NAVIMIND_AGENT_V2_SECRET": "",
        "NAVIMIND_AGENT_URL": "https://example.test/api/agent/task",
        "NAVIMIND_AGENT_SECRET": "mock",
    }):
        assert BackgroundWorkMission._v2_configuration_blocker() is None
    with patch.dict("os.environ", {
        "NAVIMIND_AGENT_V2_URL": "http://127.0.0.1:7777/api/agent/task",
        "NAVIMIND_AGENT_V2_SECRET": "mock",
        "NAVIMIND_AGENT_URL": "",
        "NAVIMIND_AGENT_SECRET": "",
    }):
        assert BackgroundWorkMission._v2_configuration_blocker() is None
