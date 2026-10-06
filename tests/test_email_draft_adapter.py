from app.agent.adapters.email_draft_adapter import EmailDraftAdapter


def test_email_draft_adapter_creates_reads_and_attaches_file(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    attachment = root / "oferta.pdf"
    attachment.write_bytes(b"pdf-data")

    adapter = EmailDraftAdapter(
        allowed_roots=(root,),
    )

    path = root / "wiadomosc.eml"
    draft = adapter.create_draft(
        path,
        to=("klient@example.com",),
        cc=("sprzedaz@example.com",),
        subject="Oferta okien",
        body="Dzień dobry, przesyłam ofertę.",
        attachments=(attachment,),
    )

    assert draft.subject == "Oferta okien"
    assert draft.to == ("klient@example.com",)
    assert draft.cc == ("sprzedaz@example.com",)
    assert draft.body == "Dzień dobry, przesyłam ofertę.\n"
    assert draft.attachments == ("oferta.pdf",)

    restored = adapter.read_draft(path)

    assert restored.to == draft.to
    assert restored.cc == draft.cc
    assert restored.subject == draft.subject
    assert restored.body == draft.body
    assert restored.attachments == ("oferta.pdf",)


def test_email_draft_adapter_requires_recipient_and_safe_root(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = EmailDraftAdapter(
        allowed_roots=(root,),
    )

    try:
        adapter.create_draft(
            root / "empty.eml",
            to=(),
            subject="Test",
            body="Treść",
        )
    except ValueError as exc:
        assert "recipient" in str(exc)
    else:
        raise AssertionError("Draft without recipient was accepted.")

    try:
        adapter.exists(tmp_path / "outside.eml")
    except PermissionError:
        pass
    else:
        raise AssertionError("Outside draft path was accepted.")


def test_email_draft_adapter_requires_explicit_overwrite(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    adapter = EmailDraftAdapter(
        allowed_roots=(root,),
    )

    path = root / "test.eml"
    adapter.create_draft(
        path,
        to=("a@example.com",),
        subject="First",
        body="One",
    )

    try:
        adapter.create_draft(
            path,
            to=("b@example.com",),
            subject="Second",
            body="Two",
        )
    except FileExistsError:
        pass
    else:
        raise AssertionError("Existing draft was overwritten.")

    restored = adapter.create_draft(
        path,
        to=("b@example.com",),
        subject="Second",
        body="Two",
        overwrite=True,
    )

    assert restored.to == ("b@example.com",)
    assert restored.subject == "Second"
