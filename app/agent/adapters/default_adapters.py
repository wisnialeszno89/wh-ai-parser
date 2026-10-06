from __future__ import annotations

from pathlib import Path
import os

from app.agent.adapters.adapter_registry import AdapterRegistry
from app.agent.adapters.filesystem_adapter import FileSystemAdapter


def create_default_adapter_registry(
    *,
    filesystem_roots: tuple[str | Path, ...] | None = None,
) -> AdapterRegistry:
    roots = filesystem_roots

    if roots is None:
        configured_root = os.environ.get(
            "AGENT_FILESYSTEM_ROOT",
            "runtime_data/workspace",
        )
        roots = (configured_root,)

    return AdapterRegistry(
        adapters=(
            FileSystemAdapter(
                allowed_roots=roots,
            ),
        )
    )
