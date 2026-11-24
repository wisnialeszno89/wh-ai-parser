"""Portable, read-only program capability routing for universal NaviMind.

Discovery is based on facts from a trusted local inventory. Never download,
install or execute programs from a chat message, search result or document.
Installation proposals require explicit human consent and verified publisher.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProgramRoute(str, Enum):
    USE_INSTALLED = "use_installed"
    ASK_TO_INSTALL = "ask_to_install"
    ASK_TO_CHOOSE = "ask_to_choose"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class InstalledProgram:
    program_id: str
    display_name: str
    capabilities: tuple[str, ...]
    installed_verified: bool
    executable_verified: bool
    supports_safe_edit: bool = False
    publisher_verified: bool = False

    def __post_init__(self):
        if not self.program_id.strip() or not self.display_name.strip():
            raise ValueError("program_identity_required")


@dataclass(frozen=True)
class ProgramRequirement:
    capability: str
    prefer_program_id: str | None = None
    requires_editable_output: bool = False

    def __post_init__(self):
        if not self.capability.strip():
            raise ValueError("required_capability_missing")


@dataclass(frozen=True)
class ProgramChoice:
    route: ProgramRoute
    program_id: str | None
    reason: str
    approval_required: bool = False
    auto_installed: bool = False
    app_launched: bool = False


def route_program(
    requirement: ProgramRequirement,
    inventory: tuple[InstalledProgram, ...],
    *, known_trusted_catalog: tuple[InstalledProgram, ...] = (),
) -> ProgramChoice:
    """Select only one verified local program, otherwise ask.

    The catalog supplies suggestions, never installer URLs or downloads.
    A real Windows discovery adapter will feed verified local inventory.
    """
    if len({p.program_id for p in inventory}) != len(inventory):
        raise ValueError("duplicate_inventory_program")
    compatible = [
        p for p in inventory
        if p.installed_verified and p.executable_verified
        and requirement.capability in p.capabilities
        and (not requirement.requires_editable_output or p.supports_safe_edit)
    ]
    if requirement.prefer_program_id:
        exact = [p for p in compatible if p.program_id == requirement.prefer_program_id]
        if len(exact) == 1:
            return ProgramChoice(ProgramRoute.USE_INSTALLED, exact[0].program_id,
                                 "verified_preferred_program")
    if len(compatible) == 1:
        return ProgramChoice(ProgramRoute.USE_INSTALLED, compatible[0].program_id,
                             "unique_verified_local_capability")
    if len(compatible) > 1:
        return ProgramChoice(ProgramRoute.ASK_TO_CHOOSE, None,
                             "multiple_verified_programs_available", approval_required=True)
    trusted = [
        p for p in known_trusted_catalog
        if p.publisher_verified
        and requirement.capability in p.capabilities
        and (not requirement.requires_editable_output or p.supports_safe_edit)
    ]
    if requirement.prefer_program_id:
        trusted = [p for p in trusted if p.program_id == requirement.prefer_program_id]
    if len(trusted) == 1:
        return ProgramChoice(ProgramRoute.ASK_TO_INSTALL, trusted[0].program_id,
                             "program_not_verified_installed_install_requires_user",
                             approval_required=True)
    if len(trusted) > 1:
        return ProgramChoice(ProgramRoute.ASK_TO_CHOOSE, None,
                             "multiple_trusted_install_candidates", approval_required=True)
    return ProgramChoice(ProgramRoute.UNSUPPORTED, None,
                         "no_verified_local_or_trusted_program_route")
