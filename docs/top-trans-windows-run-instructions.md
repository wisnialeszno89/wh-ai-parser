# Windows: get the actual branch before running the Top Trans preflight

The earlier command failed from `C:\Users\WisniewskiA\AppData\Local\WindowHub-2e2ae54`,
which is a WindowHub application folder rather than the repository working tree.
**No test executed and the missing-file error does not mean the mission failed.**

Run in PowerShell:

```powershell
$paths = @(
  'E:\wh-ai-parser-navimind-world-model-v2',
  'E:\wh-ai-parser',
  "$HOME\Desktop\wh-ai-parser"
)
$repo = $paths | Where-Object {
  Test-Path (Join-Path $_ '.git') -PathType Any
} | Select-Object -First 1
if (-not $repo) { throw "Nie znaleziono repo. Podaj rzeczywista lokalizacje katalogu wh-ai-parser." }

Set-Location $repo
git status --short
git remote -v
# If the working tree has changes, do not force a checkout or discard them.
git fetch origin feat/navimind-windowhub-decision-policy-20261119

# A separate worktree does not disturb the currently checked-out branch.
$testDir = Join-Path (Split-Path $repo -Parent) 'wh-ai-parser-top-trans-test'
if (Test-Path $testDir) { throw "Folder testowy juz istnieje: $testDir" }
git worktree add --detach $testDir origin/feat/navimind-windowhub-decision-policy-20261119
Set-Location $testDir

python -m pytest tests/test_windowhub_top_trans_enquiry_mission.py tests/test_windowhub_assembly_geometry.py -q
python tools/prepare_windowhub_enquiry_mission.py --out reports/top-trans-preflight.json
```

This is an **offline** check; it cannot create a WindowHub offer or validate
local supplier database choices. Real GUI offer creation still requires a wired,
reviewable NaviMind execution flow. Use only a disposable OFR for acceptance.

**Sizing principle:** catalogue first; respect verified sizes and constraints.
Distinguish a *bare window height* from a *whole window-plus-top-box height*.
If only the bare window is specified, do not subtract a box from it. If a
whole-assembly envelope is specified, choose a catalogue-compatible box and
reconcile the dimensions using its verified size and manufacturer's input
convention. Verify the final overall dimensions in the application's readback.
