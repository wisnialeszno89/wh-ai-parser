<#
Safe NaviMind V2 THINK entrypoint.
No desktop actions; task and semantic scene are sent to NaviMind.
The secret is prompted in masked form and never saved by this script.
#>
param(
    [string]$Goal = 'Dodaj nowa pozycje okienna do aktualnie otwartej oferty. Nie tworz nowej oferty, nie zapisuj i nie wysylaj.',
    [string]$Endpoint = 'https://navimind.app/api/agent/task'
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

if ($Endpoint -notmatch '^https://[^/?#]+/api/agent/task$') {
    throw 'Oczekiwany bezpieczny endpoint HTTPS /api/agent/task.'
}
$oldUrl = [Environment]::GetEnvironmentVariable('NAVIMIND_AGENT_V2_URL', 'Process')
$oldSecret = [Environment]::GetEnvironmentVariable('NAVIMIND_AGENT_V2_SECRET', 'Process')
$promptedSecret = $false
try {
    $env:NAVIMIND_AGENT_V2_URL = $Endpoint
    if ([string]::IsNullOrWhiteSpace($oldSecret)) {
        Write-Host 'Wpisz sekret NAVIMIND_AGENT_SECRET z Vercel. Nie udostepniaj go na czacie.'
        $secure = Read-Host 'Sekret (ukryty)' -AsSecureString
        $ptr = [IntPtr]::Zero
        try {
            $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
            if ([string]::IsNullOrWhiteSpace($plain)) {
                throw 'Brak sekretu. Przerwano.'
            }
            $env:NAVIMIND_AGENT_V2_SECRET = $plain
            $promptedSecret = $true
        }
        finally {
            if ($ptr -ne [IntPtr]::Zero) {
                [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
            }
            Remove-Variable plain -ErrorAction SilentlyContinue
            Remove-Variable secure -ErrorAction SilentlyContinue
        }
    }

    Write-Host ''
    Write-Host '=== KONFIGURACJA V2 (BEZ WARTOSCI SEKRETOW) ==='
    python tools/diagnose_navimind_setup.py
    if ($LASTEXITCODE -ne 0) { throw 'DIAGNOSIS FAILED' }

    Write-Host ''
    Write-Host '=== V2 THINK - ZERO KLIKNIĘĆ ==='
    python tools/run_windowhub_goal_v2.py --goal $Goal --mode think
    $exitCode = $LASTEXITCODE
    Write-Host "THINK_EXIT_CODE=$exitCode"
    if ($exitCode -ne 0) {
        throw "THINK FAILED: $exitCode"
    }
}
finally {
    if ($promptedSecret) {
        Remove-Item Env:NAVIMIND_AGENT_V2_SECRET -ErrorAction SilentlyContinue
    }
    if ([string]::IsNullOrWhiteSpace($oldUrl)) {
        Remove-Item Env:NAVIMIND_AGENT_V2_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:NAVIMIND_AGENT_V2_URL = $oldUrl
    }
}
