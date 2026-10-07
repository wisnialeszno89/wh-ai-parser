from app.agent.adapters.browser_adapter import BrowserAdapter
from app.agent.adapters.default_adapters import create_default_adapter_registry
from app.agent.adapters.email_draft_adapter import EmailDraftAdapter
from app.agent.adapters.excel_workbook_adapter import ExcelWorkbookAdapter
from app.agent.adapters.filesystem_adapter import FileSystemAdapter
from app.agent.adapters.word_document_adapter import WordDocumentAdapter


def test_default_registry_exposes_core_file_adapters(tmp_path):
    registry = create_default_adapter_registry(
        filesystem_roots=(tmp_path,),
    )

    filesystem = registry.resolve(
        application="FileSystem",
        capability="read",
    )
    assert isinstance(filesystem, FileSystemAdapter)

    word = registry.resolve(
        application="Word",
        capability="create",
    )
    assert isinstance(word, WordDocumentAdapter)

    excel = registry.resolve(
        application="Excel",
        capability="write_range",
    )
    assert isinstance(excel, ExcelWorkbookAdapter)

    email = registry.resolve(
        application="Email",
        capability="create_draft",
    )
    assert isinstance(email, EmailDraftAdapter)

    browser = registry.resolve(
        application="Browser",
        capability="navigate",
    )
    # The default provider is intentionally unconfigured, so resolution
    # fails closed until a concrete browser provider is injected.
    assert browser is None
