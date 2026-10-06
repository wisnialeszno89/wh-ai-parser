from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class AdapterDescriptor:
    """
    Model-safe description of one application/environment adapter.

    Descriptors contain only semantic capabilities. They never expose window
    handles, coordinates, process ids or provider-specific runtime objects.
    """

    adapter_id: str
    application: str
    capabilities: tuple[str, ...] = ()
    description: str = ""

    def to_payload(self) -> dict[str, object]:
        return {
            "adapter_id": self.adapter_id,
            "application": self.application,
            "capabilities": self.capabilities,
            "description": self.description,
        }


class ApplicationAdapter(ABC):
    """
    Universal semantic adapter contract for one application/domain.

    Observation belongs to EnvironmentAdapter. This interface describes the
    additional application-level operations that a Universal Digital Worker
    can safely use without knowing platform-specific UI details.
    """

    @property
    @abstractmethod
    def descriptor(self) -> AdapterDescriptor:
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether this adapter can currently service requests."""
        raise NotImplementedError

    def supports(self, capability: str) -> bool:
        return capability.strip().casefold() in {
            item.strip().casefold()
            for item in self.descriptor.capabilities
        }

    def metadata(self) -> Mapping[str, object]:
        return self.descriptor.to_payload()
