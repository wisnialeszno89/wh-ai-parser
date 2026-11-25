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
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw "NaviMind WindowHub test wymaga Windows."
}
if ($Pdf -and $RequestFile) {
  throw "Podaj -Pdf ALBO -RequestFile (nie oba jednocześnie)."
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
$WindowHub = @(Get-Process -Name "Okna" -ErrorAction SilentlyContinue)
if ($WindowHub.Count -ne 1) {
  throw "Wymagany jeden uruchomiony proces Okna.exe (wykryto $($WindowHub.Count)). Uruchom WindowHub i otwórz Start1."
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
    & $Python $Preflight
    if ($LASTEXITCODE -ne 0) {
      throw "Nie udało się wykonać bezpiecznego preflight."
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
