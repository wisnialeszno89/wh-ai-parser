"""Static acceptance for planning startup and scrollable customer documents.

The planning UI must still launch when the exact WindowHub executable cannot
be located. Native live mode continues to require a verified local process.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_planning_launcher_does_not_require_a_named_okna_process():
    source = (ROOT / "tools" / "Start-NaviMind-TwoWindows.ps1").read_text(
        encoding="utf-8-sig"
    )
    assert 'if ($Live) {' in source
    assert 'LIVE wymaga jednoznacznego Okna.exe' in source
    assert 'Uruchamiam rozmowe i obserwacje bez klikniec' in source
    assert 'configure_navimind_chat --setup-gateway' in source


def test_customer_document_editor_has_scrollbar_and_native_scroll():
    source = (ROOT / "tools" / "navimind_main_workspace.py").read_text(
        encoding="utf-8"
    )
    assert 'self.enquiry_scrollbar = tk.Scrollbar(' in source
    assert 'yscrollcommand=self.enquiry_scrollbar.set' in source
    assert 'command=self.enquiry_editor.yview' in source
    assert 'self.enquiry_editor.pack(side="left", fill="both", expand=True)' in source
