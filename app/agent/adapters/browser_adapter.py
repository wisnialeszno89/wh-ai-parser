from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import urlparse

from app.agent.adapters.application_adapter import (
    AdapterDescriptor,
    ApplicationAdapter,
)


@dataclass(frozen=True)
class BrowserElement:
    """Model-safe semantic description of one browser element."""

    label: str
    kind: str = "element"
    interaction_capability: str = "UNKNOWN"
    current_value: str | None = None
    confidence: float = 0.0
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return {
            "label": self.label,
            "kind": self.kind,
            "interaction_capability": self.interaction_capability,
            "current_value": self.current_value,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class BrowserPage:
    """Semantic snapshot of the currently observed browser page."""

    url: str
    title: str
    text: str
    elements: tuple[BrowserElement, ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "url": self.url,
            "title": self.title,
            "text": self.text,
            "elements": tuple(
                element.to_payload()
                for element in self.elements
            ),
        }


class BrowserProvider(ABC):
    """Provider boundary for concrete browser automation engines."""

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def open(self, url: str) -> BrowserPage:
        raise NotImplementedError

    @abstractmethod
    def current_page(self) -> BrowserPage:
        raise NotImplementedError

    @abstractmethod
    def click(self, target: BrowserElement) -> BrowserPage:
        raise NotImplementedError

    @abstractmethod
    def write_text(
        self,
        target: BrowserElement,
        value: str,
    ) -> BrowserPage:
        raise NotImplementedError

    @abstractmethod
    def select_option(
        self,
        target: BrowserElement,
        value: str,
    ) -> BrowserPage:
        raise NotImplementedError

    @abstractmethod
    def back(self) -> BrowserPage:
        raise NotImplementedError


class BrowserAdapter(ApplicationAdapter):
    """
    Semantic browser adapter.

    The adapter exposes browser actions through stable semantic targets.
    Provider-specific selectors, coordinates, handles and runtime IDs never
    enter the public model-facing contract.
    """

    adapter_id = "browser"

    def __init__(
        self,
        *,
        provider: BrowserProvider,
        allowed_domains: Iterable[str] = (),
        dry_run: bool = True,
    ) -> None:
        self._provider = provider
        self._allowed_domains = frozenset(
            self._normalize_domain(item)
            for item in allowed_domains
            if isinstance(item, str) and item.strip()
        )
        self._dry_run = dry_run

    @property
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            adapter_id=self.adapter_id,
            application="Browser",
            capabilities=(
                "navigate",
                "read",
                "click",
                "write_text",
                "select_option",
                "back",
            ),
            description=(
                "Semantic browser navigation and interaction through a "
                "provider boundary; technical selectors and runtime "
                "identifiers remain local."
            ),
        )

    def is_available(self) -> bool:
        return self._provider.is_available()

    @property
    def dry_run(self) -> bool:
        return self._dry_run

    @property
    def allowed_domains(self) -> tuple[str, ...]:
        return tuple(sorted(self._allowed_domains))

    def open(self, url: str) -> BrowserPage:
        normalized = self._validate_url(url)

        if self._dry_run:
            return self._provider.current_page()

        return self._provider.open(normalized)

    def read(self) -> BrowserPage:
        return self._provider.current_page()

    def click(self, target: BrowserElement) -> BrowserPage:
        self._validate_target(target, capability="CLICKABLE")

        if self._dry_run:
            return self._provider.current_page()

        return self._provider.click(target)

    def write_text(
        self,
        target: BrowserElement,
        value: str,
    ) -> BrowserPage:
        self._validate_target(target, capability="EDITABLE")

        if not isinstance(value, str) or not value:
            raise ValueError("Browser text value must not be empty.")

        if self._dry_run:
            return self._provider.current_page()

        return self._provider.write_text(target, value)

    def select_option(
        self,
        target: BrowserElement,
        value: str,
    ) -> BrowserPage:
        self._validate_target(target, capability="SELECTABLE")

        if not isinstance(value, str) or not value.strip():
            raise ValueError("Browser option value must not be empty.")

        if self._dry_run:
            return self._provider.current_page()

        return self._provider.select_option(target, value)

    def back(self) -> BrowserPage:
        if self._dry_run:
            return self._provider.current_page()

        return self._provider.back()

    @staticmethod
    def _normalize_domain(value: str) -> str:
        candidate = value.strip().casefold()
        if "://" in candidate:
            parsed = urlparse(candidate)
            candidate = parsed.hostname or ""
        else:
            candidate = candidate.split("/", 1)[0]

        if not candidate:
            raise ValueError("Browser allowed domain must not be empty.")

        return candidate

    def _validate_url(self, url: str) -> str:
        if not isinstance(url, str) or not url.strip():
            raise ValueError("Browser URL must not be empty.")

        normalized = url.strip()
        parsed = urlparse(normalized)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Browser URL must use http or https.")

        if not parsed.hostname:
            raise ValueError("Browser URL must contain a hostname.")

        if self._allowed_domains:
            hostname = parsed.hostname.casefold()
            if not any(
                hostname == domain
                or hostname.endswith(f".{domain}")
                for domain in self._allowed_domains
            ):
                raise PermissionError(
                    f"Browser domain '{hostname}' is not allowed."
                )

        return normalized

    @staticmethod
    def _validate_target(
        target: BrowserElement,
        *,
        capability: str,
    ) -> None:
        if not isinstance(target, BrowserElement):
            raise TypeError(
                "Browser interaction target must be BrowserElement."
            )

        if not target.label.strip():
            raise ValueError("Browser interaction target must have a label.")

        normalized = target.interaction_capability.strip().upper()

        if normalized != capability:
            raise PermissionError(
                f"Browser target does not have {capability} capability."
            )

        try:
            confidence = float(target.confidence)
        except (TypeError, ValueError):
            raise ValueError("Browser target confidence must be numeric.")

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "Browser target confidence must be between 0 and 1."
            )

        if confidence <= 0.0:
            raise PermissionError(
                "Browser interaction target requires positive confidence."
            )
