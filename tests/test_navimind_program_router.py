"""Tests for capability discovery and install consent gate."""
import pytest

from app.agent.runtime.navimind_program_router import (
    InstalledProgram, ProgramRequirement, ProgramRoute, route_program,
)


def wh(installed=True):
    return InstalledProgram(
        "windowhub", "WindowHub", ("window_quote", "editable_quote"),
        installed_verified=installed, executable_verified=installed,
        supports_safe_edit=True, publisher_verified=True,
    )


def word():
    return InstalledProgram(
        "word", "Microsoft Word", ("edit_document", "print_document"),
        installed_verified=True, executable_verified=True,
        supports_safe_edit=True, publisher_verified=True,
    )


def test_unique_verified_installed_program_is_selected():
    result = route_program(ProgramRequirement("editable_quote", requires_editable_output=True), (wh(), word()))
    assert result.route == ProgramRoute.USE_INSTALLED
    assert result.program_id == "windowhub"
    assert not result.app_launched


def test_missing_program_can_only_be_proposed_for_installation():
    result = route_program(
        ProgramRequirement("editable_quote"),
        (), known_trusted_catalog=(wh(installed=False),),
    )
    assert result.route == ProgramRoute.ASK_TO_INSTALL
    assert result.approval_required
    assert not result.auto_installed


def test_unverified_publisher_is_not_trusted_install_candidate():
    untrusted = InstalledProgram(
        "unknown-app", "Unknown App", ("edit_document",),
        installed_verified=False, executable_verified=False,
        publisher_verified=False,
    )
    result = route_program(ProgramRequirement("edit_document"), (),
                           known_trusted_catalog=(untrusted,))
    assert result.route == ProgramRoute.UNSUPPORTED


def test_multiple_installed_apps_ask_user_to_choose():
    other = InstalledProgram(
        "writer", "LibreOffice Writer", ("edit_document",),
        installed_verified=True, executable_verified=True,
        supports_safe_edit=True,
    )
    result = route_program(ProgramRequirement("edit_document", requires_editable_output=True),
                           (word(), other))
    assert result.route == ProgramRoute.ASK_TO_CHOOSE
    assert result.approval_required


def test_explicit_preference_resolves_multiple_supported_apps():
    other = InstalledProgram("writer", "LibreOffice Writer",
                             ("edit_document",), True, True, True)
    result = route_program(
        ProgramRequirement("edit_document", prefer_program_id="word"),
        (word(), other),
    )
    assert result.route == ProgramRoute.USE_INSTALLED
    assert result.program_id == "word"


def test_software_not_verified_installed_is_not_launched():
    result = route_program(
        ProgramRequirement("window_quote"),
        (wh(installed=False),),
    )
    assert result.route == ProgramRoute.UNSUPPORTED
    assert not result.app_launched


def test_missing_edit_support_does_not_falsely_match():
    viewer = InstalledProgram("viewer", "PDF Viewer", ("edit_document",),
                              True, True, False)
    assert route_program(
        ProgramRequirement("edit_document", requires_editable_output=True),
        (viewer,),
    ).route == ProgramRoute.UNSUPPORTED


def test_ambiguous_trusted_installers_require_choice_not_autoinstall():
    a = InstalledProgram("a", "A", ("edit_document",), False, False,
                         supports_safe_edit=True, publisher_verified=True)
    b = InstalledProgram("b", "B", ("edit_document",), False, False,
                         supports_safe_edit=True, publisher_verified=True)
    result = route_program(
        ProgramRequirement("edit_document", requires_editable_output=True),
        (), known_trusted_catalog=(a, b),
    )
    assert result.route == ProgramRoute.ASK_TO_CHOOSE
    assert result.approval_required


def test_duplicate_inventory_is_rejected():
    with pytest.raises(ValueError, match="duplicate_inventory_program"):
        route_program(ProgramRequirement("window_quote"), (wh(), wh()))


def test_unknown_capability_fails_closed():
    assert route_program(
        ProgramRequirement("launch_rocket"), (word(), wh())
    ).route == ProgramRoute.UNSUPPORTED
