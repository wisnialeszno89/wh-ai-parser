from app.services.construction_matcher import (
    match_construction
)


def test_match_construction_accepts_catalog_id():
    result = match_construction(
        "hst"
    )

    assert result["construction"]["id"] == "hst"
    assert result["score"] == 100


def test_match_construction_accepts_catalog_alias():
    result = match_construction(
        "drzwi przesuwne"
    )

    assert result["construction"]["id"] == "hst"
    assert result["score"] == 100


def test_match_construction_returns_no_match_for_unknown_text():
    result = match_construction(
        "not-a-real-construction"
    )

    assert result["construction"] is None
    assert result["score"] == 0
