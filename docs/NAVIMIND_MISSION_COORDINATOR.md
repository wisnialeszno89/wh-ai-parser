# NaviMind mission coordinator — Codespaces acceptance

The pure coordinator in `app/agent/runtime/navimind_mission_coordinator.py`
combines independently tested quotation routes and portable editor skills.

## Stage 1 — offline planning contract

The coordinator produces **intents, not GUI actions**. All readback flags passed
in must originate from the independently checked local WindowHub adapter.
A real click, paste or price edit has NOT happened when the planner returns an
intent.

Supported intent progression for each position:

1. Verify exact WindowHub offer document and current observation.
2. Choose available quotation representation (catalogue / descriptive
   representative window / text item) and request position creation.
3. Require fresh proof of the created position before preparing description.
4. Require unique, editable, fresh editor target before editing.
5. Require independent description readback before preparing an image.
6. Require user permission and image support before inserting image.
7. Require independent price readback, whether price was typed manually or
   calculated elsewhere. Never invent missing prices.
8. Move to next position only after required fields have verified readbacks.
9. Finish with a review report; no autonomous save, send or production approval.

Warnings about warranty and deviations survive every planned action. A
commercial offer outside manufacturer guidance is allowed with transparent
warnings; it is NOT a production order or automatic approval.

## Stage 2 — Codespaces commands

Use branch `feat/navimind-mission-coordinator-20261124`.

```bash
python -m pytest -q \
  tests/test_navimind_mission_coordinator.py \
  tests/test_portable_editor_skills.py \
  tests/test_windowhub_commercial_quote_routes.py \
  tests/test_navimind_evidence_decision_engine.py \
  tests/test_windowhub_sales_mission_review.py
```

No Windows runtime, local licensed documentation, internet browser or system
clipboard is required.

## Stage 3 — Windows integration gate (not completed)

- Map proposed intents to existing validated V2 capabilities, not raw clicks.
- Read back exact document ID, current position, description and price.
- Establish real image insertion capability and visual/readback confirmation.
- Prove no accidental extra positions, wrong offer edits, auto-save or send.
- Include operator corrections, technical warning and per-position evidence in
  final review without claiming unobserved work.
