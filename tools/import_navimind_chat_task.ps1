# Import the latest explicitly downloaded NaviMind chat task into WindowHub.
# INSPECT is read-only. THINK calls the configured model and can incur API cost.
# Execution is intentionally not offered through this handoff helper.
[CmdletBinding()]
param(
    [ValidateSet("inspect", "think")]
    [string]$Mode = "inspect",
    [string]$TaskFile = "",
    [switch]$AllowModelRequest
)

$ErrorActionPreference = "Stop"
$project = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $project

if ($Mode -eq "think" -and -not $AllowModelRequest) {
    throw "MODEL_APPROVAL_REQUIRED: Run with -AllowModelRequest to permit one possibly billed NaviMind reasoning request."
}

if ([string]::IsNullOrWhiteSpace($TaskFile)) {
    $downloadFolder = Join-Path $env:USERPROFILE "Downloads"
    $latest = Get-ChildItem -LiteralPath $downloadFolder -Filter "navimind-agent-task*.txt" -File -ErrorAction Stop |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($null -eq $latest) {
        throw "TASK_NOT_FOUND: Download navimind-agent-task.txt from the NaviMind chat card first."
    }
    $task = $latest
} else {
    $task = Get-Item -LiteralPath $TaskFile -ErrorAction Stop
}

if ($task.Extension.ToLowerInvariant() -ne ".txt" -or $task.Length -gt 48000 -or $task.Length -lt 4) {
    throw "TASK_INVALID: Only a nonempty, bounded .txt task is accepted."
}

Write-Host "TASK_SELECTED=$($task.Name)"
Write-Host "TASK_MODE=$Mode"
Write-Host "TASK_EXECUTION=DISABLED"
Write-Host "NOTE=Keep WindowHub in the foreground for inspection and decision planning."

$cmdArgs = @("tools/run_windowhub_goal_v2.py", "--mode", $Mode, "--task-file", $task.FullName)
$demoPath = Join-Path $project "outputs\agent_learning"
$demo = Get-ChildItem -LiteralPath $demoPath -Filter "windowhub-demo-*.jsonl" -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($null -ne $demo) {
    $cmdArgs += @("--demo", $demo.FullName)
}

& python @cmdArgs
if ($LASTEXITCODE -ne 0) {
    throw "WINDOWHUB_TASK_CHECK_FAILED: Exit code $LASTEXITCODE. No execution was requested."
}

Write-Host "TASK_HANDOFF_CHECK=PASS"
Write-Host "NEXT=Review the model decision and local safeguards before trying any real actions."
