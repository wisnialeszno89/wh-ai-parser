# Dot-source from an interactive PowerShell window:
# . .\tools\new_navimind_two_hour_test_secret.ps1
# Generates a random temporary credential without committing or printing it.
# The credential is copied to clipboard for pasting into Vercel.
# Server-side expiry requires the NaviMind V2 temporary-secret feature deployed.

$ErrorActionPreference = 'Stop'

$bytes = New-Object byte[] 32
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
try { $rng.GetBytes($bytes) }
finally { $rng.Dispose() }

$secret = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')
[Array]::Clear($bytes, 0, $bytes.Length)
$now = [DateTimeOffset]::UtcNow
$expiry = $now.AddHours(2)

$env:NAVIMIND_AGENT_V2_URL = 'https://www.navimind.app/api/agent/task'
$env:NAVIMIND_AGENT_V2_SECRET = $secret
Set-Clipboard -Value $secret
Remove-Variable secret -ErrorAction SilentlyContinue

Write-Host ''
Write-Host 'Tymczasowy klucz zostal wygenerowany i skopiowany do schowka.' -ForegroundColor Green
Write-Host 'Dodaj na Vercel 3 oddzielne zmienne w Production:'
Write-Host 'NAVIMIND_AGENT_TEST_SECRET = [WKLEJ ZE SCHOWKA CTRL+V]'
Write-Host ('NAVIMIND_AGENT_TEST_ISSUED_AT = ' + $now.ToString('yyyy-MM-ddTHH:mm:ssZ'))
Write-Host ('NAVIMIND_AGENT_TEST_EXPIRES_AT = ' + $expiry.ToString('yyyy-MM-ddTHH:mm:ssZ'))
Write-Host ''
Write-Host 'Po zapisaniu zmiennych konieczne jest nowe wdrozenie serwera.'
Write-Host 'Ten klucz nie obchodzi Vercel SSO/Deployment Protection.'
Write-Host 'W tym oknie PowerShell klucz jest ustawiony w NAVIMIND_AGENT_V2_SECRET.'
Write-Host 'Nie wklejaj klucza do chatu, Git ani logow.'
