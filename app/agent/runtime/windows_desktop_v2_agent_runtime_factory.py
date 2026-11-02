"""Factory for the V2 autonomous Windows desktop computer-use runtime."""

from app.agent.reasoning.navimind_task_reasoner_v2 import (
    NaviMindTaskReasonerV2,
)
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)
from app.agent.runtime.windows_desktop_v2_agent_runtime import (
    WindowsDesktopV2AgentRuntime,
)


def create_windows_desktop_v2_agent_runtime() -> WindowsDesktopV2AgentRuntime:
    """Create a V2 runtime using NAVIMIND_AGENT_V2_URL and local Windows UIA."""
    return WindowsDesktopV2AgentRuntime(
        control_loop=create_windows_desktop_agent_control_loop(),
        reasoner=NaviMindTaskReasonerV2(),
    )
