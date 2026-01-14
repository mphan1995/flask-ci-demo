param(
    [Parameter(Mandatory = $true)][string]$RulesPath,
    [Parameter(Mandatory = $true)][string]$SelectedIds,
    [ValidateSet("dry_run", "apply")][string]$Mode = "dry_run",
    [ValidateSet("disable", "enable")][string]$Action = "disable"
)

. "$PSScriptRoot\common.ps1"

try {
    $rulesData = Get-Content -Raw -Path $RulesPath | ConvertFrom-Json
} catch {
    $errorOut = @{ ok = $false; error = "failed to read rules"; detail = $_.Exception.Message }
    $errorOut | ConvertTo-Json -Depth 6
    exit 1
}

$rules = $rulesData.rules
$selected = @($SelectedIds -split "," | Where-Object { $_ -and $_.Trim().Length -gt 0 })
$selectedRules = @($rules | Where-Object { $selected -contains $_.id })

if ($selectedRules.Count -eq 0) {
    $errorOut = @{ ok = $false; error = "no matching rules" }
    $errorOut | ConvertTo-Json -Depth 6
    exit 1
}

$plan = @()
foreach ($rule in $selectedRules) {
    $statusInfo = Get-RuleStatus -Rule $rule
    $action = "apply"
    if ($Action -eq "disable") {
        if ($statusInfo.status -eq "Disabled") { $action = "skip" }
        if ($statusInfo.status -eq "NotFound") { $action = "skip_not_found" }
    } else {
        if ($statusInfo.status -eq "Enabled") { $action = "skip" }
        if ($statusInfo.status -eq "NotFound") { $action = "skip_not_found" }
    }
    $plan += [ordered]@{
        id = $rule.id
        title = $rule.title
        risk = $rule.risk
        type = $rule.type
        status = $statusInfo.status
        action = $action
    }
}

$summary = [ordered]@{ success = 0; failed = 0; skipped = 0; skipped_not_found = 0 }

if ($Mode -eq "dry_run") {
    $out = [ordered]@{
        ok = $true
        mode = $Mode
        action = $Action
        plan = $plan
        summary = $summary
        backup_id = $null
        log_id = $null
    }
    $out | ConvertTo-Json -Depth 8
    exit 0
}

Require-Admin

$changeRules = @()
foreach ($planItem in $plan) {
    if ($planItem.action -eq "apply") {
        $ruleObj = $selectedRules | Where-Object { $_.id -eq $planItem.id }
        if ($ruleObj) { $changeRules += $ruleObj }
    }
}

$backupId = $null
if ($changeRules.Count -gt 0) {
    $backupId = New-BackupId
}
$logId = if ($backupId) { "ps-apply-$backupId" } else { "ps-apply-$(New-BackupId)" }
$logPaths = Get-LogPaths -LogId $logId

Write-JsonLog -LogPath $logPaths.Json -Level "info" -Message "apply start" -Data @{ mode = $Mode; action = $Action; selected = $selected }
Write-TextLog -LogPath $logPaths.Text -Message "apply start $logId"
Write-JsonLog -LogPath $logPaths.Json -Level "info" -Message "apply plan" -Data @{ action = $Action; plan = $plan }

if ($backupId) {
    Backup-State -BackupId $backupId -Rules $changeRules | Out-Null
}

$results = @()
foreach ($rule in $selectedRules) {
    $planItem = $plan | Where-Object { $_.id -eq $rule.id } | Select-Object -First 1
    if (-not $planItem -or $planItem.action -ne "apply") {
        if ($planItem -and $planItem.action -eq "skip_not_found") {
            $summary.skipped_not_found += 1
            $results += @{ id = $rule.id; status = "SkippedNotFound" }
            Write-JsonLog -LogPath $logPaths.Json -Level "info" -Message "apply rule skipped not found" -Data @{ id = $rule.id }
        } else {
            $summary.skipped += 1
            $results += @{ id = $rule.id; status = "Skipped" }
            Write-JsonLog -LogPath $logPaths.Json -Level "info" -Message "apply rule skipped" -Data @{ id = $rule.id }
        }
        continue
    }

    $ruleResults = @()
    if ($Action -eq "disable") {
        if ($rule.type -eq "service") {
            $startType = $rule.apply.startType
            if (-not $startType) { $startType = "Disabled" }
            $stop = $true
            if ($null -ne $rule.apply.stop) { $stop = [bool]$rule.apply.stop }
            foreach ($target in $rule.targets) {
                $res = Safe-SetServiceStartType -Name $target.name -StartType $startType -StopService $stop
                $ruleResults += $res
            }
        } elseif ($rule.type -eq "task") {
            foreach ($target in $rule.targets) {
                $res = Safe-DisableTask -TaskPath $target.path
                $ruleResults += $res
            }
        } elseif ($rule.type -eq "registry") {
            foreach ($target in $rule.targets) {
                $value = $rule.apply.value
                if ($null -eq $value) { $value = $rule.detect.value }
                if ($null -eq $value) { $value = $target.value }
                $valueType = $rule.apply.valueType
                if (-not $valueType) { $valueType = $target.valueType }
                $res = Safe-SetRegistry -Path $target.path -Name $target.name -Value $value -ValueType $valueType
                $ruleResults += $res
            }
        } else {
            $ruleResults += @{ status = "Error"; error = "unknown rule type" }
        }
    } else {
        $enable = if ($null -ne $rule.enable) { $rule.enable } else { [pscustomobject]@{} }
        if ($rule.type -eq "service") {
            $startType = $enable.startType
            if (-not $startType) { $startType = "Manual" }
            foreach ($target in $rule.targets) {
                $res = Safe-SetServiceStartType -Name $target.name -StartType $startType -StopService $false
                $ruleResults += $res
            }
        } elseif ($rule.type -eq "task") {
            $enabled = $true
            if ($null -ne $enable.enabled) { $enabled = [bool]$enable.enabled }
            foreach ($target in $rule.targets) {
                $res = Safe-SetTaskEnabled -TaskPath $target.path -Enabled $enabled
                $ruleResults += $res
            }
        } elseif ($rule.type -eq "registry") {
            $enableAction = $enable.action
            $enableValue = $enable.value
            if (-not $enableAction) {
                if ($null -ne $enableValue) {
                    $enableAction = "set"
                } else {
                    $enableAction = "remove"
                }
            }
            foreach ($target in $rule.targets) {
                if ($enableAction -eq "remove") {
                    $res = Safe-RemoveRegistryValue -Path $target.path -Name $target.name
                } else {
                    $value = $enableValue
                    $valueType = $enable.valueType
                    if (-not $valueType) { $valueType = $target.valueType }
                    $res = Safe-SetRegistry -Path $target.path -Name $target.name -Value $value -ValueType $valueType
                }
                $ruleResults += $res
            }
        } else {
            $ruleResults += @{ status = "Error"; error = "unknown rule type" }
        }
    }

    $postStatus = Get-RuleStatus -Rule $rule
    $ruleResults += @{ status = "PostCheck"; detail = $postStatus }

    $failed = @($ruleResults | Where-Object { $_.status -eq "Error" })
    $expectedStatus = if ($Action -eq "enable") { "Enabled" } else { "Disabled" }
    if ($postStatus.status -ne $expectedStatus -and $postStatus.status -ne "NotFound") {
        $failed = @($failed + @(@{ status = "Error"; error = "post-check not $expectedStatus"; detail = $postStatus }))
    }
    if ($failed.Count -gt 0) {
        $summary.failed += 1
        $results += @{ id = $rule.id; status = "Failed"; results = $ruleResults }
        Write-JsonLog -LogPath $logPaths.Json -Level "error" -Message "apply rule failed" -Data @{ id = $rule.id; results = $ruleResults }
    } else {
        $summary.success += 1
        $results += @{ id = $rule.id; status = "Applied"; results = $ruleResults }
        Write-JsonLog -LogPath $logPaths.Json -Level "info" -Message "apply rule ok" -Data @{ id = $rule.id; results = $ruleResults }
    }
}

Write-JsonLog -LogPath $logPaths.Json -Level "info" -Message "apply done" -Data @{ summary = $summary; backup_id = $backupId }
Write-TextLog -LogPath $logPaths.Text -Message "apply done $logId"

$out = [ordered]@{
    ok = $true
    mode = $Mode
    action = $Action
    plan = $plan
    results = $results
    summary = $summary
    backup_id = $backupId
    log_id = $logId
}

$out | ConvertTo-Json -Depth 8
