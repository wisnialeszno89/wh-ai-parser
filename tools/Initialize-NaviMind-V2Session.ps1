<#
.SYNOPSIS
  Configure this PowerShell session for the existing NaviMind V2 endpoint.
.DESCRIPTION
  Dot-source in a trusted interactive PowerShell window:
    . .\tools\Initialize-NaviMind-V2Session.ps1
  Does not create, rotate or fetch server-side secrets, alter Vercel,
  enable computer control, persist a secret to disk or run any native input.
  The typed secret must MATCH the existing Vercel Production agent secret,
  or a separately authorized non-expired V2 test credential.
#>
[CmdletBinding()]
param([switch]$NoPrompt)
$ErrorActionPreference = 'Stop'
$env:NAVIMIND_AGENT_V2_URL = 'https://www.navimind.app/api/agent/task'
if (-not $env:NAVIMIND_AGENT_V2_SECRET) {
  if ($NoPrompt) {
    Write-Host 'V2_SECRET_MISSING=True' -ForegroundColor Yellow
  } else {
    Write-Host 'Wprowadz lokalnie sekret V2 zgodny z serwerem (znaki nie beda wyswietlane).' -ForegroundColor Yellow
    Write-Host 'Jesli nie znasz sekretu serwera, przerwij Ctrl+C. Nie tworz przypadkowej wartosci.'
    $secure = Read-Host -Prompt 'Sekret V2 (tylko lokalna sesja)' -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
      $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
      if ([string]::IsNullOrWhiteSpace($value)) {
        throw 'Nie ustawiono sekretu V2.'
      }
      $env:NAVIMIND_AGENT_V2_SECRET = $value
    }
    finally {
      if ($ptr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
      }
      Remove-Variable value, secure -ErrorAction SilentlyContinue
    }
  }
}
Write-Host 'V2_ENDPOINT_CONFIGURED=True'
Write-Host ('V2_SECRET_CONFIGURED=' + [bool]$env:NAVIMIND_AGENT_V2_SECRET)
Write-Host ('VERCEL_PROTECTION_BYPASS_PRESENT=' + [bool]$env:NAVIMIND_VERCEL_PROTECTION_BYPASS)
Write-Host 'Produkcja ma wlaczone Vercel SSO. Moze byc wymagany autoryzowany bypass.'
Write-Host 'Wykonaj: python tools/check_navimind_v2_connection.py'
Write-Host 'Tylko konfiguracja. Nie wlaczono LIVE, nie zapisano zadnej oferty.'
