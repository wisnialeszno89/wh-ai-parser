# Structured enquiries into NaviMind V2 (first connected planning gate)

The `--sales-mission` flag now loads a validated structured enquiry and
supplies it to every V2 observe/think/act cycle as
`knowledge.active_sales_mission`. It also supplies a concise natural-language
mission goal. The field-level source requirements remain **planned** until
actually observed and verified in WH Okna. This uses the **existing** V2
request contract; no server-side deployment or schema modification is required.

Example mission:
`research/scenarios/top_trans_20261119_4windows.json`.

## Windows commands

From the test worktree created earlier (or a fresh checkout of this PR branch):

```powershell
git fetch origin feat/navimind-windowhub-decision-policy-20261119
git status --short
# On the detached test worktree only, and only if it is clean:
git switch --detach origin/feat/navimind-windowhub-decision-policy-20261119

python -m pytest tests/test_windowhub_sales_mission_v2.py tests/test_windowhub_top_trans_enquiry_mission.py tests/test_windowhub_decision_policy.py tests/test_windowhub_assembly_geometry.py -q

# Read-only local observation: no model request, no clicks
python tools/run_windowhub_goal_v2.py --sales-mission research/scenarios/top_trans_20261119_4windows.json --mode inspect

# Real NaviMind planning request; no UI actions
python tools/run_windowhub_goal_v2.py --sales-mission research/scenarios/top_trans_20261119_4windows.json --mode think --max-actions 1
```

The think call uses the configured NaviMind V2 endpoint and may send the
exact customer name and position details to it; use only an authorized
workspace. Set up `NAVIMIND_AGENT_V2_URL` and
`NAVIMIND_AGENT_V2_SECRET` through the existing environment workflow, never
paste secrets into chat.

## Safety and capability boundaries

- `--mode think` obtains one proposed next action without clicking.
- `--mode inspect` performs local scene inspection. With desktop flags
  enabled it may bring the WindowHub application to foreground.
- The V2 runner's guarded execution mode can act on verified semantic
  controls, but that is **not** proof of full four-window automation.
- Native customer selection, roller-box catalog navigation, multi-position
  progress readback and unsaved handoff are not yet unified with this
  structured mission. These require live acceptance and further integration.
- Never enable production/customer offer mutations for this test.
- The V2 no-save guard currently covers identified semantic buttons but
  alternate menu paths/keyboard shortcuts need an explicit policy audit.
- A reasoning model's response is a proposal, not evidence that a construction
  or business document was created.
