from pathlib import Path
import re


DATASET_DIR = Path(
    "research/semantic_dataset/ru"
)


def parse_filename(name):

    stem = Path(name).stem

    parts = stem.split()

    result = {

        "geometry": None,

        "width_mm": None,

        "height_mm": None,

        "profile": "perfectline",

        "glass": "2glass",

        "color_inside": "white",

        "color_outside": "white"
    }

    if parts:

        result["geometry"] = (
            parts[0]
        )

    size_match = re.search(
        r"(\d+)x(\d+)",
        stem
    )

    if size_match:

        result["width_mm"] = int(
            size_match.group(1)
        )

        result["height_mm"] = int(
            size_match.group(2)
        )

    lower = stem.lower()

    if "sf82" in lower:

        result["profile"] = (
            "softline82"
        )

    if "3szyby" in lower:

        result["glass"] = (
            "3glass"
        )

    if "antra_ws" in lower:

        result["color_outside"] = (
            "anthracite"
        )

        result["color_inside"] = (
            "white"
        )

    if "eiche_ws" in lower:

        result["color_outside"] = (
            "golden_oak"
        )

        result["color_inside"] = (
            "white"
        )

    return result


def main():

    files = sorted(
        DATASET_DIR.glob("*.OFR")
    )

    for f in files:

        parsed = parse_filename(
            f.name
        )

        print("\n================")
        print(f.name)

        for k, v in parsed.items():

            print(
                f"{k}: {v}"
            )


if __name__ == "__main__":

    main()