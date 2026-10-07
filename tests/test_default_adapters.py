from app.agent.adapters.browser_adapter import BrowserAdapter
from app.agent.adapters.default_adapters import create_default_adapter_registry


def test_default_registry_exposes_core_file_adapters(tmp_path):
    registry = create_default_adapter_registry(
        filesystem_roots=(tmp_path,),
    )

    browser = registry.resolve(
        application="Browser",
        capability="navigate",
    )
    assert isinstance(browser, BrowserAdapter)
    assert browser.descriptor.adapter_id == "browser"
