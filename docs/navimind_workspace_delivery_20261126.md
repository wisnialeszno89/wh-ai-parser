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

## 2026-11-26: remaining blockers after successful local status check

Latest operator evidence:
- Background UIA reports Start1, one WindowHub window and 47 interactive
  controls. This proves limited structural observation, not editable document
  content, authenticated catalog availability, or input readiness.
- Approved two-window excerpt can be parsed. It is per-session consent; an
  earlier message saying "zatwierdzone" is not a substitute for a current
  session approval.
- "bez dodatkowych opcji, Bez montażu, demontażu i wykończenia" previously
  failed model tool selection. Bounded human correction parser now supports
  this phrase, and coordinator can carry the exclusions across intervening
  read-only status/document questions until another offer request boundary.
- Blocked mission is locally PAUSED with `v2_endpoint_missing`, zero confirmed
  GUI actions and no confirmed saved offer.
- Agent previously suggested that merchant should "approve V2 credentials".
  This conflates IT/server configuration with operator action authorization.
  Host factual status now explains these separately.

Required gates to truly quote in WindowHub:
1. V2 URL and secret configured in the SAME local process, including dotenv.
   Valid remote URLs require HTTPS, or HTTP only for loopback; shared V2
   endpoint uses /api/agent/task. No secrets are committed to Git.
2. Successful endpoint authentication and expected task-response schema.
   URL/secret presence alone does not prove 200; Vercel deployment protection,
   SSO, 401, 403 and rate limiting are distinct possible blockers.
3. Unique user-session WindowHub (Okna.exe) identification; app can be in
   background/minimized for observation but non-interfering UIA observations
   cannot be misrepresented as permission to click background windows.
   Human must log in to password-protected application personally.
4. Verified Start1 -> new offer -> precise customer selection (Top Trans
   Artur Janik / matching record) and exact document scope.
5. Readable verified profile, color, glass and hardware catalog controls;
   two independent constructions and both individual discounts.
6. Operator-enabled LIVE flags and independent local Resume per verified step;
   post-action readback, safe stop, no save/send.

Testing and evidence: automated suite is not an end-to-end GUI acceptance.
Use a test customer and an unsaved disposable offer. If a required field
cannot be read, stop and explain rather than guessing configuration or prices.

## 2026-11-26 follow-up: existing Vercel route and protected production

Connected project inspection (metadata only, no secret values):
- Vercel project `navimind` has READY production deployment. Repo is
  `wisnialeszno89/navimind`; its `POST /api/agent/task` supports V2.
- Production environment *lists* `NAVIMIND_AGENT_SECRET` and `OPENAI_API_KEY`.
  This does not prove runtime authentication or usable service.
- Vercel Deployment Protection SSO is enabled for all deployments.
  A valid NaviMind application secret alone might therefore fail at Vercel
  before reaching the task route. Never disable SSO without explicit approval.
- Exact canonical app endpoint for local test:
  `https://www.navimind.app/api/agent/task`.

New safe local workflow:
1. In a trusted PowerShell session, dot-source
   `. .\\tools\\Initialize-NaviMind-V2Session.ps1`. It sets only the V2
   endpoint and securely prompts for a matching secret if missing. Secrets
   remain in process environment (not checked into Git). If unknown, stop
   instead of inventing a secret; use an explicitly provisioned test credential
   with expiry or an authorized existing production value.
2. `python tools/run_navimind_offer_preflight.py`: inspect dependencies and
   environment presence, not network access.
3. `python tools/check_navimind_v2_connection.py`: send only
   `{"version":"2"}`, a deliberately invalid synthetic V2 contract.
   A server 400 JSON `INVALID_AGENT_TASK_V2` is expected after application
   authentication and provider configuration. Distinguish server-side 401
   UNAUTHORIZED from HTML/Vercel SSO 401/403, and reject redirects.
4. Only after an authenticated synthetic check should the team attempt
   a separate valid V2 protocol reasoning smoke. This still does NOT grant
   permission to click WindowHub or save an offer.

The local app must not claim connectivity from env vars alone. No customer
data, screenshots or native computer input are used in the synthetic probe.

## 2026-11-26 09:32 regression: consent/tool routing and duplicate offers

Observed:
- User explicitly requested a factual explanation of V2 vs operator control
  and whether a construction was created. Agent instead returned document
  approval instructions. Root cause: a substring intent classifier matched
  "jak" inside "jakąkolwiek" and the syllable "zgod" inside a question
  about consent to GUI control.
- The classifier now requires an actual interrogative AND explicit document
  sharing/approval target. GUI control questions route to host-grounded
  mission status. Unit tests cover the exact failing user sentence.
- User requested a fresh WindowHub stage and number of UIA controls, but
  the model sometimes answered only that Okna.exe was running. Explicit
  stage/count requests now use local inspect_windowhub read-only capability,
  and never claim a process inventory is the requested stage observation.
- Repeating identical paused offer requests previously created a new
  mission without the earlier exclusions. New task/revision is still
  required, but its exact matching prior mission carries bounded service
  exclusions across, provided its document consent version is unchanged.
  This never transfers an input permit or GUI progress.

Still blocked: V2 endpoint/secret are not configured on the operator machine.
Next: run the safe V2 synthetic network probe, resolving protected Vercel
access via approved authentication, then a valid non-executing protocol test,
before any GUI Live acceptance. multiple_windows means an ambiguous UIA
scene rather than a proven current offer and must not grant input.

## 2026-11-26: approved-document phrasings and multiple_windows

Fresh user evidence: a request to analyze the "zatwierdzone zapytanie" returned
a generic model claim of missing consent, while a second request to analyze the
"udostępnione zapytanie klienta/PDF" returned two window positions. Background
UIA observed two Okna.exe windows and 35 interactive controls, stage
`multiple_windows`.

Changes:
- Both explicit customer-enquiry analysis wordings now use the SAME
  consent-gated local read-only tool, rather than allowing the model to
  invent the consent state. The tool has one current-session permission epoch.
  If the user has not approved sharing, it requests consent through the
  existing UI; it never silently shares a PDF.
- The background UIA reader now explicitly explains that two verified
  WindowHub HWNDs with an aggregate control count do not uniquely establish
  the correct offer/document or native input scope.
- Regression tests lock both approved and unapproved paths and avoid customer
  data leakage in the UIA summary.
- Two older test assertions referring to an obsolete V2_EXECUTOR_CONNECTED
  LIVE flag were corrected to use the current split LIVE/HTTP readiness label.

Follow-up must prioritize actual V2 connectivity. Local configuration and a
read-only synthetic authenticated V2 probe remain necessary before a valid V2
reasoning smoke, independent of native-control consent.
