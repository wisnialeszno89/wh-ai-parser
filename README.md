# WH AI Parser

This repository contains the local perception, validation, execution and verification runtime for the Windows desktop agent.

## NaviMind semantic bridge

The optional NaviMind bridge moves high-level reasoning to the deployed NaviMind service while keeping environment-specific execution local.

Flow:

`observe -> perceive -> NaviMind -> semantic action -> local execute -> re-observe`

The bridge contract deliberately excludes screen coordinates, window handles, AutomationId/runtime IDs and provider-specific low-level identifiers.

Set these variables only in the local environment:

```env
NAVIMIND_AGENT_ENABLED=1
NAVIMIND_AGENT_URL=https://navimind.vercel.app/api/agent/task
NAVIMIND_AGENT_TIMEOUT_SEC=30
# NAVIMIND_AGENT_SECRET=
```

The production URL may be replaced with another NaviMind deployment URL.

The bridge is opt-in. Existing local execution remains unchanged unless the NaviMind loop is explicitly created by the runtime integration.
