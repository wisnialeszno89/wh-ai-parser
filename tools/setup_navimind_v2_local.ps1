# Configure a local NaviMind V2 endpoint from an existing Vercel deployment.
# No HTTP requests, no secret output, no GUI automation and no Vercel mutation.
[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"

$project = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$envPath = Join-Path $project ".env"

if (Test-Path -LiteralPath $envPath) {
    throw "LOCAL_ENV_ALREADY_EXISTS: No changes made. Back up the file before manual updates."
}
Write-Host "NaviMind V2 local setup"
Write-Host "Deploy NaviMind PR #26 and configure server OPENAI_API_KEY + NAVIMIND_AGENT_SECRET first."
Write-Host "Enter the SAME secret already configured in Vercel. Never paste it in chat."

$origin = (Read-Host "Vercel production HTTPS origin (or full /api/agent/task URL)").Trim()
if (-not $origin) { throw "URL_REQUIRED" }
$uri = $null
try { $uri = [System.Uri]::new($origin, [System.UriKind]::Absolute) }
catch { throw "URL_MALFORMED" }
if (
    -not $uri.IsAbsoluteUri -or
    [string]::IsNullOrWhiteSpace($uri.Host) -or
    -not [string]::IsNullOrEmpty($uri.UserInfo) -or
    -not [string]::IsNullOrEmpty($uri.Query) -or
    -not [string]::IsNullOrEmpty($uri.Fragment)
) { throw "URL_NOT_ACCEPTED" }
if (
    $uri.Scheme -ne "https" -and
    -not (
        $uri.Scheme -eq "http" -and
        $uri.Host -in @("localhost", "127.0.0.1")
    )
) { throw "URL_MUST_USE_HTTPS" }
$path = $uri.AbsolutePath.TrimEnd("/")
if ($path -ne "" -and $path -ne "/api/agent/task") {
    throw "URL_WRONG_PATH: Use deployment origin or /api/agent/task, not /api/agent/task/v2"
}
$endpoint = $uri.GetLeftPart([System.UriPartial]::Authority).TrimEnd("/") + "/api/agent/task"

$secureSecret = Read-Host "Existing Vercel NAVIMIND_AGENT_SECRET (input hidden)" -AsSecureString
if ($null -eq $secureSecret -or $secureSecret.Length -lt 24) {
    throw "SECRET_REQUIRED: Use an existing high-entropy Vercel secret of at least 24 characters."
}

$bstr = [IntPtr]::Zero
$secret = $null
try {
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureSecret)
    $secret = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if (
        [string]::IsNullOrWhiteSpace($secret) -or
        $secret.Length -lt 24 -or
        $secret.IndexOf([char]10) -ge 0 -or
        $secret.IndexOf([char]13) -ge 0
    ) { throw "SECRET_FORMAT_INVALID" }

    $escapedSecret = $secret.Replace('\', '\\').Replace('"', '\"')
    $eol = [Environment]::NewLine
    $fileContent = "# Local only: .env is ignored by Git." + $eol +
        'NAVIMIND_AGENT_V2_URL="' + $endpoint + '"' + $eol +
        'NAVIMIND_AGENT_V2_SECRET="' + $escapedSecret + '"' + $eol
    [System.IO.File]::WriteAllText(
        $envPath, $fileContent, [System.Text.UTF8Encoding]::new($false)
    )
} finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    $secret = $null
    if ($null -ne $secureSecret) { $secureSecret.Dispose() }
}
Write-Host "LOCAL_ENV_CREATED=True"
Write-Host "SECRET_DISPLAYED=False"
Write-Host "DEPLOYMENT_VERIFIED=False"
Write-Host "NEXT=Run python tools/diagnose_navimind_setup.py; do not share .env."
