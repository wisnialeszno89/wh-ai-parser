from app.context.offer_context import OfferContext
from app.context.context_source import ContextSource
from app.context.context_source import ContextSource
from app.decision.decision_engine import DecisionEngine
from app.decision.decision_trace import DecisionKind


def test_single_window():

    context = OfferContext()

    context.construction_type = (
        "single_window"
    )

    result = (
        DecisionEngine()
        .choose_workflow(
            context
        )
    )

    assert result.workflow == "single_window"

    assert result.manual_review is False

    assert result.confidence == 1.0

def test_single_window_has_decision_trace():
    context = OfferContext()
    context.construction_type = "single_window"

    result = DecisionEngine().choose_workflow(context)

    assert len(result.trace) == 1
    trace = result.trace[0]

    assert trace.field == "construction_type"
    assert trace.value == "single_window"
    assert trace.kind.value == "fact"
    assert trace.source == "context"


def test_manual_review_has_decision_trace():
    context = OfferContext()
    context.manual_review = True

    result = DecisionEngine().choose_workflow(context)

    assert len(result.trace) == 1
    trace = result.trace[0]

    assert trace.field == "manual_review"
    assert trace.value == "true"
    assert trace.kind.value == "fact"
    assert trace.source == "context"


def test_unknown_construction_has_unknown_trace():
    context = OfferContext()
    context.construction_type = "something_unknown"

    result = DecisionEngine().choose_workflow(context)

    assert result.manual_review is True
    assert len(result.trace) == 1

    trace = result.trace[0]

    assert trace.field == "construction_type"
    assert trace.value == "something_unknown"
    assert trace.kind.value == "unknown"
    assert trace.source == "context"


def test_profile_from_pdf_can_be_traced():
    context = OfferContext()
    context.construction_type = "single_window"
    context.profile = "VEKA_82"
    context.profile_source = ContextSource.PDF

    result = DecisionEngine().choose_workflow(context)

    assert result.workflow == "single_window"

    profile_trace = next(
        trace for trace in result.trace
        if trace.field == "profile"
    )

    assert profile_trace.value == "VEKA_82"
    assert profile_trace.kind.value == "fact"
    assert profile_trace.source == "PDF"


def test_profile_from_pdf_can_be_traced():
    context = OfferContext()
    context.construction_type = "single_window"
    context.profile = "VEKA_82"
    context.profile_source = ContextSource.PDF

    result = DecisionEngine().choose_workflow(context)

    assert result.workflow == "single_window"

    profile_trace = next(
        trace for trace in result.trace
        if trace.field == "profile"
    )

    assert profile_trace.value == "VEKA_82"
    assert profile_trace.kind.value == "fact"
    assert profile_trace.source == "PDF"


def test_profile_from_default_is_traced_as_default():
    context = OfferContext()
    context.construction_type = "single_window"
    context.profile = "VEKA_82"
    context.profile_source = ContextSource.DEFAULT

    result = DecisionEngine().choose_workflow(context)

    profile_trace = next(
        trace for trace in result.trace
        if trace.field == "profile"
    )

    assert profile_trace.value == "VEKA_82"
    assert profile_trace.kind.value == "default"
    assert profile_trace.source == "DEFAULT"


def test_profile_from_salesman_is_traced_as_salesman_decision():
    context = OfferContext()
    context.construction_type = "single_window"
    context.profile = "VEKA_82"
    context.profile_source = ContextSource.SALESMAN

    result = DecisionEngine().choose_workflow(context)

    profile_trace = next(
        trace for trace in result.trace
        if trace.field == "profile"
    )

    assert profile_trace.value == "VEKA_82"
    assert profile_trace.kind.value == "salesman_decision"
    assert profile_trace.source == "SALESMAN"


def test_color_from_pdf_is_traced_as_fact():
    context = OfferContext()
    context.construction_type = "single_window"
    context.color = "white"
    context.color_source = ContextSource.PDF

    result = DecisionEngine().choose_workflow(context)

    color_trace = next(
        trace for trace in result.trace
        if trace.field == "color"
    )

    assert color_trace.value == "white"
    assert color_trace.kind.value == "fact"
    assert color_trace.source == "PDF"
def test_profile_catalog_provides_default_hardware_trace():
    context = OfferContext()
    context.construction_type = "single_window"
    context.profile = "VEKA_82"
    context.profile_source = ContextSource.PDF

    result = DecisionEngine().choose_workflow(context)

    default_hardware_trace = next(
        trace
        for trace in result.trace
        if trace.field == "default_hardware"
    )

    assert default_hardware_trace.value == "WINKHAUS_PRO"
    assert default_hardware_trace.kind == DecisionKind.DEFAULT
    assert default_hardware_trace.source == "catalog"

    compatibility_trace = next(
        trace
        for trace in result.trace
        if trace.field == "hardware_compatibility"
    )

    assert compatibility_trace.value == "activPilot Concept"
    assert compatibility_trace.kind == DecisionKind.COMPATIBILITY
    assert compatibility_trace.source == "catalog"

def test_profile_catalog_provides_default_components():
    context = OfferContext()
    context.construction_type = "single_window"
    context.profile = "VEKA_82"
    context.profile_source = ContextSource.PDF

    result = DecisionEngine().choose_workflow(context)

    frame_trace = next(
        trace
        for trace in result.trace
        if trace.field == "default_frame"
    )

    assert frame_trace.value == "VEKA82_MD"
    assert frame_trace.kind == DecisionKind.DEFAULT
    assert frame_trace.source == "catalog"

    glass_trace = next(
        trace
        for trace in result.trace
        if trace.field == "default_glass"
    )

    assert glass_trace.value == "PERFECT_48"
    assert glass_trace.kind == DecisionKind.DEFAULT
    assert glass_trace.source == "catalog"

    hardware_trace = next(
        trace
        for trace in result.trace
        if trace.field == "default_hardware"
    )

    assert hardware_trace.value == "WINKHAUS_PRO"
    assert hardware_trace.kind == DecisionKind.DEFAULT
    assert hardware_trace.source == "catalog"
