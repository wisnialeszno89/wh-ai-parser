"""Regression: chat consent guidance and local-only right-click clipboard."""
from pathlib import Path
from app.agent.runtime.navimind_live_conversation import (
    explicit_document_sharing_help_request,
)

ROOT = Path(__file__).resolve().parents[1]


def test_consent_help_direct_and_followup_context():
    assert explicit_document_sharing_help_request(
        "Jak udostępnić zapytanie do analizy?"
    )
    assert explicit_document_sharing_help_request(
        "w jaki sposob sie to robi?",
        "Proszę o udostępnienie AI zatwierdzonego zapytania.",
    )
    assert not explicit_document_sharing_help_request(
        "w jaki sposob sie to robi?",
        "Znalazłem uruchomiony WindowHub.",
    )
    assert not explicit_document_sharing_help_request(
        "przygotuj ofertę", "Proszę o zgodę."
    )


def test_workspace_local_edit_context_menu():
    src = (ROOT / "tools" / "navimind_main_workspace.py").read_text(encoding="utf-8")
    assert "self._install_edit_context_menu(self.entry)" in src
    assert "self._install_edit_context_menu(self.enquiry_editor)" in src
    assert 'widget.event_generate("<<Paste>>")' in src
    assert 'widget.bind("<Button-3>", show)' in src
    assert "document_approval_indicator" in src


def test_host_provides_consent_help_without_granting_access():
    src = (ROOT / "tools" / "run_navimind_shared_control_center.py").read_text(
        encoding="utf-8"
    )
    assert '"document_sharing_help": ReadOnlyTool(' in src
    assert 'live_chat.document_context_active()' in src
    assert '„Przeanalizuj dokument w NaviMind”' in src
    assert 'if live_allowed else' in src
