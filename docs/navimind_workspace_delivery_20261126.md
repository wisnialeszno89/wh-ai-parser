# NaviMind workspace: verified improvements and next acceptance gates (2026-11-26)

This file records incremental work in the active feature branch. Claims about
real WindowHub behavior require a local Windows acceptance run; unit tests alone
do not demonstrate desktop execution.

## Current verified user feedback

- Chat provider answers and can parse the approved two-window request.
- Background inventory can discover WindowHub (Okna.exe) without focusing it.
- The work planner reports `v2_endpoint_missing` when the native task
  reasoning endpoint is not configured. Chat provider credentials are NOT a
  replacement for a V2 task endpoint.
- A short correction such as "bez montażu, demontażu i wykończenia" is recognized
  and the immediately following new mission carries those service exclusions.
- Consent for local PDF/text is per session, explicitly approved by the
  operator. Its absence must never be inferred away from earlier model text.
- Native GUI control is disabled by default; no save/send permission.

## Changes from the 2026-11-26 feedback

- Chat history is a read-only Tk Text widget. Right mouse button now exposes
  Copy selection, Copy latest agent answer and Select entire conversation.
  There is also a direct Copy latest agent answer button.
- Explicit factual mission-status questions are sent to a host-owned,
  read-only tool that reports WindowHub discovery, local enquiry consent,
  current mission stage, confirmed native actions, V2 config presence and
  live-input constraints. Model-only generic narratives are not acceptable
  substitutes for this status.
- Service-exclusion acknowledgement wording clearly lists excluded services
  without the grammatical error "bez montaż".
- A regression suite protects the above behavior.

## Next work: actual operation

1. Verify latest tests and Tk mouse-copy behavior on operator Windows.
2. Configure and validate a real V2 endpoint and secret locally; keep secrets
   out of Git and chat logs. Verify actual HTTP handshake separately from
   environment-variable presence.
3. Implement safe session-recovery for non-sensitive mission constraints and
   explicit consent re-check for customer data after restart.
4. Expand human correction merging from service exclusions to customer,
   profile, glazing, color, hardware and discount fields with conflict detection.
5. Confirm safe UIA observation on minimized/background WindowHub. Some native
   input needs foreground focus after the operator resumes; fail closed when
   identity, ownership or state cannot be proved.
6. Perform supervised WindowHub Start1 -> New offer -> Customer -> two positions
   acceptance; do not save or send. Validate each business field with readback.

## Operator restart workflow

- Update feature branch with `git pull --ff-only`.
- Run the relevant `pytest` suite.
- Start panel via `tools/Start-NaviMind-TwoWindows.ps1` using
  `examples/navimind_two_window_smoke.txt` in planning mode.
- Explicitly review and share the local document once per session.
- Test discovery, document read, service correction, offer planning/status
  and right-click copying of an agent reply.

## Feedback: mission disappears from status after V2 blocker

The operator confirmed actual output: both positions parsed, service exclusions
acknowledged, WindowHub discovered and `v2_endpoint_missing` correctly reported,
but the next status call reported no registered mission. Cause: the host returned
a configuration blocker before `WorkMissionCoordinator.queue_current()`.

The host now registers the current human quote mission, immediately transitions
it to PAUSED with the allowlisted reason, and reports zero verified GUI actions.
A later status question is itself a new mission revision: the status tool may
describe the previous PAUSED mission but MUST label it stale/non-executable.
No old authorization carries over and neither blocked mission nor status
can cause native input.

Acceptance checks:
- Request quote with approved 2-window enquiry, V2 endpoint unset: report
  locally registered PAUSED mission with `v2_endpoint_missing`.
- Ask factual mission status: show previous PAUSED mission and mark it
  stale because the status request changed revision.
- GUI actions remain zero; offer remains unsaved.
- Verify the real V2 endpoint connection separately before enabling LIVE.
