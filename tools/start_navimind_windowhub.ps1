# Windows PowerShell 5.1 / NaviMind V2 launcher with local DPAPI credential store.
# Does not change server credentials, and never prints request headers or secrets.
[CmdletBinding()]
param(
    [switch]$ConfigureAgent,
    [switch]$ConfigureBypass,
    [switch]$TestOnly,
    [ValidateRange(1, 20)][int]$MaxActions = 4,
    [string]$CustomerName = "Top Trans Janik Artur",
    [string]$SalesMission = "research/scenarios/top_trans_20261119_4windows.json"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$vault = Join-Path $env:LOCALAPPDATA "NaviMind"
$secretPath = Join-Path $vault "agent-v2-secret.txt"
$bypassPath = Join-Path $vault "vercel-protection-bypass.txt"
$env:NAVIMIND_AGENT_V2_URL = "https://navimind-adams-projects-080d3918.vercel.app/api/agent/task"

function Get-UnprotectedText([Security.SecureString]$secure) {
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
}

function Write-LocalCredential([string]$path, [string]$promptText) {
    New-Item -ItemType Directory -Path $vault -Force | Out-Null
    $secure = Read-Host $promptText -AsSecureString
    if ($secure.Length -lt 1) {
        throw "EMPTY_CREDENTIAL_NOT_SAVED"
    }
    $encrypted = ConvertFrom-SecureString -SecureString $secure
    [System.IO.File]::WriteAllText($path, $encrypted, [System.Text.Encoding]::ASCII)
    Write-Host "DPAPI_CREDENTIAL_SAVED=True"
}

function Read-LocalCredential([string]$path) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "MISSING_DPAPI_CREDENTIAL: Run with -ConfigureAgent or -ConfigureBypass, as appropriate."
    }
    $encrypted = [System.IO.File]::ReadAllText($path).Trim()
    return Get-UnprotectedText (ConvertTo-SecureString -String $encrypted)
}

if ($ConfigureAgent) {
    Write-LocalCredential $secretPath "Wklej ten SAM klucz, ktory jest na Vercel jako NAVIMIND_AGENT_SECRET"
}
if ($ConfigureBypass) {
    Write-LocalCredential $bypassPath "Wklej prawidlowy Vercel Protection Bypass"
}
if ($ConfigureAgent -or $ConfigureBypass) {
    Write-Host "CONFIGURATION_UPDATED_LOCALLY=True"
    Write-Host "NOTE=Vercel environment variables were NOT changed."
    exit 0
}

$env:NAVIMIND_AGENT_V2_SECRET = Read-LocalCredential $secretPath
$env:NAVIMIND_VERCEL_PROTECTION_BYPASS = Read-LocalCredential $bypassPath

function Test-NaviMindAuth {
    $headers = @{
        "x-navimind-agent-secret" = $env:NAVIMIND_AGENT_V2_SECRET
        "x-vercel-protection-bypass" = $env:NAVIMIND_VERCEL_PROTECTION_BYPASS
    }
    $response = $null
    $body = ""
    $status = 0
    $contentType = ""
    $mitigated = ""
    try {
        $web = Invoke-WebRequest -Uri $env:NAVIMIND_AGENT_V2_URL -Method Post `
            -Headers $headers -ContentType "application/json" -Body "{}" `
            -UseBasicParsing -MaximumRedirection 0 -ErrorAction Stop
        $status = [int]$web.StatusCode
        $contentType = [string]$web.Headers["Content-Type"]
        $body = [string]$web.Content
    }
    catch [System.Net.WebException] {
        $response = $_.Exception.Response
        if ($null -eq $response) {
            Write-Host "NAVIMIND_AUTH=NETWORK_ERROR"
            return $false
        }
        $status = [int]$response.StatusCode
        $contentType = [string]$response.ContentType
        $mitigated = [string]$response.Headers["x-vercel-mitigated"]
        try {
            $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
            try { $body = $reader.ReadToEnd() }
            finally { $reader.Dispose() }
        }
        catch { $body = "" }
    }

    $errorCode = ""
    if ($contentType -match "json" -and $body) {
        try {
            $json = ConvertFrom-Json -InputObject $body
            if ($json.error -is [string]) { $errorCode = $json.error }
        }
        catch { }
    }

    Write-Host "NAVIMIND_HTTP_STATUS=$status"
    Write-Host "NAVIMIND_CONTENT_TYPE=$contentType"
    if ($mitigated) { Write-Host "VERCEL_MITIGATION=$mitigated" }
    if ($errorCode) { Write-Host "NAVIMIND_API_ERROR=$errorCode" }

    if ($status -eq 400 -and $errorCode -eq "INVALID_AGENT_TASK") {
        Write-Host "NAVIMIND_AUTH=PASS" -ForegroundColor Green
        return $true
    }

    if ($mitigated -or ($status -eq 401 -and $contentType -notmatch "json")) {
        Write-Host "NAVIMIND_AUTH=VERCEL_PROTECTION_OR_CHALLENGE" -ForegroundColor Yellow
        Write-Host "ACTION=Verify Vercel Deployment Protection bypass token; do not rotate NaviMind agent secret."
    }
    elseif ($status -eq 401 -and $errorCode -eq "UNAUTHORIZED") {
        Write-Host "NAVIMIND_AUTH=AGENT_SECRET_MISMATCH" -ForegroundColor Yellow
        Write-Host "ACTION=Sync Vercel NAVIMIND_AGENT_SECRET with local DPAPI credential; redeploy production if changed."
    }
    elseif ($status -eq 401) {
        Write-Host "NAVIMIND_AUTH=UNCLASSIFIED_401" -ForegroundColor Yellow
        Write-Host "ACTION=Inspect non-sensitive response headers and Vercel access logs."
    }
    else {
        Write-Host "NAVIMIND_AUTH=UNEXPECTED_RESPONSE"
    }
    return $false
}

if (-not (Test-NaviMindAuth)) {
    Write-Host "WINDOWHUB_EXECUTED=False"
    exit 3
}
if ($TestOnly) { exit 0 }

Set-Location $repoRoot
# Avoid thousands of tiny .pyc writes on removable/low-space E: drive.
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:COMPUTER_USE_LIVE = "1"
$env:WH_REAL_WINDOWHUB = "1"
try {
    & python (Join-Path $repoRoot "tools/run_windowhub_goal_v2.py") `
        --sales-mission $SalesMission `
        --mode execute --execute-live `
        --customer-lookup-skill `
        --customer-name $CustomerName `
        --interactive-handoff --handoff-timeout 120 `
        --max-actions $MaxActions
    exit $LASTEXITCODE
}
finally {
    Remove-Item Env:COMPUTER_USE_LIVE, Env:WH_REAL_WINDOWHUB -ErrorAction SilentlyContinue
}
