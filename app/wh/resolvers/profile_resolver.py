from dataclasses import dataclass
from enum import Enum


class ProfileResolutionStatus(Enum):
    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ProfileResolution:
    status: ProfileResolutionStatus
    profile: str | None = None
    matched_alias: str | None = None


class ProfileResolver:

    PROFILES = {
        "veka 82": "VEKA_82",
        "softline 82": "VEKA_82",
        "v82": "VEKA_82",
    }

    PROFILE_MARKERS = (
        "veka",
        "softline",
        "profil",
        "profile",
    )

    def resolve_result(self, text: str) -> ProfileResolution:
        text = text.lower()

        for alias, profile in self.PROFILES.items():
            if alias in text:
                return ProfileResolution(
                    status=ProfileResolutionStatus.RESOLVED,
                    profile=profile,
                    matched_alias=alias,
                )

        if any(marker in text for marker in self.PROFILE_MARKERS):
            return ProfileResolution(
                status=ProfileResolutionStatus.UNKNOWN,
            )

        return ProfileResolution(
            status=ProfileResolutionStatus.NOT_FOUND,
        )

    def resolve(self, text: str) -> str | None:
        result = self.resolve_result(text)

        if result.status == ProfileResolutionStatus.RESOLVED:
            return result.profile

        return None
