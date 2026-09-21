from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CSV_PATH = Path("research/gui_lab/candidate_atlas.csv")
SOURCE_PATH = Path("samples/wh_screen.png")
OUTPUT_PATH = Path("research/gui_lab/interactive_atlas.png")

CELL_W = 180
CELL_H = 150
PADDING = 8
CROP_PADDING = 12
COLUMNS = 6


def main() -> None:
    source = Image.open(SOURCE_PATH).convert("RGB")
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))

    rows = [
        row
        for row in rows
        if row["structural_type"] == "UNKNOWN"
        and 15 <= int(row["width"]) <= 300
        and 15 <= int(row["height"]) <= 150
        and int(row["children"]) <= 2
    ]

    rows.sort(key=lambda row: int(row["id"]))

    rows_per_page = COLUMNS
    count = len(rows)
    grid_rows = (count + COLUMNS - 1) // COLUMNS

    atlas_w = COLUMNS * (CELL_W + PADDING) + PADDING
    atlas_h = grid_rows * (CELL_H + PADDING) + PADDING

    atlas = Image.new("RGB", (atlas_w, atlas_h), "white")
    draw = ImageDraw.Draw(atlas)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
        small_font = ImageFont.truetype("DejaVuSans.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
        small_font = font

    for index, row in enumerate(rows):
        col = index % COLUMNS
        grid_row = index // COLUMNS

        cell_x = PADDING + col * (CELL_W + PADDING)
        cell_y = PADDING + grid_row * (CELL_H + PADDING)

        x = int(row["x"])
        y = int(row["y"])
        w = int(row["width"])
        h = int(row["height"])

        left = max(0, x - CROP_PADDING)
        top = max(0, y - CROP_PADDING)
        right = min(source.width, x + w + CROP_PADDING)
        bottom = min(source.height, y + h + CROP_PADDING)

        crop = source.crop((left, top, right, bottom))
        crop.thumbnail((CELL_W - 16, CELL_H - 42))

        crop_x = cell_x + (CELL_W - crop.width) // 2
        crop_y = cell_y + 28

        draw.rectangle(
            [cell_x, cell_y, cell_x + CELL_W, cell_y + CELL_H],
            outline="black",
            width=1,
        )

        draw.text(
            (cell_x + 5, cell_y + 5),
            f'ID {row["id"]}',
            fill="black",
            font=font,
        )

        draw.text(
            (cell_x + 55, cell_y + 7),
            f'{w}x{h}',
            fill="black",
            font=small_font,
        )

        atlas.paste(crop, (crop_x, crop_y))

        draw.rectangle(
            [
                crop_x + (x - left),
                crop_y + (y - top),
                crop_x + (x - left) + w,
                crop_y + (y - top) + h,
            ],
            outline="red",
            width=2,
        )

    atlas.save(OUTPUT_PATH)

    print(f"selected: {count}")
    print(f"atlas: {OUTPUT_PATH}")
    print(f"size: {atlas.size[0]}x{atlas.size[1]}")


if __name__ == "__main__":
    main()
