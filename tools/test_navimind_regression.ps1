param(
    [switch]$InstallDependencies,
    [switch]$Headless,
    [string]$OutputDirectory = '',
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$labPython = Join-Path $repoRoot '.venv-offer-lab\Scripts\python.exe'
if (-not $OutputDirectory) {
    $desktop = [Environment]::GetFolderPath('Desktop')
    if (-not $desktop) { throw 'Pass -OutputDirectory for a writable report directory.' }
    $OutputDirectory = Join-Path $desktop 'NaviMind-Praca\Testy-agenta'
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
$priorUtf8 = $env:PYTHONUTF8
$priorEncoding = $env:PYTHONIOENCODING
Push-Location $repoRoot
try {
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    $offerArguments = @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'test_window_offer_pipeline.ps1'),'-OutputDirectory',$OutputDirectory)
    if ($InstallDependencies) { $offerArguments += '-InstallDependencies' }
    if ($Python) { $offerArguments += @('-Python',$Python) }
    & powershell @offerArguments
    if ($LASTEXITCODE -ne 0) { throw 'Offer regression failed; browser suite was not started.' }
    if ($InstallDependencies) {
        & $labPython -m playwright install chromium
        if ($LASTEXITCODE -ne 0) { throw 'Chromium installation failed.' }
    }
    & $labPython -m pytest tests/test_navimind_browser.py -q
    if ($LASTEXITCODE -ne 0) { throw 'Browser executor contracts failed.' }
    $browserArguments = @('tools/test_navimind_browser_suite.py','--execute-live','--report-directory',$OutputDirectory)
    if ($Headless) { $browserArguments += '--headless' }
    & $labPython @browserArguments
    if ($LASTEXITCODE -ne 0) { throw 'Chromium regression failed.' }
    Write-Host 'NAVIMIND_REGRESSION=passed REAL_MODEL=False PUBLIC_FORM=False'
} finally {
    $env:PYTHONUTF8 = $priorUtf8
    $env:PYTHONIOENCODING = $priorEncoding
    Pop-Location
}
