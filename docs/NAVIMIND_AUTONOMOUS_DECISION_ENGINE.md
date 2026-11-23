# NaviMind autonomous decision engine — architecture, 2026-11-23

NaviMind is not a fixed macro or a general model with unrestricted access to a desktop.

## Execution cycle

1. **Understand** the salesperson's goal and requirements (source: the user's
   request, enquiry PDF, drawing or approved prior decision).
2. **Retrieve** knowledge from allowed local Winkhaus program documentation,
   verified demonstrations, the installed catalogue and optionally public web.
   Maintain provenance. Never treat a third-party webpage as a manufacturer
   approval or as a fact about the customer's local WindowHub installation.
3. **Observe** fresh WindowHub UIA scene and, where UIA lacks controls, bounded
   native inspection/OCR.
4. **Propose** one next action grounded in the goal and currently exposed controls.
   The reasoner is allowed to rank multiple eligible actions, rather than choosing
   the first control seen or following a hardcoded screen path.
5. **Validate** target uniqueness, actual document identity, field semantics,
   absence of side effects, source provenance and attempted-action history.
6. **Execute** through the existing WindowHub V2 local executor, never through
   model-supplied coordinates or direct model-produced native handles.
7. **Verify** the business postcondition by independent application readback.
   The absence of an observation is *unknown*, not success.
8. **Recover** by collecting new evidence / choosing an alternative, with
   bounded no-progress retries. Ask for human guidance only on genuine ambiguity.
9. **Report** requested versus observed values, substitutions and unresolved
   questions. Keep quotation unsaved and unsent until a salesperson explicitly
   reviews and approves business persistence.

## Source hierarchy and limits

- Customer enquiry defines requested requirements, but not supplier availability.
- Current WindowHub observation can verify what is shown/selected; a click is not
  proof of persisted customer association.
- Winkhaus manuals explain program capabilities and manufacturer rules only for
  the documented version/configuration; supplier installation must corroborate
  live catalogue compatibility.
- Curated local rules require recorded scope, provenance and regression tests.
- Public web is supplemental explanatory data, never an execution command.
- AI inference proposes hypotheses and actions, not verified business facts.

## Implemented this branch

- `app/agent/reasoning/navimind_evidence_decision_engine.py`: typed, pure
  observe/consult/act/ask/stop/complete planner and model-proposal verifier.
- `tests/test_navimind_evidence_decision_engine.py`: offline safety/recovery tests.
- `app/agent/learning/windowhub_training_context.py`: source hierarchy and
  decision-engine contract exposed to the current V2 knowledge payload.

## Not yet implemented

- The new pure decision module is not yet bound to the live V2 executor.
- No autonomous web browser or unbounded internet retrieval has been enabled.
- No Winkhaus licensed manual has been retrieved or ingested by this branch.
- The model cannot authorize save, send, or order conversion.
- Before production, add a source registry with version, license, excerpt scopes
  and retrieval tests, then adapt a sanitized action proposal into the new
  verifier and run both offline and supervised live acceptance tests.

## Acceptance gates

1. Offline tests for source provenance, evidence gaps, stale UI, duplicate
   actions, ambiguous targets, model ranking and unsaved-document guarantees.
2. V2 contract tests and no-regression check of current WindowHub actions.
3. Supervised WindowHub live test on a separate draft, with explicit review
   and checked field readback.
