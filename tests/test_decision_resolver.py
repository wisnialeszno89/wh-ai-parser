from app.context.context_source import ContextSource
from app.decision.decision_override import DecisionOverride
from app.decision.decision_resolver import DecisionResolver


def test_base_value_is_used_without_override():

    result = DecisionResolver().resolve(
        field="glass",
        value="PERFECT_48",
        source=ContextSource.DEFAULT,
        reason="default glass from profile catalog",
    )

    assert result.field == "glass"
    assert result.value == "PERFECT_48"
    assert result.source == ContextSource.DEFAULT


def test_salesman_override_replaces_base_value():

    override = DecisionOverride(
        field="glass",
        value="6/16/6/16/6",
        reason="price requested VSG configuration using WH equivalent",
    )

    result = DecisionResolver().resolve(
        field="glass",
        value="VSG 44.4/16/4/16/6",
        source=ContextSource.CUSTOMER,
        reason="requested by customer",
        overrides=[override],
    )

    assert result.value == "6/16/6/16/6"
    assert result.source == ContextSource.SALESMAN
    assert result.reason == (
        "price requested VSG configuration using WH equivalent"
    )


def test_override_only_affects_matching_field():

    override = DecisionOverride(
        field="glass",
        value="6/16/6/16/6",
        reason="WH pricing equivalent",
    )

    result = DecisionResolver().resolve(
        field="color",
        value="white",
        source=ContextSource.CUSTOMER,
        reason="requested by customer",
        overrides=[override],
    )

    assert result.field == "color"
    assert result.value == "white"
    assert result.source == ContextSource.CUSTOMER


def test_last_override_wins_for_same_field():

    overrides = [
        DecisionOverride(
            field="glass",
            value="4/16/4/16/4",
            reason="first salesman instruction",
        ),
        DecisionOverride(
            field="glass",
            value="6/16/6/16/6",
            reason="latest salesman instruction",
        ),
    ]

    result = DecisionResolver().resolve(
        field="glass",
        value="PERFECT_48",
        source=ContextSource.DEFAULT,
        reason="default glass",
        overrides=overrides,
    )

    assert result.value == "6/16/6/16/6"
    assert result.source == ContextSource.SALESMAN
    assert result.reason == "latest salesman instruction"
