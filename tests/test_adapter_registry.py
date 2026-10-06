from app.agent.adapters.adapter_registry import AdapterRegistry
from app.agent.adapters.application_adapter import (
    AdapterDescriptor,
    ApplicationAdapter,
)


class FakeAdapter(ApplicationAdapter):
    def __init__(self, adapter_id, application, capabilities=()):
        self._descriptor = AdapterDescriptor(
            adapter_id=adapter_id,
            application=application,
            capabilities=capabilities,
        )

    @property
    def descriptor(self):
        return self._descriptor

    def is_available(self):
        return True


def test_registry_resolves_by_application_and_capability():
    registry = AdapterRegistry(
        adapters=(
            FakeAdapter(
                "word-main",
                "Word",
                ("read", "write"),
            ),
            FakeAdapter(
                "excel-main",
                "Excel",
                ("read", "write"),
            ),
        )
    )

    adapter = registry.resolve(
        application="Word",
        capability="write",
    )

    assert adapter is not None
    assert adapter.descriptor.adapter_id == "word-main"


def test_registry_fails_closed_on_ambiguous_best_match():
    registry = AdapterRegistry(
        adapters=(
            FakeAdapter(
                "word-a",
                "Word",
                ("read",),
            ),
            FakeAdapter(
                "word-b",
                "Word",
                ("read",),
            ),
        )
    )

    assert registry.resolve(
        application="Word",
        capability="read",
    ) is None


def test_registry_rejects_duplicate_adapter_ids():
    adapter = FakeAdapter("same", "Word")
    registry = AdapterRegistry(adapters=(adapter,))

    try:
        registry.register(FakeAdapter("same", "Excel"))
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("Duplicate adapter id was accepted.")


def test_registry_ignores_unavailable_adapters():
    class Unavailable(FakeAdapter):
        def is_available(self):
            return False

    registry = AdapterRegistry(
        adapters=(Unavailable("word", "Word", ("read",)),)
    )

    assert registry.resolve(
        application="Word",
        capability="read",
    ) is None
