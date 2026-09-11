from app.catalog.profiles import PROFILE_CATALOG
from app.context.context_source import ContextSource
from app.context.offer_context import OfferContext
from app.decision.decision_result import DecisionResult
from app.decision.decision_trace import (
    DecisionKind,
    DecisionTrace,
)
from app.wh.resolvers.hardware_resolver import HardwareResolver


class DecisionEngine:

    @staticmethod
    def _trace_kind(
        source: ContextSource,
    ) -> DecisionKind:

        if source == ContextSource.DEFAULT:
            return DecisionKind.DEFAULT

        if source == ContextSource.SALESMAN:
            return DecisionKind.SALESMAN_DECISION

        return DecisionKind.FACT

    def _append_profile_catalog_trace(
        self,
        context: OfferContext,
        trace: list[DecisionTrace],
    ) -> None:

        if context.profile is None:
            return

        profile = PROFILE_CATALOG.get(
            context.profile
        )

        if profile is None:

            trace.append(
                DecisionTrace(
                    field="profile_catalog",
                    value=context.profile,
                    kind=DecisionKind.UNKNOWN,
                    source="catalog",
                    reason="profile not found in catalog",
                )
            )

            return

        trace.append(
            DecisionTrace(
                field="default_frame",
                value=profile.default_frame,
                kind=DecisionKind.DEFAULT,
                source="catalog",
                reason=(
                    f"default frame for profile "
                    f"{profile.code}"
                ),
            )
        )

        trace.append(
            DecisionTrace(
                field="default_glass",
                value=profile.default_glass,
                kind=DecisionKind.DEFAULT,
                source="catalog",
                reason=(
                    f"default glass for profile "
                    f"{profile.code}"
                ),
            )
        )

        trace.append(
            DecisionTrace(
                field="default_hardware",
                value=profile.default_hardware,
                kind=DecisionKind.DEFAULT,
                source="catalog",
                reason=(
                    f"default hardware for profile "
                    f"{profile.code}"
                ),
            )
        )

        hardware = HardwareResolver().resolve(
            profile.default_hardware
        )

        if hardware is None:

            trace.append(
                DecisionTrace(
                    field="hardware_compatibility",
                    value=profile.default_hardware,
                    kind=DecisionKind.UNKNOWN,
                    source="catalog",
                    reason="hardware not found in catalog",
                )
            )

            return

        trace.append(
            DecisionTrace(
                field="hardware_compatibility",
                value=hardware.system,
                kind=DecisionKind.COMPATIBILITY,
                source="catalog",
                reason=(
                    f"hardware {hardware.code} is compatible "
                    f"with profile {profile.code}"
                ),
            )
        )

    def choose_workflow(
        self,
        context: OfferContext,
    ) -> DecisionResult:

        trace: list[DecisionTrace] = []

        if context.profile is not None:

            trace.append(
                DecisionTrace(
                    field="profile",
                    value=context.profile,
                    kind=self._trace_kind(
                        context.profile_source
                    ),
                    source=context.profile_source.value,
                    reason="profile value from context",
                )
            )

        if context.color is not None:

            trace.append(
                DecisionTrace(
                    field="color",
                    value=context.color,
                    kind=self._trace_kind(
                        context.color_source
                    ),
                    source=context.color_source.value,
                    reason="color value from context",
                )
            )

        self._append_profile_catalog_trace(
            context,
            trace,
        )

        if context.manual_review:

            trace.append(
                DecisionTrace(
                    field="manual_review",
                    value="true",
                    kind=DecisionKind.FACT,
                    source="context",
                    reason="manual_review flag",
                )
            )

            return DecisionResult(
                workflow="manual_review",
                confidence=1.0,
                manual_review=True,
                reason="manual_review flag",
                trace=tuple(trace),
            )

        if context.construction_type == "single_window":

            trace.append(
                DecisionTrace(
                    field="construction_type",
                    value="single_window",
                    kind=DecisionKind.FACT,
                    source="context",
                    reason="construction_type=single_window",
                )
            )

            return DecisionResult(
                workflow="single_window",
                confidence=1.0,
                manual_review=False,
                reason="construction_type=single_window",
                trace=tuple(trace),
            )

        trace.append(
            DecisionTrace(
                field="construction_type",
                value=context.construction_type,
                kind=DecisionKind.UNKNOWN,
                source="context",
                reason="unknown construction",
            )
        )

        return DecisionResult(
            workflow="manual_review",
            confidence=0.0,
            manual_review=True,
            reason="unknown construction",
            trace=tuple(trace),
        )