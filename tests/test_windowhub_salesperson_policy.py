"""Offline contract tests: planning is not proof of desktop execution."""
import unittest

from app.agent.offers.windowhub_salesperson_policy import (
    EntryRoute, OfferProgress, PositionResult, PositionStatus,
    SalesPosition, plan_position, route_from_stage,
)


class SalespersonPolicyTests(unittest.TestCase):
    def test_defaults_are_explicit(self):
        item = plan_position(SalesPosition(1500, 1400))
        self.assertEqual((item.color_inside, item.color_outside), ("biały", "biały"))
        self.assertEqual(item.glazing_panes, 2)
        self.assertIsNone(item.opening)
        self.assertTrue(item.needs_opening_selection)
        self.assertEqual(len(item.assumptions), 3)

    def test_explicit_specs_are_preserved(self):
        item = plan_position(SalesPosition(
            990, 2120, color_inside="biały", color_outside="antracyt",
            glazing_panes=3, opening="DL",
        ))
        self.assertEqual(item.color_outside, "antracyt")
        self.assertEqual(item.glazing_panes, 3)
        self.assertEqual(item.opening, "DL")
        self.assertEqual(item.assumptions, ())

    def test_single_sided_color_is_assumption(self):
        item = plan_position(SalesPosition(1500, 1400, color_outside="RAL 7016"))
        self.assertEqual(item.color_inside, "RAL 7016")
        self.assertIn("color_inside_matches_outside_assumed", item.assumptions)

    def test_rejects_impossible_dimensions(self):
        with self.assertRaises(ValueError):
            SalesPosition(0, 1400)
        with self.assertRaises(ValueError):
            SalesPosition(1500, 1400, glazing_panes=1)

    def test_unknown_environment_never_clicked_automatically(self):
        self.assertEqual(route_from_stage(None), EntryRoute.ACTIVATE_WINDOWHUB)
        self.assertEqual(route_from_stage("start"), EntryRoute.CREATE_OFFER)
        self.assertEqual(route_from_stage("windowhub_unmapped"), EntryRoute.INSPECT_UNKNOWN_STAGE)

    def test_existing_document_requires_authorization(self):
        self.assertEqual(route_from_stage("modifier"), EntryRoute.VERIFY_DOCUMENT)
        self.assertEqual(
            route_from_stage("modifier", existing_offer_authorized=True),
            EntryRoute.CONTINUE_EDITOR,
        )
        self.assertEqual(
            route_from_stage("glazing", existing_offer_authorized=True),
            EntryRoute.CONTINUE_POSITION,
        )

    def test_partial_requires_verified_placeholder(self):
        with self.assertRaises(ValueError):
            PositionResult(index=1, status=PositionStatus.PARTIAL, dimensions_verified=True)
        with self.assertRaises(ValueError):
            PositionResult(index=1, status=PositionStatus.COMPLETE)

    def test_continue_after_partial(self):
        progress = OfferProgress(customer_verified=True)
        progress.record(PositionResult(
            1, PositionStatus.PARTIAL,
            dimensions_verified=True, draft_placeholder_verified=True,
            missing=("profile_system",), assumptions=("two_pane_glazing_default",),
        ))
        self.assertEqual(progress.next_position_index(3), 2)
        progress.record(PositionResult(2, PositionStatus.BLOCKED, note="No valid catalog option"))
        self.assertEqual(progress.next_position_index(3), 3)
        report = progress.report()
        self.assertEqual(report["partial_count"], 1)
        self.assertEqual(report["blocked_count"], 1)
        self.assertFalse(report["draft_saved_verified"])
        self.assertEqual(report["positions"][0]["missing"], ["profile_system"])

    def test_no_duplicated_progress(self):
        progress = OfferProgress()
        progress.record(PositionResult(1, PositionStatus.PENDING))
        with self.assertRaises(ValueError):
            progress.record(PositionResult(1, PositionStatus.PENDING))


if __name__ == "__main__":
    unittest.main()
