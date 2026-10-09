# NaviMind + Universal Agent: Integration Roadmap

Status date: 2026-10-09

## North star

A user can leave a supported Windows application open and say:
- "Create a quote from these PDF instructions."
- "Build an annual X/Y table using the approved folder of monthly datasets."

The agent reads local sources, grounds facts with provenance, asks about critical ambiguity, acts through a local safety-controlled runtime, verifies the result, and reports what it actually completed.

## Repository boundaries

- `wisnialeszno89/navimind`: hosted Next.js semantic reasoning bridge; validates a request and proposes at most one semantic action / done / manual review. It must not receive arbitrary machine access or become the physical executor.
- `wisnialeszno89/wh-ai-parser`: local Windows runtime, filesystem/document/data adapters, local source access, UIA/vision, local action policy, execution, verification and audit trail.
- The desktop runtime initiates outbound HTTPS requests to the hosted endpoint. Do not open an inbound port or port-forward to the PC.
- GitHub source visibility and deployment visibility are different. The repo is currently public, so assume every committed file can be read by anyone. Keep credentials, customer PDFs, confidential price tables, real datasets and local paths out of commits. Private repos can be used if the source must not be public, but privacy settings must be changed explicitly in GitHub settings.
- A public endpoint must be authenticated. Production must fail closed if `NAVIMIND_AGENT_SECRET` is missing. Only minimized, provenance-preserving facts/excerpts should go to the hosted model; source files remain local by default.

## Verified today

- PR #57 Computer Foundation merged.
- PR #58 Universal Windows Computer Core merged.
- Live controlled E2E clicked the visible `Testing` tab, observed the resulting state and completed.
- NaviMind `POST /api/agent/task` route exists.
- Local filesystem adapter has explicitly allowed roots.
- Local adapter registry and initial document/Office/browser adapter concepts exist; availability of a semantic adapter does not by itself prove the complete end-to-end workflow works.
- The PDF-to-WindowHub offer path and Excel annual-X/Y path are not yet fully verified.

## End-to-end contract

Each iteration follows:

1. Local request intake stores task ID and user goal.
2. Local source broker resolves approved paths/files and enforces file/size/root limits.
3. Local parsers produce typed facts with provenance (file alias, page/sheet/table/row, extraction method, confidence and limitations).
4. Deterministic domain validators normalize units, enforce required fields/rules, and find conflicts.
5. If a critical fact is missing, conflicting or lacks an authoritative calculation/price rule, pause and ask the user.
6. Local runtime observes current application state and sends a minimized semantic world + task goal + validated facts to NaviMind.
7. NaviMind returns exactly one next semantic action, done, or manual_review.
8. Local policy checks action name, target visibility, requested-target consistency, capability, foreground window, budgets and approval requirements.
9. Local runtime executes one action, observes again and independently verifies the expected state change.
10. Persist a resumable step record and audit metadata; continue until verified completion or a safe stop.
11. Report inputs/sources, output path, completed steps, caveats and unresolved items.

## Work packages (issues)

### wh-ai-parser
- #59 Epic: end-to-end PDF instructions to verified WindowHub quote
- #60 Local PDF ingestion with provenance
- #61 Typed quote facts and deterministic source-backed validation
- #62 Resumable task state and verified multi-step WindowHub draft workflow
- #63 Deterministic Excel/CSV annual X-Y aggregation with verified output

### navimind
- #17 Epic: harden NaviMind desktop-agent bridge for production task orchestration
- #18 Secure `/api/agent/task` and add contract parity tests
- #19 Security/deployment checklist

## Milestones

### M1 — Contract + endpoint security
- Share a JSON Schema/fixture defining request and response in both repos.
- Protect deployed endpoint, bounded payload, bounded world/evidence arrays, request timeout and reasoning budget.
- Ensure one-action continue / zero-action done / manual_review contract.
- CI compares action policy against local allowlist.

### M2 — Local document intake
- PDF text/page parser with strict size/page/text caps.
- Detect scans/empty extraction and report OCR needed explicitly.
- Preserve page provenance through the whole reasoning context.
- Later extend to DOCX/XLSX/CSV and OCR only when justified.

### M3 — Quote facts and validation
- Derive the actual WindowHub required fields and workflow from existing code / confirmed live screens.
- Build typed fact model, unit normalization, conflict detection, required-field validation.
- Use existing authoritative prices/rules; never infer price from model prose.
- Block GUI execution while required facts are unresolved.

### M4 — WindowHub draft
- Dry-run state-machine workflow with per-step postconditions.
- A controlled live run creates/fills a test draft only.
- Explicit approval before final quote submission or sending externally.
- Independently verify final values.

### M5 — Excel annual X/Y
- Approved input folder + explicit X/Y/date/aggregation mapping.
- Deterministic XLSX/CSV reading, monthly merge and annual calculation.
- New output workbook by default, reopened and validated.
- UI automation only where needed for the open application.

### M6 — Broaden desktop capability
- Keyboard commands, select, navigation, scroll, drag/drop and visual fallback added one capability at a time with test+policy+verification.
- Improve telemetry so E2E records actual semantic target, executor path, executed flag and verification evidence.
- Never equate successful dispatch/click with successful task completion.

## Environment setup checklist

### Local runtime
- `OPENAI_API_KEY` or the configured NaviMind bridge credentials; never commit either.
- `NAVIMIND_AGENT_URL=https://<your-deployment>/api/agent/task` when remote reasoning is used.
- `NAVIMIND_AGENT_SECRET` configured in the local runtime and the deployment, with identical high-entropy value.
- Explicit allowlisted roots (e.g. a dedicated test-data folder) rather than an unrestricted home directory.
- `COMPUTER_REAL=0` / dry-run by default; enable live mode only for an explicitly scoped test.
- Synthetic PDF and dataset fixtures checked into tests, never real customer materials.

### NaviMind deployment
- Deploy Next.js to a HTTPS host (e.g. Vercel or another chosen host).
- Set `OPENAI_API_KEY`, `NAVIMIND_AGENT_SECRET`, and model configuration in host environment settings.
- Fail deployment/health-check if production secret is missing.
- No inbound tunnel/desktop listening port required.
- Test authenticated endpoint with a synthetic task; do not place secret in URL, source code, client bundle or logs.

### GitHub hygiene
- Never commit `.env`, API keys, secret values, customer PDFs, price lists or machine-specific paths.
- Use GitHub Actions to run each repo's unit/contract tests and build.
- Put real test outputs and deployment values in local environment/secret manager, not issue comments.
- Public source repositories mean committed code and fixtures are public; use synthetic, non-sensitive fixtures.

## Go-live acceptance gate

Do not call the workflow complete until:
- Contract parity and endpoint auth tests pass.
- PDF fact extraction includes accurate source page evidence.
- Missing/conflicting quote facts lead to review.
- Simulated WindowHub task finishes with verified end state.
- Controlled live draft E2E passes.
- Excel annual X/Y fixture produces exact expected values.
- Both repositories' CI/builds pass.
