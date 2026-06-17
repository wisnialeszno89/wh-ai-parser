import re

import cv2
import pytesseract

from app.core.extractors.dimensions.detect_dimension_regions import (
    detect_dimension_regions
)


def is_dimension_text(text: str):

    text = text.strip()

    if not text:

        return False

    digits = re.sub(
        r"[^0-9]",
        "",
        text
    )

    if len(digits) < 3:

        return False

    if len(digits) > 5:

        return False

    return True


def clean_dimension_text(text: str):

    digits = re.sub(
        r"[^0-9]",
        "",
        text
    )

    return digits


def prepare_crop_for_ocr(crop):

    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2GRAY
    )

    padded = cv2.copyMakeBorder(

        gray,

        20,
        20,
        20,
        20,

        cv2.BORDER_CONSTANT,

        value=255
    )

    _, thresh = cv2.threshold(

        padded,

        150,

        255,

        cv2.THRESH_BINARY
    )

    return thresh


def rotate_if_vertical(crop):

    h, w = crop.shape[:2]

    if h > w:

        crop = cv2.rotate(

            crop,

            cv2.ROTATE_90_CLOCKWISE
        )

    return crop


def ocr_dimensions(image_path: str):

    image = cv2.imread(
        image_path
    )

    regions = detect_dimension_regions(
        image_path
    )

    results = []

    for region in regions:

        x, y, w, h = region

        crop = image[
            y:y+h,
            x:x+w
        ]

        crop = rotate_if_vertical(
            crop
        )

        crop = prepare_crop_for_ocr(
            crop
        )

        text = pytesseract.image_to_string(

            crop,

            config="--psm 7 digits"
        )

        text = text.strip()

        if not is_dimension_text(
            text
        ):

            continue

        cleaned = clean_dimension_text(
            text
        )

        results.append({

            "text": cleaned,

            "x": x,
            "y": y,
            "w": w,
            "h": h
        })

    return results