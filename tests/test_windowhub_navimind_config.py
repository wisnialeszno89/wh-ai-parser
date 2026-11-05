import pytest

from tools.run_windowhub_goal_v2 import parse_args, shared_endpoint_v2_config


def test_shared_v2_uses_existing_secure_v1_url_without_exposing_secret(monkeypatch):
    monkeypatch.setenv("NAVIMIND_AGENT_URL", "https://example.test/api/agent/task")
    monkeypatch.setenv("NAVIMIND_AGENT_SECRET", "synthetic-test-secret")
    config = shared_endpoint_v2_config()
    assert config.url == "https://example.test/api/agent/task"
    assert config.secret == "synthetic-test-secret"
    args = parse_args(["--mode", "think", "--goal", "Open a test offer", "--reuse-shared-navimind-endpoint"])
    assert args.reuse_shared_navimind_endpoint is True


@pytest.mark.parametrize("url", [
    "http://production.example.com/api/agent/task",
    "https://example.com/api/agent/task/v2",
    "https://example.com/api/agent/task?secret=bad",
    "https://bad:password@example.com/api/agent/task",
    "",
])
def test_shared_endpoint_rejects_unsafe_or_wrong_urls(monkeypatch, url):
    monkeypatch.setenv("NAVIMIND_AGENT_URL", url)
    monkeypatch.setenv("NAVIMIND_AGENT_SECRET", "synthetic-test-secret")
    with pytest.raises(ValueError):
        shared_endpoint_v2_config()


def test_shared_endpoint_requires_existing_server_secret(monkeypatch):
    monkeypatch.setenv("NAVIMIND_AGENT_URL", "https://example.com/api/agent/task")
    monkeypatch.delenv("NAVIMIND_AGENT_SECRET", raising=False)
    with pytest.raises(ValueError, match="SECRET"):
        shared_endpoint_v2_config()
