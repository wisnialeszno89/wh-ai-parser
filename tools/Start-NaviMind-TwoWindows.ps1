<#
.SYNOPSIS
  Start a supervised, exactly-two-window WindowHub offer acceptance test.
.DESCRIPTION
  Run inside this repository after checkout of the PR #240 test branch.
  It never starts WindowHub, saves an offer, clicks without local operator
  Resume, or authorizes sending a PDF to an AI provider without UI consent.
.EXAMPLE
  .\tools\Start-NaviMind-TwoWindows.ps1 -Pdf "C:\Oferty\zapytanie.pdf"
.EXAMPLE
  .\tools\Start-NaviMind-TwoWindows.ps1 -RequestFile "C:\Oferty\dwa-okna.txt" -Live
#>
[CmdletBinding()]
param(
  [string]$Pdf,
  [string]$RequestFile,
  [switch]$Live,
  [switch]$SkipPreflight,
  [string]$Python = "python"
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
# Load only missing keys from the local .env so a freshly opened terminal
# does not silently lose CHAT credentials while V2 still appears configured.
# Never print credentials or overwrite values explicitly provided by user.
$LocalEnv = Join-Path $Root '.env'
if (Test-Path -LiteralPath $LocalEnv -PathType Leaf) {
  foreach ($Line in [System.IO.File]::ReadAllLines($LocalEnv)) {
    $Trimmed = $Line.Trim()
    if (-not $Trimmed -or $Trimmed.StartsWith('#')) { continue }
    $Match = [regex]::Match($Trimmed, '^([A-Za-z_][A-Za-z0-9_]*)=(.*)
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw "NaviMind WindowHub test wymaga Windows."
}
if ($Pdf -and $RequestFile) {
  throw "Podaj -Pdf ALBO -RequestFile (nie oba jednocześnie)."
}
if ($Live -and $SkipPreflight) {
  throw "Przy -Live nie można pominąć kontroli środowiska."
}
$Script = Join-Path $Root "tools\run_navimind_shared_control_center.py"
$Preflight = Join-Path $Root "tools\run_navimind_offer_preflight.py"
if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) {
  throw "Nie znaleziono lokalnego hosta NaviMind: $Script"
}
& $Python --version
if ($LASTEXITCODE -ne 0) {
  throw "Python jest niedostępny; wybierz poprawną ścieżkę przez -Python."
}
# A planning session must remain available even when the application
# is absent, renamed or not yet discoverable. Live mode still fails closed:
# the native executor requires an independently verified exact WindowHub scope.
$WindowHub = @(Get-Process -Name "Okna" -ErrorAction SilentlyContinue)
if ($WindowHub.Count -ne 1) {
  if ($Live) {
    throw "LIVE wymaga jednoznacznego Okna.exe (wykryto $($WindowHub.Count)). Nie uruchamiam sterowania nieznanym programem."
  }
  Write-Warning "Nie potwierdzono Okna.exe (wykryto $($WindowHub.Count)). Uruchamiam rozmowe i obserwacje bez klikniec; NaviMind moze poprosic o wskazanie programu."
}
$ResolvedPdf = $null
if ($Pdf) {
  $ResolvedPdf = (Resolve-Path -LiteralPath $Pdf -ErrorAction Stop).Path
  if ([IO.Path]::GetExtension($ResolvedPdf).ToLowerInvariant() -ne ".pdf") {
    throw "Plik musi mieć rozszerzenie PDF."
  }
}
$ResolvedRequest = $null
if ($RequestFile) {
  $ResolvedRequest = (Resolve-Path -LiteralPath $RequestFile -ErrorAction Stop).Path
  if ([IO.Path]::GetExtension($ResolvedRequest).ToLowerInvariant() -ne ".txt") {
    throw "Plik z treścią musi mieć rozszerzenie TXT (UTF-8)."
  }
}
Push-Location $Root
$OldLive = [Environment]::GetEnvironmentVariable("COMPUTER_USE_LIVE", "Process")
$OldWH = [Environment]::GetEnvironmentVariable("WH_REAL_WINDOWHUB", "Process")
try {
  # A dry run cannot inherit an accidentally armed parent process.
  $env:COMPUTER_USE_LIVE = if ($Live) { "1" } else { "0" }
  $env:WH_REAL_WINDOWHUB = if ($Live) { "1" } else { "0" }
  if (-not $SkipPreflight) {
    $PreflightOutput = & $Python $Preflight | Out-String
    if ($LASTEXITCODE -ne 0) {
      throw "Nie udało się wykonać bezpiecznego preflight."
    }
    $Report = $PreflightOutput | ConvertFrom-Json
    $PreflightOutput | Write-Host
    if (-not $env:NAVIMIND_CHAT_URL -or -not $env:NAVIMIND_CHAT_MODEL -or -not $env:NAVIMIND_CHAT_API_KEY) {
      Write-Warning "MODEL AI NIEPODLACZONY: wymagane NAVIMIND_CHAT_URL, NAVIMIND_CHAT_MODEL i NAVIMIND_CHAT_API_KEY w tej sesji PowerShell. Obserwacja moze dzialac bez rozmowy."
    }
    if ($Live) {
      $MissingRuntime = (
        -not $Report.dependencies.pywinauto -or
        -not $Report.dependencies.pythoncom -or
        -not $Report.reasoner_url_configured -or
        -not $Report.reasoner_secret_configured
      )
      if ($Pdf -and -not $Report.dependencies.fitz) {
        $MissingRuntime = $true
      }
      if ($MissingRuntime) {
        throw "Brak wymaganych zależności Windows lub konfiguracji V2. Napraw ostrzeżenia preflight przed testem -Live."
      }
    }
  }
  Write-Host ""
  Write-Host "NAVIMIND • TEST DOKŁADNIE 2 OKIEN" -ForegroundColor Cyan
  Write-Host "Tryb: $(if ($Live) {'LIVE - nadal wymaga klikania Wznów pracę'} else {'TYLKO PLANOWANIE'})"
  Write-Host "Podaj w panelu dwie pozycje w ZAPYTANIE KLIENTA / PDF."
  Write-Host "Potem: sprawdź treść -> Udostępnij AI -> wpisz w czacie"
  Write-Host "  Przygotuj nową, niezapisaną ofertę dla dwóch pozycji z zapytania."
  Write-Host "Używaj wyłącznie testowego klienta. Nie zapisuj oferty."
  Write-Host ""
  $Arguments = @($Script, "--new-offer", "--test-two-windows")
  if ($ResolvedPdf) {
    $Arguments += @("--pdf", $ResolvedPdf)
  }
  if ($ResolvedRequest) {
    $Arguments += @("--request-file", $ResolvedRequest)
  }
  & $Python @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "NaviMind zakończył pracę z kodem: $LASTEXITCODE"
  }
} finally {
  [Environment]::SetEnvironmentVariable("COMPUTER_USE_LIVE", $OldLive, "Process")
  [Environment]::SetEnvironmentVariable("WH_REAL_WINDOWHUB", $OldWH, "Process")
  Pop-Location
}
)
    if (-not $Match.Success) { continue }
    $Key = $Match.Groups[1].Value
    if ($Key -notin @(
      'NAVIMIND_AGENT_V2_URL', 'NAVIMIND_AGENT_V2_SECRET',
      'NAVIMIND_VERCEL_PROTECTION_BYPASS',
      'NAVIMIND_CHAT_URL', 'NAVIMIND_CHAT_MODEL', 'NAVIMIND_CHAT_API_KEY'
    )) { continue }
    $Existing = [Environment]::GetEnvironmentVariable($Key, 'Process')
    if (-not [string]::IsNullOrWhiteSpace($Existing)) { continue }
    $Value = $Match.Groups[2].Value.Trim()
    if ($Value.Length -ge 2 -and (
      ($Value.StartsWith('"') -and $Value.EndsWith('"')) -or
      ($Value.StartsWith("'") -and $Value.EndsWith("'"))
    )) {
      $Value = $Value.Substring(1, $Value.Length - 2)
    }
    if (-not [string]::IsNullOrWhiteSpace($Value)) {
      [Environment]::SetEnvironmentVariable($Key, $Value, 'Process')
    }
  }
}
$ChatKeysPresent = (
  -not [string]::IsNullOrWhiteSpace($env:NAVIMIND_CHAT_URL) -and
  -not [string]::IsNullOrWhiteSpace($env:NAVIMIND_CHAT_MODEL) -and
  -not [string]::IsNullOrWhiteSpace($env:NAVIMIND_CHAT_API_KEY)
)
Write-Host "NAVIMIND_CHAT_CONFIG_PRESENT=$ChatKeysPresent"
Write-Host "NAVIMIND_CHAT_KEYS_SOURCE=process_or_local_env"

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw "NaviMind WindowHub test wymaga Windows."
}
if ($Pdf -and $RequestFile) {
  throw "Podaj -Pdf ALBO -RequestFile (nie oba jednocześnie)."
}
if ($Live -and $SkipPreflight) {
  throw "Przy -Live nie można pominąć kontroli środowiska."
}
$Script = Join-Path $Root "tools\run_navimind_shared_control_center.py"
$Preflight = Join-Path $Root "tools\run_navimind_offer_preflight.py"
if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) {
  throw "Nie znaleziono lokalnego hosta NaviMind: $Script"
}
& $Python --version
if ($LASTEXITCODE -ne 0) {
  throw "Python jest niedostępny; wybierz poprawną ścieżkę przez -Python."
}
# A planning session must remain available even when the application
# is absent, renamed or not yet discoverable. Live mode still fails closed:
# the native executor requires an independently verified exact WindowHub scope.
$WindowHub = @(Get-Process -Name "Okna" -ErrorAction SilentlyContinue)
if ($WindowHub.Count -ne 1) {
  if ($Live) {
    throw "LIVE wymaga jednoznacznego Okna.exe (wykryto $($WindowHub.Count)). Nie uruchamiam sterowania nieznanym programem."
  }
  Write-Warning "Nie potwierdzono Okna.exe (wykryto $($WindowHub.Count)). Uruchamiam rozmowe i obserwacje bez klikniec; NaviMind moze poprosic o wskazanie programu."
}
$ResolvedPdf = $null
if ($Pdf) {
  $ResolvedPdf = (Resolve-Path -LiteralPath $Pdf -ErrorAction Stop).Path
  if ([IO.Path]::GetExtension($ResolvedPdf).ToLowerInvariant() -ne ".pdf") {
    throw "Plik musi mieć rozszerzenie PDF."
  }
}
$ResolvedRequest = $null
if ($RequestFile) {
  $ResolvedRequest = (Resolve-Path -LiteralPath $RequestFile -ErrorAction Stop).Path
  if ([IO.Path]::GetExtension($ResolvedRequest).ToLowerInvariant() -ne ".txt") {
    throw "Plik z treścią musi mieć rozszerzenie TXT (UTF-8)."
  }
}
Push-Location $Root
$OldLive = [Environment]::GetEnvironmentVariable("COMPUTER_USE_LIVE", "Process")
$OldWH = [Environment]::GetEnvironmentVariable("WH_REAL_WINDOWHUB", "Process")
try {
  # A dry run cannot inherit an accidentally armed parent process.
  $env:COMPUTER_USE_LIVE = if ($Live) { "1" } else { "0" }
  $env:WH_REAL_WINDOWHUB = if ($Live) { "1" } else { "0" }
  if (-not $SkipPreflight) {
    $PreflightOutput = & $Python $Preflight | Out-String
    if ($LASTEXITCODE -ne 0) {
      throw "Nie udało się wykonać bezpiecznego preflight."
    }
    $Report = $PreflightOutput | ConvertFrom-Json
    $PreflightOutput | Write-Host
    if (-not $env:NAVIMIND_CHAT_URL -or -not $env:NAVIMIND_CHAT_MODEL -or -not $env:NAVIMIND_CHAT_API_KEY) {
      Write-Warning "MODEL AI NIEPODLACZONY: wymagane NAVIMIND_CHAT_URL, NAVIMIND_CHAT_MODEL i NAVIMIND_CHAT_API_KEY w tej sesji PowerShell. Obserwacja moze dzialac bez rozmowy."
    }
    if ($Live) {
      $MissingRuntime = (
        -not $Report.dependencies.pywinauto -or
        -not $Report.dependencies.pythoncom -or
        -not $Report.reasoner_url_configured -or
        -not $Report.reasoner_secret_configured
      )
      if ($Pdf -and -not $Report.dependencies.fitz) {
        $MissingRuntime = $true
      }
      if ($MissingRuntime) {
        throw "Brak wymaganych zależności Windows lub konfiguracji V2. Napraw ostrzeżenia preflight przed testem -Live."
      }
    }
  }
  Write-Host ""
  Write-Host "NAVIMIND • TEST DOKŁADNIE 2 OKIEN" -ForegroundColor Cyan
  Write-Host "Tryb: $(if ($Live) {'LIVE - nadal wymaga klikania Wznów pracę'} else {'TYLKO PLANOWANIE'})"
  Write-Host "Podaj w panelu dwie pozycje w ZAPYTANIE KLIENTA / PDF."
  Write-Host "Potem: sprawdź treść -> Udostępnij AI -> wpisz w czacie"
  Write-Host "  Przygotuj nową, niezapisaną ofertę dla dwóch pozycji z zapytania."
  Write-Host "Używaj wyłącznie testowego klienta. Nie zapisuj oferty."
  Write-Host ""
  $Arguments = @($Script, "--new-offer", "--test-two-windows")
  if ($ResolvedPdf) {
    $Arguments += @("--pdf", $ResolvedPdf)
  }
  if ($ResolvedRequest) {
    $Arguments += @("--request-file", $ResolvedRequest)
  }
  & $Python @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "NaviMind zakończył pracę z kodem: $LASTEXITCODE"
  }
} finally {
  [Environment]::SetEnvironmentVariable("COMPUTER_USE_LIVE", $OldLive, "Process")
  [Environment]::SetEnvironmentVariable("WH_REAL_WINDOWHUB", $OldWH, "Process")
  Pop-Location
}
