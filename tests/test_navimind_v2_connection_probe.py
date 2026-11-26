"""Synthetic probe must diagnose authentication without any real reasoning call."""
import io
from email.message import Message
from urllib.error import HTTPError

from tools.check_navimind_v2_connection import (
    configured_v2_connection, probe_v2,
)

URL = "https://www.navimind.app/api/agent/task"


class FakeOpener:
    def __init__(self, status=400, error="INVALID_AGENT_TASK_V2", json_response=True):
        self.status = status
        self.error = error
        self.json_response = json_response
        self.requests = []

    def open(self, req, timeout):
        self.requests.append((req, timeout))
        headers = Message()
        headers["Content-Type"] = (
            "application/json" if self.json_response else "text/html"
        )
        body = (
            ('{"error":"' + self.error + '"}').encode("utf-8")
            if self.json_response else b"<html>Sign in</html>"
        )
        raise HTTPError(req.full_url, self.status, "synthetic", headers, io.BytesIO(body))


def test_no_network_when_missing_secret():
    opener = FakeOpener()
    result = probe_v2(
        environ={"NAVIMIND_AGENT_V2_URL": URL, "NAVIMIND_AGENT_V2_SECRET": ""},
        opener=opener,
    )
    assert result == "v2_secret_missing"
    assert opener.requests == []


def test_valid_config_does_not_mean_auth_is_verified():
    blocker, connection = configured_v2_connection({
        "NAVIMIND_AGENT_V2_URL": URL,
        "NAVIMIND_AGENT_V2_SECRET": "fake-local-test-secret",
    })
    assert blocker is None
    assert connection[0] == URL


def test_expected_invalid_contract_proves_authentication_gate():
    opener = FakeOpener()
    result = probe_v2(
        environ={"NAVIMIND_AGENT_V2_URL": URL,
                 "NAVIMIND_AGENT_V2_SECRET": "fake-local-test-secret"},
        opener=opener,
    )
    assert result == "v2_authenticated_contract_rejected_as_expected"
    req, timeout = opener.requests[0]
    assert req.data == b'{"version":"2"}'
    assert timeout <= 12
    assert req.get_method() == "POST"


def test_application_secret_denied_is_separate_from_vercel_sso():
    configured = {
        "NAVIMIND_AGENT_V2_URL": URL,
        "NAVIMIND_AGENT_V2_SECRET": "fake-local-test-secret",
    }
    assert probe_v2(
        environ=configured, opener=FakeOpener(401, "UNAUTHORIZED")
    ) == "v2_application_secret_rejected"
    assert probe_v2(
        environ=configured,
        opener=FakeOpener(401, "ignored", json_response=False),
    ) == "v2_vercel_or_proxy_access_denied"


def test_secret_never_appears_in_return_codes():
    values = {
        "NAVIMIND_AGENT_V2_URL": URL,
        "NAVIMIND_AGENT_V2_SECRET": "FAKE_PRIVATE_VALUE",
        "NAVIMIND_VERCEL_PROTECTION_BYPASS": "ANOTHER_FAKE_VALUE",
    }
    opener = FakeOpener(403, "ignored", json_response=False)
    result = probe_v2(environ=values, opener=opener)
    assert "PRIVATE" not in result
    assert "ANOTHER" not in result
    req, _ = opener.requests[0]
    assert req.get_header("X-vercel-protection-bypass") == "ANOTHER_FAKE_VALUE"


def test_invalid_shared_endpoint_not_contacted():
    opener = FakeOpener()
    assert probe_v2(
        environ={"NAVIMIND_AGENT_URL":"https://www.navimind.app/login",
                 "NAVIMIND_AGENT_SECRET":"fake"},
        opener=opener,
    ) == "v2_endpoint_invalid"
    assert not opener.requests
