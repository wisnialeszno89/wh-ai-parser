from dataclasses import dataclass
import os


@dataclass(frozen=True)
class NaviMindConfig:
    """Runtime configuration for the remote NaviMind reasoner."""

    url: str
    secret: str | None = None
    timeout_seconds: float = 30.0
    enabled: bool = True

    @classmethod
    def from_environment(cls) -> "NaviMindConfig | None":
        raw_url = os.getenv("NAVIMIND_AGENT_URL", "").strip()

        if not raw_url:
            return None

        raw_timeout = os.getenv(
            "NAVIMIND_AGENT_TIMEOUT_SEC",
            "30",
        ).strip()

        try:
            timeout = max(
                1.0,
                min(120.0, float(raw_timeout)),
            )
        except ValueError:
            timeout = 30.0

        secret = os.getenv(
            "NAVIMIND_AGENT_SECRET",
            "",
        ).strip() or None

        enabled = os.getenv(
            "NAVIMIND_AGENT_ENABLED",
            "1",
        ).strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }

        return cls(
            url=raw_url,
            secret=secret,
            timeout_seconds=timeout,
            enabled=enabled,
        )
