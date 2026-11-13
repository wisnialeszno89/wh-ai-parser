param(
    [switch]$InstallDependencies,
    [switch]$ExecuteLive,
    [switch]$KeepOpen,
    [string]$SpecificationFile = '',
    [string]$OutputDirectory = '',
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if ($KeepOpen -and -not $ExecuteLive) { throw '-KeepOpen requires -ExecuteLive.' }

$repoRoot = Split-Path $PSScriptRoot -Parent
$labEnvironment = Join-Path $repoRoot '.venv-offer-lab'
$labPython = Join-Path $labEnvironment 'Scripts\python.exe'
if ($SpecificationFile) {
    $SpecificationFile = (Resolve-Path -LiteralPath $SpecificationFile).Path
}
if (-not $OutputDirectory) {
    $desktop = [Environment]::GetFolderPath('Desktop')
    if (-not $desktop) { throw 'Pass -OutputDirectory for a writable report directory.' }
    $OutputDirectory = Join-Path $desktop 'NaviMind-Praca\Testy-ofert'
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)

$priorUtf8 = $env:PYTHONUTF8
$priorEncoding = $env:PYTHONIOENCODING
Push-Location $repoRoot
try {
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    if ($InstallDependencies) {
        if (-not (Test-Path -LiteralPath $labPython)) {
            if ($Python) {
                $bootstrap = (Get-Command $Python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
            } else {
                $candidate = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
                if (-not $candidate) { throw 'Python was not found. Pass -Python with the path to python.exe.' }
                $bootstrap = $candidate.Source
            }
            & $bootstrap -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 2)"
            if ($LASTEXITCODE -ne 0) { throw 'Python 3.10 or newer is required.' }
            & $bootstrap -m venv $labEnvironment
            if ($LASTEXITCODE -ne 0) { throw 'Could not create the isolated offer-lab environment.' }
        }
        & $labPython -m pip install --disable-pip-version-check -r (Join-Path $repoRoot 'requirements-window-offer-lab.txt')
        if ($LASTEXITCODE -ne 0) { throw 'Offer-lab dependency installation failed.' }
        if ($ExecuteLive) {
            & $labPython -m playwright install chromium
            if ($LASTEXITCODE -ne 0) { throw 'Chromium installation failed.' }
        }
    }
    if (-not (Test-Path -LiteralPath $labPython)) {
        throw 'Run this script with -InstallDependencies once. The regular project environment is not modified.'
    }
    & $labPython -c "import sys,pytest,jsonschema,fitz,playwright.sync_api; print('LAB_PYTHON=' + sys.executable)"
    if ($LASTEXITCODE -ne 0) { throw 'Missing offer-lab dependencies. Run with -InstallDependencies.' }
    Write-Host 'WINDOW_OFFER_STAGE=unit_tests'
    $testFiles = @(
        'tests/test_window_offer_specification.py',
        'tests/test_german_offer_mail.py',
        'tests/test_pagen_configurator.py',
        'tests/test_pagen_shared_options.py',
        'tests/test_task_document_completeness.py',
        'tests/test_window_offer_pipeline_lab.py'
    )
    & $labPython -m pytest @testFiles -q
    if ($LASTEXITCODE -ne 0) { throw 'Contract tests failed. The browser was not started.' }

    $runArguments = @('tools/check_window_offer_pipeline.py', '--output-directory', $OutputDirectory)
    if ($SpecificationFile) { $runArguments += @('--specification-file', $SpecificationFile) }
    if ($ExecuteLive) {
        Write-Host 'WINDOW_OFFER_STAGE=public_form_test'
        Write-Host 'PAGEN receives window type, profile, quantities, dimensions and supported shared options. The enquiry is not submitted.'
        $runArguments += @('--execute-live', '--headed')
    } else {
        Write-Host 'WINDOW_OFFER_STAGE=offline_pipeline'
    }
    if ($KeepOpen) { $runArguments += '--keep-open' }
    & $labPython @runArguments
    $labExitCode = $LASTEXITCODE
    Write-Host "WINDOW_OFFER_EXIT_CODE=$labExitCode"
    exit $labExitCode
} finally {
    $env:PYTHONUTF8 = $priorUtf8
    $env:PYTHONIOENCODING = $priorEncoding
    Pop-Location
}
