"""Factory for the V2 autonomous Windows desktop computer-use runtime."""

from __future__ import annotations

import os
from pathlib import Path

from app.agent.experience.experience_retriever import ExperienceRetriever
from app.agent.experience.experience_store import ExperienceStore
from app.agent.reasoning.navimind_task_reasoner_v2 import (
    NaviMindTaskReasonerV2,
)
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)
from app.agent.runtime.windows_desktop_v2_agent_runtime import (
    WindowsDesktopV2AgentRuntime,
)


def _create_experience_retriever() -> ExperienceRetriever | None:
    """Enable persistent experience only when company and operator are explicit."""
    tenant_id = os.environ.get("NAVIMIND_TENANT_ID", "").strip()
    operator_id = os.environ.get("NAVIMIND_OPERATOR_ID", "").strip()
    if not tenant_id or not operator_id:
        return None

    configured_root = os.environ.get("NAVIMIND_EXPERIENCE_DIR", "").strip()
    if configured_root:
        root_dir = Path(configured_root).expanduser()
    else:
        local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
        root_dir = (
            Path(local_app_data) / "NaviMind" / "experience"
            if local_app_data
            else Path.home() / ".navimind" / "experience"
        )

    return ExperienceRetriever(
        store=ExperienceStore(root_dir),
        tenant_id=tenant_id,
        operator_id=operator_id,
    )


def create_windows_desktop_v2_agent_runtime() -> WindowsDesktopV2AgentRuntime:
    """Create a V2 runtime using NAVIMIND_AGENT_V2_URL, UIA and scoped experience."""
    return WindowsDesktopV2AgentRuntime(
        control_loop=create_windows_desktop_agent_control_loop(),
        reasoner=NaviMindTaskReasonerV2(),
        experience_provider=_create_experience_retriever(),
    )
