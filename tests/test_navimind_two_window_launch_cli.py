"""The two-window command line stays opt-in and does not click in unit tests."""
import pytest
from tools import run_navimind_shared_control_center as host


def test_two_window_cli_passes_preloaded_local_pdf_to_existing_host(monkeypatch):
    called = {}
    monkeypatch.setattr(host, "run", lambda **kwargs: called.update(kwargs) or 0)
    assert host.main([
        "--new-offer", "--test-two-windows",
        "--pdf", "C:/test/two-positions.pdf",
    ]) == 0
    assert called["expected_offer"] == "DRAFT/NEW"
    assert called["exactly_two_windows"] is True
    assert called["initial_pdf"] == "C:/test/two-positions.pdf"


def test_two_window_cli_rejects_both_sources_and_existing_offer(monkeypatch):
    with pytest.raises(SystemExit):
        host.main([
            "--new-offer", "--pdf", "a.pdf", "--request-file", "a.txt",
        ])
    with pytest.raises(SystemExit):
        host.main([
            "--expected-offer", "OFR/101",
            "--test-two-windows",
        ])


def test_request_file_is_passed_only_to_local_read_only_intake(monkeypatch):
    received = {}
    monkeypatch.setattr(host, "run", lambda **kwargs: received.update(kwargs) or 0)
    assert host.main([
        "--new-offer", "--test-two-windows",
        "--request-file", "C:/test/positions.txt",
    ]) == 0
    assert received["initial_request_file"] == "C:/test/positions.txt"
    assert received["initial_pdf"] is None


def test_automatic_start_is_explicit_and_allowed_only_for_new_draft(monkeypatch):
    called = {}
    monkeypatch.setattr(host, "run", lambda **kwargs: called.update(kwargs) or 0)
    assert host.main(["--new-offer", "--auto-start-draft"]) == 0
    assert called["auto_start_draft"] is True
    assert host.main(["--new-offer"]) == 0
    assert called["auto_start_draft"] is False
    with pytest.raises(SystemExit):
        host.main(["--expected-offer", "OFR/101", "--auto-start-draft"])
