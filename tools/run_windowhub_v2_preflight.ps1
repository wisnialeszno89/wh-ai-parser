# WindowHub / NaviMind V2 preflight. No HTTP and NO mouse/keyboard actions.
# Designed for the user's Windows Python environment (no admin/Node needed).
[CmdletBinding()]
param(
    [switch]$SkipTests
)
$ErrorActionPreference = "Stop"
$project = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $project

function Invoke-PythonStep {
    param([string]$Title, [string[]]$Arguments)
    Write-Host ""
    Write-Host "=== $Title ==="
    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Title failed (exit code $LASTEXITCODE). Further steps skipped."
    }
}

Write-Host "WINDOWHUB_V2_PREFLIGHT=LOCAL_ONLY"
Write-Host "NOTE=No NaviMind requests and no live WindowHub action will be performed."

if (-not $SkipTests) {
    Invoke-PythonStep -Title "V2 protocol contract tests" -Arguments @(
        "-m", "pytest",
        "tests/test_navimind_v2_offline_smoke.py",
        "tests/test_navimind_v2_server_probe.py",
        "tests/test_windowhub_chat_task_intake.py",
        "tests/test_navimind_setup_diagnostic.py",
        "tests/test_windowhub_navimind_config.py",
        "tests/test_windowhub_goal_v2_coordinator.py",
        "tests/test_windowhub_demonstration_learning.py",
        "tests/test_windowhub_demo_report.py",
        "-q"
    )
}
Invoke-PythonStep -Title "V2 synthetic semantic roundtrip" -Arguments @("tools/smoke_navimind_v2_offline.py")
Invoke-PythonStep -Title "NaviMind configuration (values redacted)" -Arguments @("tools/diagnose_navimind_setup.py")

$demoDir = Join-Path $project "outputs\agent_learning"
$latest = Get-ChildItem -LiteralPath $demoDir -Filter "windowhub-demo-*.jsonl" -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($null -ne $latest) {
    Invoke-PythonStep -Title "Human demonstration coverage" -Arguments @(
        "tools/report_windowhub_demonstration.py",
        "--demo",
        $latest.FullName
    )
} else {
    Write-Host "DEMO_REPORT=No local demonstration file; existing demo is optional."
}

Write-Host ""
Write-Host "PREFLIGHT_STATUS=LOCAL_CHECKS_PASSED"
Write-Host "REMOTE_REASONING_STATUS=NOT_TESTED"
Write-Host "NEXT=V2 remote reasoning requires deployed NaviMind PR #26 and a configured authenticated /api/agent/task URL."
Write-Host "SECURITY=Do not copy local .env secrets or tokens into chat."
