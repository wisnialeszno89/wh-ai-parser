from dataclasses import dataclass
from enum import Enum

from app.catalog.profiles import DEFAULT_PROFILE, PROFILE_CATALOG
from app.wh.resolvers.profile_resolver import (
    ProfileResolutionStatus,
    ProfileResolver,
)


class ProfileSelectionSource(Enum):
    EXPLICIT = "EXPLICIT"
    DEFAULT = "DEFAULT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ProfileSelection:
    profile: str | None
    source: ProfileSelectionSource
    reason: str


class ProfileSelectionResolver:
    """
    Resolve the profile used by the offer workflow.

    An explicitly provided profile always takes precedence.
    When no profile is provided, the configured default profile
    is used.

    An explicitly mentioned but unknown profile must never silently
    fall back to the default profile.
    """


    def __init__(
        self,
        profile_resolver: ProfileResolver | None = None,
        default_profile: str | None = None,
    ) -> None:
        self.profile_resolver = (
            profile_resolver
            if profile_resolver is not None
            else ProfileResolver()
        )

        self.default_profile = (
            default_profile
            if default_profile is not None
            else DEFAULT_PROFILE
        )

        if self.default_profile not in PROFILE_CATALOG:
            raise ValueError(
                f"Unknown default profile: {self.default_profile}"
            )

    def resolve(
        self,
        text: str,
    ) -> ProfileSelection:
        result = self.profile_resolver.resolve_result(text)

        if result.status == ProfileResolutionStatus.RESOLVED:
            return ProfileSelection(
                profile=result.profile,
                source=ProfileSelectionSource.EXPLICIT,
                reason="Profile explicitly provided in request.",
            )

        if result.status == ProfileResolutionStatus.UNKNOWN:
            return ProfileSelection(
                profile=None,
                source=ProfileSelectionSource.UNKNOWN,
                reason="Profile was mentioned but could not be resolved.",
            )

        return ProfileSelection(
            profile=self.default_profile,
            source=ProfileSelectionSource.DEFAULT,
            reason="No profile provided; default profile selected.",
        )
