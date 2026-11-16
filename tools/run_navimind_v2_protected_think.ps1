<# 
Run one NaviMind V2 auth probe followed by THINK (no UI changes).
Requires NAVIMIND_AGENT_V2_SECRET already in this PowerShell session.
Prompts separately for Vercel Automation Protection Bypass secret.
Does not persist either credential.
#>
param([switch]$SkipThink)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

if ([string]::IsNullOrWhiteSpace($env:NAVIMIND_AGENT_V2_SECRET)) {
    throw 'Missing NAVIMIND_AGENT_V2_SECRET. Generate or load valid NaviMind V2 test credential first.'
}
if ([string]::IsNullOrWhiteSpace($env:NAVIMIND_AGENT_V2_URL)) {
    $env:NAVIMIND_AGENT_V2_URL = 'https://navimind.app/api/agent/task'
}

$hadBypass = [Environment]::GetEnvironmentVariable(
    'NAVIMIND_VERCEL_PROTECTION_BYPASS', 'Process'
)
$prompted = $false
try {
    if ([string]::IsNullOrWhiteSpace($hadBypass)) {
        Write-Host 'Enter Vercel Protection Bypass for Automation secret (NOT NaviMind secret).'
        $secure = Read-Host 'Vercel bypass (hidden)' -AsSecureString
        $ptr = [IntPtr]::Zero
        try {
            $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
            if ([string]::IsNullOrWhiteSpace($plain)) {
                throw 'Empty Vercel protection bypass secret.'
            }
            $env:NAVIMIND_VERCEL_PROTECTION_BYPASS = $plain
            $prompted = $true
        }
        finally {
            if ($ptr -ne [IntPtr]::Zero) {
                [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
            }
            Remove-Variable plain -ErrorAction SilentlyContinue
            Remove-Variable secure -ErrorAction SilentlyContinue
        }
    }

    Write-Host '=== AUTH PROBE WITHOUT MODEL OR WINDOWHUB ==='
    python tools/probe_navimind_auth_layer.py
    if ($LASTEXITCODE -ne 0) {
        throw 'Authentication failed. Stop before THINK.'
    }
    if (-not $SkipThink) {
        Write-Host '=== THINK: NO UI ACTIONS ==='
        powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_navimind_v2_think_secure.ps1
        if ($LASTEXITCODE -ne 0) {
            throw 'V2 think test failed.'
        }
    }
}
finally {
    if ($prompted) {
        Remove-Item Env:NAVIMIND_VERCEL_PROTECTION_BYPASS -ErrorAction SilentlyContinue
    }
}
