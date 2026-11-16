"""Differentiate NaviMind auth failure from Vercel access protection."""
from io import BytesIO
from urllib.error import HTTPError
from tools.probe_navimind_auth_layer import classify_auth_response, probe


def test_application_401_distinguished_from_html_401():
    assert classify_auth_response(
        401, "application/json", b'{"error":"UNAUTHORIZED"}'
    ) == "navimind_secret_rejected"
    assert classify_auth_response(
        401, "text/html", b"<html><body>Login</body></html>"
    ) == "vercel_or_upstream_protection"


def test_valid_auth_reaches_schema_validation_without_reasoning():
    assert classify_auth_response(
        400, "application/json", b'{"error":"INVALID_AGENT_TASK"}'
    ) == "navimind_auth_accepted_contract_validation_reached"
    assert classify_auth_response(
        400, "application/json", b'{"error":"INVALID_AGENT_TASK_V2"}'
    ) == "navimind_auth_accepted_contract_validation_reached"


def test_unknown_auth_is_not_claimed_to_be_secret_mismatch():
    assert classify_auth_response(
        403, "application/json", b'{"error":"NOT_ALLOWED"}'
    ) == "unknown_auth_layer"


def test_probe_uses_empty_invalid_contract_and_matching_header():
    class Response:
        status = 400
        headers = {"Content-Type": "application/json"}
        def read(self, n):
            return b'{"error":"INVALID_AGENT_TASK_V2"}'[:n]
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    def opener(req, timeout):
        assert req.data == b'{"version":"2"}'
        assert req.get_header("X-navimind-agent-secret") == "secret-test"
        assert timeout <= 20
        return Response()
    status, category = probe(
        url="https://navimind.app/api/agent/task",
        secret="secret-test",
        opener=opener,
    )
    assert status == 400
    assert category == "navimind_auth_accepted_contract_validation_reached"


def test_probe_sends_optional_vercel_auth_header_without_printing(monkeypatch):
    monkeypatch.setenv("NAVIMIND_VERCEL_PROTECTION_BYPASS", "vercel-test-value")
    class Response:
        status = 400
        headers = {"Content-Type": "application/json"}
        def read(self, n):
            return b'{"error":"INVALID_AGENT_TASK_V2"}'[:n]
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    def opener(req, timeout):
        assert req.get_header("X-vercel-protection-bypass") == "vercel-test-value"
        assert req.get_header("X-navimind-agent-secret") == "application-secret"
        return Response()
    status, layer = probe(
        url="https://navimind.app/api/agent/task",
        secret="application-secret",
        opener=opener,
    )
    assert (status, layer) == (
        400, "navimind_auth_accepted_contract_validation_reached"
    )
