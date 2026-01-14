function Test-Admin {
    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($identity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

function Require-Admin {
    if (-not (Test-Admin)) {
        throw "Administrator privileges are required."
    }
}

function Get-DataRoot {
    $scriptsRoot = Split-Path -Parent $PSScriptRoot
    return (Join-Path $scriptsRoot "data")
}

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -Path $Path -ItemType Directory -Force | Out-Null
    }
}

function New-BackupId {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $rand = Get-Random -Minimum 1000 -Maximum 9999
    return "$stamp-$rand"
}

function Get-LogPaths {
    param([string]$LogId)
    $dataRoot = Get-DataRoot
    $logsRoot = Join-Path $dataRoot "logs"
    Ensure-Dir -Path $logsRoot
    return @{
        Json = (Join-Path $logsRoot "$LogId.json")
        Text = (Join-Path $logsRoot "$LogId.log")
    }
}

function Write-JsonLog {
    param(
        [string]$LogPath,
        [string]$Level,
        [string]$Message,
        [object]$Data
    )
    $logDir = Split-Path -Parent $LogPath
    if (-not (Test-Path $logDir)) {
        New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    }
    $entry = [ordered]@{
        ts = (Get-Date).ToString("o")
        level = $Level
        message = $Message
        data = $Data
    }
    $line = $entry | ConvertTo-Json -Depth 8 -Compress
    Add-Content -Path $LogPath -Value $line
}

function Write-TextLog {
    param(
        [string]$LogPath,
        [string]$Message
    )
    Add-Content -Path $LogPath -Value $Message
}
