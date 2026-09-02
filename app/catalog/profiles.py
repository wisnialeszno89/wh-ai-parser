from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileProduct:
    code: str
    name: str
    default_frame: str
    default_glass: str
    default_hardware: str


PROFILE_CATALOG = {
    "VEKA_82": ProfileProduct(
        code="VEKA_82",
        name="VEKA Softline 82 MD",
        default_frame="VEKA82_MD",
        default_glass="PERFECT_48",
        default_hardware="WINKHAUS_PRO",
    ),
}
