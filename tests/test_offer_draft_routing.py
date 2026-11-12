from app.agent.offers.offer_draft_routing import CatalogStatus, DraftPosition, route_draft_positions


def test_unsupported_positions_move_to_end_with_blank_price_and_optional_image():
    positions = [
        DraftPosition("A", "Roleta nietypowa", CatalogStatus.UNSUPPORTED, {"model": "source-only"}, "roleta.jpg"),
        DraftPosition("B", "Okno", CatalogStatus.SUPPORTED, {"width_mm": 1070}),
        DraftPosition("C", "Zestaw", CatalogStatus.UNVERIFIED, {"width_mm": 4160}),
        DraftPosition("D", "Okucie", CatalogStatus.UNSUPPORTED, {}),
    ]

    auto, review, manual_with_photo, manual = route_draft_positions(positions)

    assert (auto["reference"], auto["execution"]) == ("B", "configure")
    assert (review["reference"], review["execution"]) == ("C", "review")
    assert manual_with_photo == {
        "reference": "A", "description": "Roleta nietypowa", "execution": "manual",
        "price": None, "image_reference": "roleta.jpg",
    }
    assert manual == {"reference": "D", "description": "Okucie", "execution": "manual", "price": None}


def test_missing_configuration_stays_in_review():
    position = DraftPosition("A", "Okno", CatalogStatus.SUPPORTED, {})

    assert route_draft_positions([position])[0]["execution"] == "review"
