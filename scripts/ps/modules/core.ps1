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

function Get-ProcessCpuUsage {
    param([int]$SampleMs = 750)

    $cpuCount = [Environment]::ProcessorCount
    if ($cpuCount -lt 1) {
        $cpuCount = 1
    }

    $snapshot1 = @{}
    $processes = Get-Process -ErrorAction SilentlyContinue
    foreach ($proc in $processes) {
        if ($null -eq $proc.Id) {
            continue
        }
        $cpu = if ($null -ne $proc.CPU) { [double]$proc.CPU } else { 0 }
        $snapshot1[$proc.Id] = $cpu
    }

    Start-Sleep -Milliseconds $SampleMs

    $snapshot2 = @{}
    $processes = Get-Process -ErrorAction SilentlyContinue
    foreach ($proc in $processes) {
        if ($null -eq $proc.Id) {
            continue
        }
        $cpu = if ($null -ne $proc.CPU) { [double]$proc.CPU } else { 0 }
        $snapshot2[$proc.Id] = $cpu
    }

    $interval = [double]$SampleMs / 1000
    if ($interval -le 0) {
        $interval = 1
    }

    $usage = @{}
    foreach ($pid in $snapshot2.Keys) {
        $cpu2 = $snapshot2[$pid]
        $cpu1 = if ($snapshot1.ContainsKey($pid)) { $snapshot1[$pid] } else { $cpu2 }
        $delta = $cpu2 - $cpu1
        if ($delta -lt 0) {
            $delta = 0
        }
        $pct = ($delta / $interval) / $cpuCount * 100
        if ($pct -lt 0) {
            $pct = 0
        }
        $usage[$pid] = [math]::Round($pct, 2)
    }

    return $usage
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
