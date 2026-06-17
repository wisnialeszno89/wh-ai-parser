from app.runtime.agent_config import (
    AgentConfig
)


def test_agent_config():

    config = AgentConfig()

    assert config.real_mode is False

    assert config.debug

    assert config.screenshot_on_error