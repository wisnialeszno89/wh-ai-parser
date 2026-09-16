from app.knowledge.openings.opening_knowledge_resolver import (
    OpeningKnowledgeResolver,
)


def test_resolves_polish_alias():
    resolver = OpeningKnowledgeResolver()

    assert (
        resolver.resolve("DKR")
        == "RIGHT_TILT_TURN"
    )


def test_resolves_german_alias():
    resolver = OpeningKnowledgeResolver()

    assert (
        resolver.resolve("Dreh-Kipp Rechts")
        == "RIGHT_TILT_TURN"
    )


def test_resolves_english_alias():
    resolver = OpeningKnowledgeResolver()

    assert (
        resolver.resolve("right tilt and turn")
        == "RIGHT_TILT_TURN"
    )


def test_resolves_left_alias():
    resolver = OpeningKnowledgeResolver()

    assert (
        resolver.resolve("DKL")
        == "LEFT_TILT_TURN"
    )


def test_does_not_guess_ambiguous_opening():
    resolver = OpeningKnowledgeResolver()

    assert resolver.resolve("Dreh-Kipp") is None


def test_unknown_opening_returns_none():
    resolver = OpeningKnowledgeResolver()

    assert resolver.resolve("something unknown") is None
