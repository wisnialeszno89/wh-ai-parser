# Universal Digital Worker Architecture

The project is evolving from a WindowHub-specific automation prototype into a
universal desktop worker.

## Core contract

The worker follows this loop:

```
user request
  -> task understanding
  -> capability / skill selection
  -> semantic world
  -> semantic action
  -> target resolution
  -> controlled execution
  -> state verification
  -> memory update
```

Learning follows the same model:

```
human demonstration
  -> semantic BEFORE snapshot
  -> semantic action
  -> semantic AFTER snapshot
  -> compact semantic transition
  -> learned workflow
  -> persistent workflow memory
  -> semantic retrieval
  -> replay through the normal control loop
```

Physical coordinates, window handles, runtime IDs and provider-specific
identifiers are execution details only. They must not become part of learned
workflow data or remote reasoning contracts.

## Current foundation

Already present:

- semantic perception and world representation
- controlled GUI execution and safety gates
- verification and recovery/replanning
- OpenAI and NaviMind reasoning boundaries
- offer/session domain layer
- human teaching mode
- semantic learned workflow replay
- model-safe local/external knowledge envelope
- durable learned workflow repository
- deterministic semantic workflow matcher
- compact BEFORE -> AFTER transition model

## Next vertical milestones

1. Learned skill resolution: matched workflow -> replay service. ✅
2. Semantic text-entry learning from field state changes. ✅
3. Parameterized learned skills for request-time values. ✅
4. Universal desktop adapters: files, Word, Excel, browser and email.
5. Persistent agent memory: sessions, successful experiences and preferences.
6. Remote worker transport: HTTP/WebSocket command and status channel.
7. Controlled external research provider feeding the provenance-aware
   knowledge layer.

WindowHub remains the first demanding application adapter, not the definition
of the worker itself.
