param(
    [Parameter(Mandatory = $true)][string]$BackupId
)

. "$PSScriptRoot\common.ps1"

Require-Admin

$dataRoot = Get-DataRoot
$backupFile = Join-Path (Join-Path $dataRoot "backup") (Join-Path $BackupId "backup.json")

if (-not (Test-Path $backupFile)) {
    $errorOut = @{ ok = $false; error = "backup not found"; backup_id = $BackupId }
    $errorOut | ConvertTo-Json -Depth 6
    exit 1
}

$logId = "ps-rollback-$BackupId"
$logPaths = Get-LogPaths -LogId $logId
Write-JsonLog -LogPath $logPaths.Json -Level "info" -Message "rollback start" -Data @{ backup_id = $BackupId }
Write-TextLog -LogPath $logPaths.Text -Message "rollback start $BackupId"

$results = Rollback-FromBackup -BackupFile $backupFile

Write-JsonLog -LogPath $logPaths.Json -Level "info" -Message "rollback done" -Data @{ backup_id = $BackupId }
Write-TextLog -LogPath $logPaths.Text -Message "rollback done $BackupId"

$out = [ordered]@{
    ok = $true
    backup_id = $BackupId
    results = $results
    log_id = $logId
}

$out | ConvertTo-Json -Depth 8
