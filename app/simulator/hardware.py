from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HardwareSpec:
    """A selectable hardware product in the simulator."""

    product: str
    required_sides: tuple[str, ...] = ("left", "right")


@dataclass
class HardwareState:
    """Runtime hardware selection and installation state."""

    selected: HardwareSpec | None = None
    installed_sides: set[str] = field(default_factory=set)

    @property
    def ready(self) -> bool:
        if self.selected is None:
            return False
        return set(self.selected.required_sides).issubset(self.installed_sides)


@dataclass(frozen=True)
class HardwareReadiness:
    """Deterministic explanation of whether hardware can be installed."""

    ready: bool
    reason: str

    @classmethod
    def evaluate(
        cls,
        *,
        has_frame: bool,
        sash_sides: set[str],
        glass_sides: set[str],
        hardware: HardwareState,
    ) -> "HardwareReadiness":
        if not has_frame:
            return cls(False, "FRAME is required")

        required = {"left", "right"}
        if not required.issubset(sash_sides):
            missing = sorted(required - sash_sides)
            return cls(False, f"SASH sides missing: {', '.join(missing)}")

        if not required.issubset(glass_sides):
            missing = sorted(required - glass_sides)
            return cls(False, f"GLASS sides missing: {', '.join(missing)}")

        if hardware.selected is None:
            return cls(False, "hardware product is not selected")

        missing = set(hardware.selected.required_sides) - hardware.installed_sides
        if missing:
            return cls(False, f"hardware sides missing: {', '.join(sorted(missing))}")

        return cls(True, "hardware is installed on all required sashes")
