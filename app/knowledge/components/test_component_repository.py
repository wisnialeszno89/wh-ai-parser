from app.knowledge.components.component_repository import ComponentRepository


def test_loads_veka82_component():
    repository = ComponentRepository()

    component = repository.get_by_profile("VEKA82")

    assert component is not None
    assert component.profile == "VEKA82"
    assert component.default_frame == "VEKA82_MD"
    assert component.default_glass == "PERFECT_48"
    assert component.default_hardware == "WINKHAUS_PRO"


def test_unknown_component_returns_none():
    repository = ComponentRepository()

    assert repository.get_by_profile("UNKNOWN") is None
