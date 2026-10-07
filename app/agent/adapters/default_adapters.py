from __future__ import annotations

from pathlib import Path
import os

from app.agent.adapters.adapter_registry import AdapterRegistry
from app.agent.adapters.browser_adapter import BrowserAdapter
from app.agent.adapters.email_draft_adapter import EmailDraftAdapter
from app.agent.adapters.excel_workbook_adapter import ExcelWorkbookAdapter
from app.agent.adapters.filesystem_adapter import FileSystemAdapter
from app.agent.adapters.word_document_adapter import WordDocumentAdapter


class UnconfiguredBrowserProvider:
    """Unavailable provider placeholder until a concrete browser engine is configured."""

    def is_available(self) -> bool:
        return False

    def open(self, url: str):
        raise RuntimeError("No browser provider is configured.")

    def current_page(self):
        raise RuntimeError("No browser provider is configured.")

    def click(self, target):
        raise RuntimeError("No browser provider is configured.")

    def write_text(self, target, value: str):
        raise RuntimeError("No browser provider is configured.")

    def select_option(self, target, value: str):
        raise RuntimeError("No browser provider is configured.")

    def back(self):
        raise RuntimeError("No browser provider is configured.")


def create_default_adapter_registry(
    *,
    filesystem_roots: tuple[str | Path, ...] | None = None,
    browser_provider=None,
    browser_allowed_domains: tuple[str, ...] = (),
    browser_dry_run: bool = True,
) -> AdapterRegistry:
    roots = filesystem_roots

    if roots is None:
        configured_root = os.environ.get(
            "AGENT_FILESYSTEM_ROOT",
            "runtime_data/workspace",
        )
        roots = (configured_root,)

    if browser_provider is None:
        browser_provider = UnconfiguredBrowserProvider()

    return AdapterRegistry(
        adapters=(
            BrowserAdapter(
                provider=browser_provider,
                allowed_domains=browser_allowed_domains,
                dry_run=browser_dry_run,
            ),
            FileSystemAdapter(
                allowed_roots=roots,
            ),
            ExcelWorkbookAdapter(
                allowed_roots=roots,
            ),
            EmailDraftAdapter(
                allowed_roots=roots,
            ),
            WordDocumentAdapter(
                allowed_roots=roots,
            ),
        )
    )
