param([switch]$ExecuteLive,[ValidateRange(1,30)][int]$MaxSteps=8,[string]$TraceDirectory='')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest tests/test_visual_agent_runtime.py tests/test_visual_agent_progress.py -q
if ($LASTEXITCODE -ne 0) { throw 'Visual tests failed. No API call or GUI input started.' }
$priorLive=$env:COMPUTER_USE_LIVE
try {
    $env:COMPUTER_USE_LIVE='1'
    $runArgs=@('tools/run_visual_agent.py','--max-steps',"$MaxSteps")
    if ($TraceDirectory) { $runArgs+=@('--trace-dir',$TraceDirectory) }
    if ($ExecuteLive) { $runArgs+='--execute-live' }
    python -u @runArgs
    $runExit=$LASTEXITCODE
} finally {
    $env:COMPUTER_USE_LIVE=$priorLive
}
Write-Host "VISUAL_EXIT_CODE=$runExit"
exit $runExit
