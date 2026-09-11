from app.agent.capabilities.capability import Capability
from app.agent.capabilities.capability_registry import (
    CapabilityRegistry,
)
from app.agent.capabilities.default_capabilities import (
    create_default_capability_registry,
)


def test_registry_resolves_registered_capability():
    capability = Capability(
        name="TEST",
        description="Test capability",
    )

    registry = CapabilityRegistry(
        capabilities=(capability,)
    )

    resolved = registry.resolve("TEST")

    assert resolved == capability


def test_registry_returns_none_for_unknown_capability():
    registry = CapabilityRegistry()

    assert registry.resolve("UNKNOWN") is None


def test_registry_supports_registered_capability():
    registry = CapabilityRegistry(
        capabilities=(
            Capability(
                name="EXCEL",
                description="Excel",
            ),
        )
    )

    assert registry.supports("EXCEL") is True
    assert registry.supports("WORD") is False


def test_default_registry_contains_core_capabilities():
    registry = (
        create_default_capability_registry()
    )

    assert registry.supports("WH_WINDOW")
    assert registry.supports("EXCEL")
    assert registry.supports("WORD")


def test_registry_lists_all_capabilities():
    registry = (
        create_default_capability_registry()
    )

    names = {
        capability.name
        for capability in registry.all()
    }

    assert names == {
        "WH_WINDOW",
        "EXCEL",
        "WORD",
    }
