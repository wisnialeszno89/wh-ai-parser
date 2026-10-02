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
