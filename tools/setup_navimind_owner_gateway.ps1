# NaviMind owner-only AI Gateway credential enrollment.
# Never pass a key on the command line or save it in git, plain .env, or logs.
# Windows DPAPI protects it for the current Windows user on this machine.
$ErrorActionPreference = "Stop"
if (-not $IsWindows -and $env:OS -ne "Windows_NT") {
    throw "Ten skrypt jest przeznaczony dla Windows."
}
$folder = Join-Path $env:APPDATA "NaviMind\Secrets"
$file = Join-Path $folder "owner-gateway.dpapi"
New-Item -Path $folder -ItemType Directory -Force | Out-Null
Write-Host "NaviMind: zapis klucza AI Gateway dla aktualnego konta Windows." -ForegroundColor Cyan
Write-Host "Wklej klucz z Vercel AI Gateway. Nie bedzie pokazany w terminalu."
if (Test-Path -LiteralPath $file) {
    $confirmed = Read-Host "Poprzedni klucz istnieje. Nadpisac? Wpisz TAK"
    if ($confirmed -cne "TAK") {
        Write-Host "Przerwano, poprzedni klucz zachowany."
        return
    }
}
$secure = Read-Host "Klucz AI Gateway" -AsSecureString
if ($null -eq $secure -or $secure.Length -lt 20) {
    throw "Klucz pusty lub zbyt krotki. Nic nie zapisano."
}
# On Windows, this uses DPAPI, not a manually typed encryption password.
$encrypted = ConvertFrom-SecureString -SecureString $secure
Set-Content -LiteralPath $file -Value $encrypted -NoNewline -Encoding Ascii
# Protect from accidental directory listing and discourage easy sharing.
try { (Get-Item -LiteralPath $file).Attributes = "Hidden, Archive" } catch {}
Remove-Variable secure, encrypted -ErrorAction SilentlyContinue
Write-Host "ZAPISANO_DPAPI=True" -ForegroundColor Green
Write-Host "NaviMind przechowuje klucz tylko jako zaszyfrowany plik profilu uzytkownika."
Write-Host "Nie kopiuj tego pliku do ZIP, GitHub ani na inny komputer."
Write-Host "Zalecenie: wyczysc schowek po skopiowaniu klucza z Vercel."
