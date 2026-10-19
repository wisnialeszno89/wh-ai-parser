from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.agent.adapters.browser_adapter import (
    BrowserElement,
    BrowserPage,
    BrowserProvider,
)


class PlaywrightBrowserProvider(BrowserProvider):
    """
    Concrete BrowserProvider backed by Playwright's synchronous Python API.

    All Playwright locators and runtime objects remain provider-local.
    """

    SUPPORTED_BROWSER_TYPES = frozenset(
        {"chromium", "firefox", "webkit"}
    )

    _ROLE_CAPABILITIES = {
        "button": "CLICKABLE",
        "link": "CLICKABLE",
        "checkbox": "CLICKABLE",
        "radio": "CLICKABLE",
        "textbox": "EDITABLE",
        "combobox": "SELECTABLE",
        "listbox": "SELECTABLE",
    }

    def __init__(
        self,
        *,
        browser_type: str = "chromium",
        headless: bool | None = None,
        user_data_dir: str | Path | None = None,
        navigation_timeout_ms: int = 30_000,
        max_elements: int = 150,
    ) -> None:
        normalized_type = browser_type.strip().casefold()

        if normalized_type not in self.SUPPORTED_BROWSER_TYPES:
            raise ValueError(
                f"Unsupported Playwright browser type: {browser_type!r}"
            )

        if navigation_timeout_ms < 1:
            raise ValueError("navigation_timeout_ms must be positive.")

        if max_elements < 1:
            raise ValueError("max_elements must be positive.")

        self.browser_type = normalized_type
        self.headless = (
            self._env_bool("AGENT_BROWSER_HEADLESS", True)
            if headless is None
            else headless
        )
        self.user_data_dir = (
            Path(user_data_dir)
            if user_data_dir is not None
            else None
        )
        self.navigation_timeout_ms = navigation_timeout_ms
        self.max_elements = max_elements

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def is_available(self) -> bool:
        if not self._env_bool("AGENT_BROWSER_ENABLED", False):
            return False

        try:
            import playwright.sync_api  # noqa: F401
        except ImportError:
            return False

        return True

    def open(self, url: str) -> BrowserPage:
        page = self._ensure_page()
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=self.navigation_timeout_ms,
        )
        return self._snapshot(page)

    def current_page(self) -> BrowserPage:
        return self._snapshot(self._ensure_page())

    def click(self, target: BrowserElement) -> BrowserPage:
        page = self._ensure_page()
        locator = self._resolve_target(page, target)
        locator.click(timeout=self.navigation_timeout_ms)
        return self._snapshot(page)

    def write_text(
        self,
        target: BrowserElement,
        value: str,
    ) -> BrowserPage:
        page = self._ensure_page()
        locator = self._resolve_target(page, target)
        locator.fill(
            value,
            timeout=self.navigation_timeout_ms,
        )
        return self._snapshot(page)

    def select_option(
        self,
        target: BrowserElement,
        value: str,
    ) -> BrowserPage:
        page = self._ensure_page()
        locator = self._resolve_target(page, target)

        tag_name = str(
            (target.metadata or {}).get("tag_name", "")
        ).casefold()

        if tag_name == "select":
            self._select_native_option(locator, value)
        else:
            locator.click(timeout=self.navigation_timeout_ms)
            option = page.get_by_role(
                "option",
                name=value,
                exact=True,
            )
            self._require_unique_visible(
                option,
                target=f"option '{value}'",
            )
            option.click(timeout=self.navigation_timeout_ms)

        return self._snapshot(page)

    def back(self) -> BrowserPage:
        page = self._ensure_page()
        page.go_back(
            wait_until="domcontentloaded",
            timeout=self.navigation_timeout_ms,
        )
        return self._snapshot(page)

    def close(self) -> None:
        try:
            if self._context is not None:
                self._context.close()
        finally:
            try:
                if self._browser is not None:
                    self._browser.close()
            finally:
                self._context = None
                self._browser = None
                self._page = None

                if self._playwright is not None:
                    self._playwright.stop()
                    self._playwright = None

    def _ensure_page(self):
        if self._page is not None and not self._page.is_closed():
            return self._page

        if not self.is_available():
            raise RuntimeError(
                "Playwright browser provider is disabled or unavailable. "
                "Set AGENT_BROWSER_ENABLED=1 and install Playwright."
            )

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is not installed.") from exc

        self._playwright = sync_playwright().start()
        browser_type = getattr(
            self._playwright,
            self.browser_type,
        )

        if self.user_data_dir is not None:
            self.user_data_dir.mkdir(
                parents=True,
                exist_ok=True,
            )
            self._context = browser_type.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
            )
            self._browser = None
        else:
            self._browser = browser_type.launch(
                headless=self.headless,
            )
            self._context = self._browser.new_context()

        pages = self._context.pages
        self._page = (
            pages[0]
            if pages
            else self._context.new_page()
        )
        self._page.set_default_timeout(
            self.navigation_timeout_ms
        )

        return self._page

    def _snapshot(self, page) -> BrowserPage:
        return BrowserPage(
            url=page.url,
            title=page.title(),
            text=self._page_text(page),
            elements=tuple(self._collect_elements(page)),
        )

    @staticmethod
    def _page_text(page) -> str:
        try:
            text = page.locator("body").inner_text(timeout=2_000)
        except Exception:
            return ""
        return text.strip()[:20_000]

    def _collect_elements(self, page):
        elements: list[BrowserElement] = []

        for role, capability in self._ROLE_CAPABILITIES.items():
            locator = page.get_by_role(role)

            try:
                count = locator.count()
            except Exception:
                continue

            available = min(
                count,
                self.max_elements - len(elements),
            )

            for index in range(available):
                candidate = locator.nth(index)

                try:
                    if not candidate.is_visible():
                        continue

                    details = candidate.evaluate(
                        self._ELEMENT_DETAILS_SCRIPT
                    )
                except Exception:
                    continue

                label = details.get("label")
                source = details.get("label_source")

                if (
                    not isinstance(label, str)
                    or not label.strip()
                    or not isinstance(source, str)
                    or not source.strip()
                ):
                    continue

                elements.append(
                    BrowserElement(
                        label=label.strip(),
                        kind=role,
                        interaction_capability=capability,
                        current_value=self._read_current_value(
                            candidate,
                            role,
                            details.get("tag_name"),
                        ),
                        confidence=0.99,
                        metadata={
                            "provider": "playwright",
                            "strategy": source,
                            "locator_value": label.strip(),
                            "role": role,
                            "tag_name": details.get("tag_name"),
                        },
                    )
                )

                if len(elements) >= self.max_elements:
                    return elements

        return elements

    @staticmethod
    def _read_current_value(
        locator,
        role: str,
        tag_name: Any,
    ) -> str | None:
        normalized_tag = str(tag_name or "").casefold()

        try:
            if role in {"checkbox", "radio"}:
                return str(locator.is_checked()).casefold()

            if normalized_tag in {"input", "textarea"}:
                value = locator.input_value()
                return value if value != "" else None

            if normalized_tag == "select":
                option = locator.locator("option:checked").first
                text = option.text_content()
                if isinstance(text, str):
                    return text.strip() or None
        except Exception:
            return None

        return None

    @classmethod
    def _resolve_target(cls, page, target: BrowserElement):
        metadata = target.metadata or {}
        strategy = metadata.get("strategy")
        value = metadata.get("locator_value")
        role = metadata.get("role")

        if not isinstance(strategy, str):
            raise PermissionError(
                "Browser target has no provider-local locator strategy."
            )

        if not isinstance(value, str) or not value.strip():
            raise PermissionError(
                "Browser target has no provider-local locator value."
            )

        normalized_strategy = strategy.casefold()

        if normalized_strategy == "label":
            locator = page.get_by_label(
                value,
                exact=True,
            )
        elif normalized_strategy in {
            "aria-label",
            "placeholder",
            "title",
            "text",
            "name",
        }:
            if not isinstance(role, str) or not role.strip():
                raise PermissionError(
                    "Browser target lacks a semantic role."
                )
            locator = page.get_by_role(
                role,
                name=value,
                exact=True,
            )
        else:
            raise PermissionError(
                "Unsupported provider-local browser locator strategy."
            )

        cls._require_unique_visible(
            locator,
            target=f"browser element '{target.label}'",
        )
        return locator

    @staticmethod
    def _require_unique_visible(locator, *, target: str) -> None:
        count = locator.count()
        if count != 1:
            raise PermissionError(
                f"Browser target '{target}' is ambiguous "
                f"(matched {count} elements)."
            )
        if not locator.is_visible():
            raise PermissionError(
                f"Browser target '{target}' is not visible."
            )

    @staticmethod
    def _select_native_option(locator, value: str) -> None:
        try:
            locator.select_option(
                label=value,
                timeout=30_000,
            )
            return
        except Exception:
            try:
                locator.select_option(
                    value=value,
                    timeout=30_000,
                )
                return
            except Exception as exc:
                raise PermissionError(
                    f"Browser option '{value}' could not be selected."
                ) from exc

    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().casefold() in {
            "1",
            "true",
            "yes",
            "on",
        }

    _ELEMENT_DETAILS_SCRIPT = r"""
    element => {
        const clean = value => {
            if (typeof value !== "string") return "";
            return value.replace(/\s+/g, " ").trim();
        };

        const directLabel = clean(element.getAttribute("aria-label"));
        if (directLabel) {
            return {
                label: directLabel,
                label_source: "aria-label",
                tag_name: element.tagName.toLowerCase()
            };
        }

        const id = element.id;
        if (id) {
            const selector = 'label[for="' + CSS.escape(id) + '"]';
            const label = document.querySelector(selector);
            const text = clean(label?.innerText);
            if (text) {
                return {
                    label: text,
                    label_source: "label",
                    tag_name: element.tagName.toLowerCase()
                };
            }
        }

        const wrappingLabel = clean(
            element.closest("label")?.innerText
        );
        if (wrappingLabel) {
            return {
                label: wrappingLabel,
                label_source: "label",
                tag_name: element.tagName.toLowerCase()
            };
        }

        const placeholder = clean(
            element.getAttribute("placeholder")
        );
        if (placeholder) {
            return {
                label: placeholder,
                label_source: "placeholder",
                tag_name: element.tagName.toLowerCase()
            };
        }

        const title = clean(element.getAttribute("title"));
        if (title) {
            return {
                label: title,
                label_source: "title",
                tag_name: element.tagName.toLowerCase()
            };
        }

        const text = clean(element.innerText);
        if (text) {
            return {
                label: text,
                label_source: "text",
                tag_name: element.tagName.toLowerCase()
            };
        }

        const name = clean(element.getAttribute("name"));
        if (name) {
            return {
                label: name,
                label_source: "name",
                tag_name: element.tagName.toLowerCase()
            };
        }

        return {
            label: "",
            label_source: "",
            tag_name: element.tagName.toLowerCase()
        };
    }
    """
