from app.agent.adapters.default_adapters import (
    create_default_adapter_registry,
)
from app.agent.adapters.filesystem_adapter import FileSystemAdapter
from app.agent.adapters.word_document_adapter import (
    WordDocumentAdapter,
)


def test_default_registry_exposes_filesystem_and_word_adapters(tmp_path):
    registry = create_default_adapter_registry(
        filesystem_roots=(tmp_path,),
    )

    assert isinstance(
        registry.resolve(
            application="FileSystem",
            capability="read",
        ),
        FileSystemAdapter,
    )

    word = registry.resolve(
        application="Word",
        capability="create",
    )

    assert isinstance(word, WordDocumentAdapter)
    assert word.descriptor.adapter_id == "word_document"
