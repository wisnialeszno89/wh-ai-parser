# NaviMind Agent Observe/Act V2 — Python bridge

## Scope

`NaviMindTaskReasonerV2` is a separate HTTP client for the versioned
`POST /api/agent/task` endpoint. It shares the existing V1 connection settings
but does not inherit from or translate into the V1 `TaskReasoner` contract.

The client accepts either an `AgentTaskV2Contract` or a mapping containing its
serialized payload. It validates the request locally, sends one bounded JSON
request, then validates the returned V2 decision against the exact request.

## Configuration

The client reuses the existing settings:

- `NAVIMIND_AGENT_URL`
- `NAVIMIND_AGENT_SECRET`
- `NAVIMIND_AGENT_TIMEOUT_SECONDS`

No new secret or endpoint is required. The shared secret is sent only in the
`x-navimind-agent-secret` header when configured. The response body is capped
at 64 KiB; request size is constrained by the V2 contract (256 KiB).

## Responsibility boundary

The client only transports and validates a V2 decision. It does not resolve
semantic references, access UI Automation, execute an action, or verify a
postcondition. Those responsibilities remain in the local runtime.

The current WindowHub V2 observation session exposes only a bounded
`ui_structure` read capability. Its grid reader returns structural metadata
and does not read table cells, headers, customer names, or offer values.
A V2 `act` decision is rejected unless a matching action capability was
explicitly included in that request; no V1 action is used as a fallback.

## Failure behavior

Invalid requests, HTTP/network failures, oversized or malformed responses,
version/task mismatches, stale world revisions, and unexposed capabilities
return `None` and set `last_error`. A response is returned only after the
Python V2 response validator accepts its complete shape and its references
against the submitted request.

## Current stage

This is the transport and contract-validation layer, not an end-to-end V2
runtime. The V1 runtime remains the existing default path. The V2 client is
not yet installed as a runtime selector, and there is no live WindowHub
smoke test until a structure-only perception path can avoid customer data.

## Validation coverage

The targeted bridge CI covers the existing V1 bridge tests and the isolated
V2 client tests for request validation, authentication headers, bounded
response reads, HTTP/network failures, task correlation, current-revision
checks, and capability-bound observation decisions.
