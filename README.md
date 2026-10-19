# wh-ai-parser

## Universal Agent Reasoning

The Universal Agent Core can optionally use an OpenAI-backed
PlanReasoner for verification-driven replanning.

Configuration:

1. Copy .env.example to .env.
2. Set OPENAI_API_KEY.
3. Optionally change AGENT_REASONING_MODEL.
4. Run the provider-only probe:

```powershell
python tools/probe_openai_reasoner.py
```

The probe calls only the reasoning provider. It does not execute
WindowHub, mouse, keyboard or any physical GUI action.

For the end-to-end reasoning -> replanning -> control-loop dry run:

```powershell
python tools/probe_openai_control_loop.py
```

This second probe uses the real OpenAI provider but a fully simulated
environment and semantic-only dry-run executor. It does not touch
WindowHub or perform physical GUI actions. A manual-review response is
also considered a safe outcome: the control loop stops instead of
forcing execution.

Default reasoning model: gpt-5.6-luna.

## Learned skills

The agent can learn human-demonstrated workflows as semantic state
transitions. Learned workflows are persisted outside the source tree by
default in runtime_data/learned_workflows and can be retrieved by a
deterministic semantic matcher.

An exact learned trigger is resolved before generic task planning and then
replayed through the same observation, target-resolution, safety, execution
and verification control loop.

Teaching can also infer text entry from semantic field value changes. The
first text-learning path observes UI state, coalesces rapid changes until the
value is stable, and records a semantic `write_text` action targeted to the
field label. No raw keyboard events, scan codes or clipboard contents are
captured.

The workflow data intentionally excludes coordinates, window handles,
runtime/provider identifiers and other machine-specific execution details.

Semantic text-entry steps are parameterizable. During a new replay, a
WindowHub offer request can override learned field values such as width,
height and quantity while the demonstrated workflow structure remains fixed.
The runtime still requires a high-confidence learned trigger; parameterized
continuation is accepted only when the trigger is the start of the request
and all learned parameters resolve.

## NaviMind remote task reasoning

When NAVIMIND_AGENT_URL is configured, the WindowHub runtime uses
NaviMindTaskReasoner for the initial semantic task proposal.

The execution path is:

observe -> semantic perception -> NaviMind -> local action policy ->
RobotGUIExecutor -> SafetyGate/GUI bridge -> verification -> re-observe

NaviMind receives only semantic world state. Coordinates, window handles,
runtime/provider identifiers and executor internals stay local.

The local runtime and NaviMind server both enforce the same explicit semantic
action allowlist. Unknown remote actions fail closed and require manual review.

WindowHub robot execution is DRY_RUN by default. LIVE hardware execution is
enabled only when WH_REAL_WINDOWHUB=1.

## Structured knowledge context

The NaviMind bridge uses a versioned knowledge envelope:

```text
knowledge
├── version
├── local      # trusted application/runtime knowledge
└── external   # provenance-aware external knowledge
```

External knowledge is represented by facts, sources, confidence, relevance,
conflicts and limitations. It is treated as model input only; it never
expands the local action allowlist or execution permissions.

The current stage adds the contract, validation and transport only. No web
research is executed yet.

### Agent experience memory

The runtime now keeps a durable, model-safe memory of execution outcomes.
Memories contain the application, intent, learned workflow identity, outcome
and compact diagnostics, while raw user requests and machine-specific runtime
identifiers are excluded. Recent experiences can be supplied to task
reasoning as prior context.

## Universal desktop adapters

The Universal Agent now has a semantic application-adapter contract and a
deterministic adapter registry. The current registry includes filesystem,
Word, Excel, email-draft and browser adapters.

The browser adapter exposes semantic navigation and interactions while keeping
provider-specific selectors, coordinates and runtime identifiers local. Browser
providers remain replaceable implementation details. The default browser
adapter is unconfigured and unavailable until a concrete provider is injected.

The adapter layer is separate from GUI perception and execution, so later
desktop-specific controls can reuse the same semantic registry without
becoming WindowHub-specific.

## Generic Windows desktop runtime with NaviMind

The supported generic Windows runtime entry point is
`create_windows_desktop_agent_runtime()` in
`app/agent/runtime/windows_desktop_agent_runtime.py`. It wires the selected
`TaskReasoner` into `AgentOrchestrator(require_task_reasoning=True)` and uses
the existing Windows control loop, local semantic target validation, execution
safety gate and verification path.

Configure the hosted bridge in the local `.env` file (never commit real values):

```dotenv
NAVIMIND_AGENT_URL=https://your-deployment.example/api/agent/task
NAVIMIND_AGENT_SECRET=replace-with-the-same-high-entropy-secret
NAVIMIND_AGENT_TIMEOUT_SECONDS=45
COMPUTER_REAL=0
```

NaviMind is selected whenever `NAVIMIND_AGENT_URL` is present. Its secret is
required; production endpoints must use HTTPS. HTTP is allowed only for
localhost development. If NaviMind is configured but authentication or the
remote call fails, task reasoning stops for manual review; the runtime does
not silently switch to OpenAI. The explicit OpenAI task-reasoning alternative
is `AGENT_TASK_REASONING=1` with `OPENAI_API_KEY`, and is selected only when
the NaviMind URL is absent. Verification-driven OpenAI replanning is separately
opt-in through `AGENT_PLAN_REASONING=1`.

Run a provider-only outbound contract smoke test. It sends synthetic semantic
state and does not observe, click, type into, or otherwise control the desktop:

```powershell
python tools/smoke_windows_desktop_navimind.py
```

Start the generic Windows agent with a natural-language goal:

```powershell
python tools/run_windows_desktop_agent.py --goal "Click the visible Testing tab"
```

Physical GUI execution remains disabled by default. Only set
`COMPUTER_REAL=1` for an explicitly scoped live test. Even in live mode,
NaviMind proposes semantic actions only; local target validation, execution
policy and post-action verification remain authoritative.

