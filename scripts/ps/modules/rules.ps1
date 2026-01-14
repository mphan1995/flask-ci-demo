function Get-RuleStatus {
    param([pscustomobject]$Rule)

    $type = $Rule.type
    $targets = $Rule.targets

    if ($type -eq "service") {
        $expected = $Rule.detect.startType
        if ($null -eq $expected -or $expected -eq "") { $expected = "Disabled" }
        $expectedSpec = Resolve-ServiceStartSpec -StartType $expected
        $found = 0
        $disabled = 0
        foreach ($target in $targets) {
            $name = $target.name
            $snapshot = Get-ServiceSnapshot -Name $name
            if (-not $snapshot.found) {
                continue
            }
            $found += 1
            $match = $false
            if ($null -ne $expectedSpec.StartValue -and $null -ne $snapshot.start_value) {
                $match = ($snapshot.start_value -eq $expectedSpec.StartValue)
            } elseif ($expectedSpec.StartType -and $snapshot.start_mode) {
                $match = (Normalize-ServiceStartType -StartType $snapshot.start_mode) -eq $expectedSpec.StartType
            }
            if (($expectedSpec.StartValue -eq 4 -or $expectedSpec.StartType -eq "Disabled") -and $snapshot.state -eq "Running") {
                $match = $false
            }
            if ($match) {
                $disabled += 1
            }
        }
        if ($found -eq 0) { return @{ status = "NotFound"; details = "service not found" } }
        if ($disabled -eq $found) { return @{ status = "Disabled"; details = "all services disabled" } }
        return @{ status = "Enabled"; details = "service enabled" }
    }

    if ($type -eq "task") {
        $expectedEnabled = $Rule.detect.enabled
        if ($null -eq $expectedEnabled) { $expectedEnabled = $false }
        $found = 0
        $disabled = 0
        foreach ($target in $targets) {
            $taskParts = Split-TaskPath -FullPath $target.path
            $task = Get-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction SilentlyContinue
            if (-not $task) {
                continue
            }
            $found += 1
            if ($task.Settings.Enabled -eq $expectedEnabled) {
                $disabled += 1
            }
        }
        if ($found -eq 0) { return @{ status = "NotFound"; details = "task not found" } }
        if ($disabled -eq $found) { return @{ status = "Disabled"; details = "all tasks disabled" } }
        return @{ status = "Enabled"; details = "task enabled" }
    }

    if ($type -eq "registry") {
        $expectedValue = $Rule.detect.value
        foreach ($target in $targets) {
            $valueInfo = Get-RegistryValue -Path $target.path -Name $target.name
            if (-not $valueInfo['Exists']) {
                return @{ status = "Enabled"; details = "registry not set" }
            }
            $desired = $expectedValue
            if ($null -eq $desired) { $desired = $target.value }
            $actualText = [string]$valueInfo['Value']
            $desiredText = [string]$desired
            if ($actualText -ne $desiredText) {
                return @{ status = "Enabled"; details = "registry mismatch" }
            }
        }
        return @{ status = "Disabled"; details = "registry matches" }
    }

    return @{ status = "Enabled"; details = "unknown type" }
}

function Backup-State {
    param(
        [string]$BackupId,
        [array]$Rules
    )

    $dataRoot = Get-DataRoot
    $backupRoot = Join-Path $dataRoot "backup"
    $backupDir = Join-Path $backupRoot $BackupId

    Ensure-Dir -Path $backupDir

    $services = @()
    $tasks = @()
    $registry = @()

    foreach ($rule in $Rules) {
        if ($rule.type -eq "service") {
            foreach ($target in $rule.targets) {
                $name = $target.name
                $snapshot = Get-ServiceSnapshot -Name $name
                if (-not $snapshot.found) {
                    $services += @{ name = $name; notFound = $true }
                    continue
                }
                $services += @{
                    name = $name
                    startType = $snapshot.start_mode
                    startValue = $snapshot.start_value
                    registryFound = $snapshot.registry_found
                    status = $snapshot.state
                }
            }
        }
        if ($rule.type -eq "task") {
            foreach ($target in $rule.targets) {
                $taskParts = Split-TaskPath -FullPath $target.path
                $task = Get-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction SilentlyContinue
                if (-not $task) {
                    $tasks += @{ path = $target.path; notFound = $true }
                    continue
                }
                $tasks += @{
                    path = $target.path
                    enabled = $task.Settings.Enabled
                }
            }
        }
        if ($rule.type -eq "registry") {
            foreach ($target in $rule.targets) {
                $valueInfo = Get-RegistryValue -Path $target.path -Name $target.name
                $registry += @{
                    path = $target.path
                    name = $target.name
                    exists = $valueInfo['Exists']
                    value = $valueInfo['Value']
                    kind = $valueInfo['Kind']
                }
            }
        }
    }

    $backup = [ordered]@{
        id = $BackupId
        created_at = (Get-Date).ToString("o")
        rules = @($Rules | ForEach-Object { $_.id })
        services = $services
        tasks = $tasks
        registry = $registry
    }

    $backupFile = Join-Path $backupDir "backup.json"
    $backup | ConvertTo-Json -Depth 8 | Set-Content -Path $backupFile -Encoding UTF8

    return $backupFile
}

function Rollback-FromBackup {
    param([string]$BackupFile)

    $data = Get-Content -Raw -Path $BackupFile | ConvertFrom-Json

    $results = [ordered]@{
        services = @()
        tasks = @()
        registry = @()
    }

    foreach ($svc in $data.services) {
        if ($svc.notFound) {
            $results.services += @{ target = $svc.name; status = "NotFound" }
            continue
        }
        $errors = @()
        if ($null -ne $svc.startValue) {
            $regRes = Set-ServiceRegistryStartValue -Name $svc.name -StartValue $svc.startValue
            if ($regRes.status -ne "Ok") {
                $errors += $regRes.error
            }
        }
        $svcObj = Get-Service -Name $svc.name -ErrorAction SilentlyContinue
        if ($svcObj -and $svc.startType) {
            $startType = Normalize-ServiceStartType -StartType $svc.startType
            if ($startType -in @("Automatic", "Manual", "Disabled")) {
                try {
                    Set-Service -Name $svc.name -StartupType $startType -ErrorAction Stop
                } catch {
                    $errors += $_.Exception.Message
                }
            }
            if ($svc.status -eq "Running") {
                Start-Service -Name $svc.name -ErrorAction SilentlyContinue
            } elseif ($svc.status -eq "Stopped") {
                Stop-Service -Name $svc.name -Force -ErrorAction SilentlyContinue
            }
        }
        if ($errors.Count -gt 0) {
            $results.services += @{ target = $svc.name; status = "Error"; error = ($errors -join "; ") }
        } else {
            $results.services += @{ target = $svc.name; status = "Ok" }
        }
    }

    foreach ($task in $data.tasks) {
        if ($task.notFound) {
            $results.tasks += @{ target = $task.path; status = "NotFound" }
            continue
        }
        $taskParts = Split-TaskPath -FullPath $task.path
        try {
            if ($task.enabled) {
                Enable-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction Stop | Out-Null
            } else {
                Disable-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction Stop | Out-Null
            }
            $results.tasks += @{ target = $task.path; status = "Ok" }
        } catch {
            $results.tasks += @{ target = $task.path; status = "Error"; error = $_.Exception.Message }
        }
    }

    foreach ($reg in $data.registry) {
        $regPath = Convert-RegistryPath -Path $reg.path
        try {
            if ($reg.exists) {
                if (-not (Test-Path $regPath)) {
                    New-Item -Path $regPath -Force | Out-Null
                }
                if ($reg.kind) {
                    New-ItemProperty -Path $regPath -Name $reg.name -Value $reg.value -PropertyType $reg.kind -Force | Out-Null
                } else {
                    New-ItemProperty -Path $regPath -Name $reg.name -Value $reg.value -Force | Out-Null
                }
            } else {
                if (Test-Path $regPath) {
                    Remove-ItemProperty -Path $regPath -Name $reg.name -ErrorAction SilentlyContinue
                }
            }
            $results.registry += @{ target = "$($reg.path)\\$($reg.name)"; status = "Ok" }
        } catch {
            $results.registry += @{ target = "$($reg.path)\\$($reg.name)"; status = "Error"; error = $_.Exception.Message }
        }
    }

    return $results
}
