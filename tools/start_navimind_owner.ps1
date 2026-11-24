# NaviMind owner-only launcher (Windows).
# Reads DPAPI credential at runtime, never stores a plaintext .env/API key.
param(
    [ValidatePattern('^OFR/[0-9]+-?$')]
    [string]$ExpectedOffer = "OFR/4811-",
    [switch]$DiagnoseChat
)
$ErrorActionPreference = "Stop"
$secretFile = Join-Path $env:APPDATA "NaviMind\Secrets\owner-gateway.dpapi"
if (-not (Test-Path -LiteralPath $secretFile)) {
    throw "Brak klucza DPAPI. Najpierw wykonaj: .\tools\setup_navimind_owner_gateway.ps1"
}
$secure = Get-Content -LiteralPath $secretFile -Raw | ConvertTo-SecureString
$credential = [System.Net.NetworkCredential]::new("", $secure)
$secret = $credential.Password
if ([string]::IsNullOrWhiteSpace($secret)) {
    throw "Klucz jest pusty. Skonfiguruj go ponownie."
}
# The secret exists only in this process and inherited NaviMind child process.
$env:NAVIMIND_CHAT_URL = "https://ai-gateway.vercel.sh/v1/chat/completions"
$env:NAVIMIND_CHAT_MODEL = "openai/gpt-4o-mini"
$env:NAVIMIND_CHAT_API_KEY = $secret
# Deliberately force observation-only, even if shell was set to live mode.
$env:COMPUTER_USE_LIVE = "0"
Remove-Variable secret, credential, secure -ErrorAction SilentlyContinue
$root = Split-Path -Parent $PSScriptRoot
$pushed = $false
try {
    Push-Location $root
    $pushed = $true
    Write-Host "NAVIMIND_OWNER_GATEWAY_CONFIGURED=True" -ForegroundColor Green
    Write-Host "NAVIMIND_WINDOWHUB_OBSERVATION_ONLY=True"
    Write-Host "NAVIMIND_MODEL=openai/gpt-4o-mini"
    if ($DiagnoseChat) {
        Write-Host "NAVIMIND_OWNER_DIAGNOSIS_ONLY=True"
        python "tools/diagnose_navimind_gateway_chat.py"
    } else {
        python "tools/run_navimind_shared_control_center.py" --expected-offer $ExpectedOffer
    }
}
finally {
    Remove-Item Env:\NAVIMIND_CHAT_API_KEY -ErrorAction SilentlyContinue
    if ($pushed) { Pop-Location }
}
