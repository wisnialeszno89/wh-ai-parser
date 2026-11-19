# NaviMind → WH Okna: decision loop and remaining acceptance work (2026-11-19)

## Current evidence and boundary

This branch is based on `fix/windowhub-verified-mdi-sibling` / PR #192, **not main**.
The repository already has native UIA/Win32 observations, MDI ownership guards, window
selection, wizard navigation, a fixed-glazing and single-sash builder, UR ACTIVPILOT
selection, pricing readback, seller policy, de-identified demonstrations, and
partial-position reports. These are separate paths rather than a proven end-to-end
general-purpose agent. Test counts are not live sales acceptance.

References:
- [WH Okna manufacturer's public documentation](https://whokna.com.pl/wp-content/uploads/2026/01/Instrukcja_WHOkna_v7_styczen26.pdf)
- [WH Okna knowledge base](https://whokna.com.pl/baza-wiedzy/)
- [Winkhaus product overview](https://www.winkhaus.pl/pl/serwis/WH-OKNA)
- Existing evidence catalogue: `knowledge/whokna_public_reference_v1.json`

## Target operating contract

1. Convert a salesperson's enquiry (text, drawing, PDF) into source-traceable
   per-position requirements, including *explicit*, *missing*, and *derived* values.
   Do not promote OCR guesswork to exact technical details.
2. Observe current screen, identify foreground process, owner HWND, active MDI
   document, dialog and selected position; resume an existing authorized offer
   when possible instead of reopening from Start1.
3. Distinguish existing customer lookup from a typed-but-uncommitted suggestion
   and from new-customer creation; only committed readback counts.
4. For each position, compare field intents with actual dealer catalogues.
   If an explicit requested profile, color, fitting, glazing or opening is
   unavailable, do not replace it silently. Seek a compatible alternative
   *only when the salesperson approved substitution*.
5. Default **only unspecified** attributes: white on both sides when neither
   side was specified; two panes when glazing is unspecified; 0% discount
   without a salesperson instruction; UR ACTIVPILOT for a verified compatible
   standard tilt-turn selection, not for every opening type.
6. Execute one fresh-scoped action; reobserve, verify field value and
   geometry, and classify success, uncertainty, or failure. An unknown result
   must never trigger a blind duplicate click.
7. Where possible, keep a position with verified dimensions as a clearly
   incomplete placeholder and proceed. Never call it a finished construction.
   If the UI does not support placeholder creation, ask instead of fabricating
   a saved position.
8. Distinguish the discount and markup fields from VAT. Confirm pricing only
   against an owned dialog with fresh readback. Do not submit, send, order or
   convert an offer to production without explicit human authorization.
9. Produce a structured final report: exact customer, verified positions,
   incomplete positions, assumed defaults, unavailable requirements, open
   questions, pricing evidence, save/readback state.
10. On a new situation, ask for one targeted teaching demonstration, store
    de-identified semantic steps, replay on disposable data, verify results,
    and only then graduate a learned rule to a reusable skill.

## What this branch actually changes

- `app/agent/knowledge/windowhub_decision_policy.py`: pure field choice and
  placeholder fallback policy with mandatory evidence and non-silent defaults.
- `app/agent/learning/windowhub_training_context.py`: exposes this contract
  to the NaviMind V2 knowledge object.
- `tests/test_windowhub_decision_policy.py`: covers evidence, required
  fields, missing catalogue options and safe partial paths.

This **does not yet** connect `decide_field` to the native action executor,
does not expand the V2 API contract, and does not demonstrate a live completed offer.
Knowledge injection informs reasoning; the native execution guard must enforce it.

## Next integration milestones (in order)

A. Unify the intake schema and `SalesPosition` with native field-level evidence;
   record `requested`, `defaulted`, `observed`, `applied`, `readback` separately.
B. Connect the common planner to customer lookup, wizard steps, drawing editor,
   hardware picker and pricing. Remove hard-coded assumptions in specialized
   scripts only after parity tests.
C. Build a semantic catalogue capability map from actual installed dealer data,
   including profile/sash compatibility, glazing and fittings. Version by local
   supplier DB and app build; avoid shipping customer data or licensed data.
D. Add supervised learning: demonstration → candidate rule → disposable
   regression → approved rule with provenance/version/revocation.
E. Add a bounded recoverable goal loop: inspect unknown dialog, identify owner,
   choose allowable option, handle incomplete position, continue other positions.
F. Add an end-to-end Windows acceptance: existing customer, two varied positions,
   one unavailable requested option, 0% default discount, nonzero instructed
   discount, interruption/restart, and verified final draft. Reject any run that
   conflates operator confirmation with machine readback.

## Questions requiring operator knowledge

- Which profiles/systems, colors, glazing catalogue labels and opening codes
  exist in *your* dealer database? Manufacturer docs do not prove availability.
- May the agent select a technically compatible alternative to an explicitly
  requested item, or only leave a placeholder and report the conflict?
- Is the permitted final action **save draft offer only**, and may an unsaved
  incomplete position be left on screen when the program does not support a
  true blank position?
- Which screen/step currently fails in the full real WindowHub run? Provide a
  screenshot and log; no need to rerun previously passed isolated tests.

## Regression command (pure policy)

```powershell
python -m pytest tests/test_windowhub_decision_policy.py -q
```

Run Windows native acceptance only against a disposable OFR with explicit operator
authorization and the appropriate `COMPUTER_USE_LIVE`/`WH_REAL_WINDOWHUB` gates.


## Operator decisions — 2026-11-19 (supersede earlier questions)

- The agent autonomously pursues the nearest **technically verified, functionally
  suitable, live-available** substitute. It records exact original value,
  substitute, and deviation for the salesperson. Mere textual similarity is not
  technical compatibility.
- When no valid substitute exists, the agent keeps a **dimensioned unfinished
  position** where the editor truly supports it; otherwise it records a blocker.
- The agent does **not SAVE** the offer before salesperson review, corrections
  and approval. It leaves the offer on screen, reports work performed and
  remaining gaps, and awaits salesperson intervention.
- NaviMind combines current program observation, public WH Okna documentation
  and guarded native actions. Web information must never be interpreted as a
  guarantee of an option's availability in a particular dealer database.
- Conversation and learning should avoid repetitive questions; request
  demonstrations only for a genuine missing capability, then verify against
  disposable test data before retaining a skill.

## Implementation extension in this branch

- `windowhub_decision_policy.py` ranks only verified alternative candidates
  and marks substitutions for mandatory human review.
- `windowhub_goal_v2_coordinator.py` rejects recognized save/send/order
  conversion buttons, even if generic persistence approval is set.
- `windowhub_salesperson_policy.py` records substitutions and emits a
  salesperson-review-required report with `agent_save_performed=false`.
- `run_windowhub_autonomous_offer.py` prints this review report at exit.

**Limitations:** The candidate alternative catalog is not yet wired to a real
supplier-native discovery driver. The no-save action guard covers identified
semantic buttons but not every possible menu shortcut or other executor path;
these require an explicit allowlist audit before any unsupervised live trial.
No Windows end-to-end successful offer has been demonstrated by this branch.

Pure regression candidates:

```powershell
python -m pytest tests/test_windowhub_decision_policy.py tests/test_windowhub_goal_v2_coordinator.py -q
```
