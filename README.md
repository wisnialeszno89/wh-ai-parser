# wh-ai-parser

## Universal Agent Reasoning

The Universal Agent Core can optionally use an OpenAI-backed
`PlanReasoner` for verification-driven replanning.

Configuration:

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY`.
3. Optionally change `AGENT_REASONING_MODEL`.
4. Run the provider-only probe:

```powershell
python tools/probe_openai_reasoner.py
```

The probe calls only the reasoning provider. It does not execute
WindowHub, mouse, keyboard or any physical GUI action.

For the end-to-end reasoning → replanning → control-loop dry run:

```powershell
python tools/probe_openai_control_loop.py
```

This second probe uses the real OpenAI provider but a fully simulated
environment and semantic-only dry-run executor. It does not touch
WindowHub or perform physical GUI actions. A manual-review response is
also considered a safe outcome: the control loop stops instead of
forcing execution.

Default reasoning model: `gpt-5.6-luna`.

## NaviMind remote task reasoning

When `NAVIMIND_AGENT_URL` is configured, the WindowHub runtime uses
`NaviMindTaskReasoner` for the initial semantic task proposal.

The execution path is:

`observe -> semantic perception -> NaviMind -> local action policy ->
RobotGUIExecutor -> SafetyGate/GUI bridge -> verification -> re-observe`

NaviMind receives only semantic world state. Coordinates, window handles,
runtime/provider identifiers and executor internals stay local.

The local runtime and NaviMind server both enforce the same explicit semantic
action allowlist. Unknown remote actions fail closed and require manual review.

WindowHub robot execution is DRY_RUN by default. LIVE hardware execution is
enabled only when `WH_REAL_WINDOWHUB=1`.



## Structured knowledge context

The NaviMind bridge uses a versioned knowledge envelope:

```text
knowledge
├── version
├── local      # trusted application/runtime knowledge
└── external   # provenance-aware external knowledge
```

External knowledge is represented by facts, sources, confidence, relevance,
conflicts and limitations. It is treated as model input only; it never expands
the local action allowlist or execution permissions.

The current stage adds the contract, validation and transport only. No web
research is executed yet.


## Universal Windows desktop computer use (V2)

The application-neutral Windows runtime observes the active foreground window.
It combines Windows UI Automation with OCR text extraction when Tesseract is
installed. OCR is evidence about visible text only: OCR-only labels are not
clickable and do not grant action permissions.

Python package:

```powershell
python -m pip install -r requirements.txt
```

The OCR provider also requires the Tesseract OCR executable. Install Tesseract
for Windows and make sure `tesseract.exe` is on PATH, or set `TESSERACT_CMD`
to its full path. Set `COMPUTER_USE_OCR_LANG` to an installed language set
such as `deu+eng` when German and English trained data are available. The
default language is `eng`. If Tesseract is absent or fails, the provider
records a diagnostic and the UI Automation path continues.

The V2 desktop runtime requires `NAVIMIND_AGENT_V2_URL` and optionally
`NAVIMIND_AGENT_V2_SECRET`. It defaults to DRY_RUN. Real mouse and keyboard
input requires the explicit `COMPUTER_USE_LIVE=1` opt-in.

This is the first generic Windows foreground-window stage; it does not yet
enumerate every desktop window, taskbar control or every application surface.
