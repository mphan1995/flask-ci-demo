function Split-TaskPath {
    param([string]$FullPath)
    $path = $FullPath.Trim()
    if (-not $path.StartsWith("\")) {
        $path = "\" + $path
    }
    $lastSlash = $path.LastIndexOf("\")
    if ($lastSlash -lt 0) {
        return @{ TaskPath = "\"; TaskName = $path }
    }
    $taskName = $path.Substring($lastSlash + 1)
    $taskPath = $path.Substring(0, $lastSlash + 1)
    return @{ TaskPath = $taskPath; TaskName = $taskName }
}

function Safe-DisableTask {
    param([string]$TaskPath)

    $taskParts = Split-TaskPath -FullPath $TaskPath
    $task = Get-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction SilentlyContinue
    if (-not $task) {
        return @{ status = "NotFound"; target = $TaskPath }
    }

    $stopError = $null
    if ($task.State -eq "Running") {
        try {
            Stop-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction Stop | Out-Null
        } catch {
            $stopError = $_.Exception.Message
        }
    }

    try {
        Disable-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction Stop | Out-Null
        if ($stopError) {
            return @{ status = "Error"; target = $TaskPath; error = "failed to stop running task: $stopError" }
        }
        $taskAfter = Get-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction SilentlyContinue
        if ($taskAfter -and $taskAfter.State -eq "Running") {
            return @{ status = "Error"; target = $TaskPath; error = "task still running" }
        }
        return @{ status = "Ok"; target = $TaskPath }
    } catch {
        return @{ status = "Error"; target = $TaskPath; error = $_.Exception.Message }
    }
}

function Safe-SetTaskEnabled {
    param(
        [string]$TaskPath,
        [bool]$Enabled
    )

    if (-not $Enabled) {
        $res = Safe-DisableTask -TaskPath $TaskPath
        if ($res.status -eq "Ok") {
            $res.enabled = $false
        }
        return $res
    }

    $taskParts = Split-TaskPath -FullPath $TaskPath
    $task = Get-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction SilentlyContinue
    if (-not $task) {
        return @{ status = "NotFound"; target = $TaskPath }
    }

    try {
        if ($Enabled) {
            Enable-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction Stop | Out-Null
        } else {
            Disable-ScheduledTask -TaskName $taskParts.TaskName -TaskPath $taskParts.TaskPath -ErrorAction Stop | Out-Null
        }
        return @{ status = "Ok"; target = $TaskPath; enabled = $Enabled }
    } catch {
        return @{ status = "Error"; target = $TaskPath; error = $_.Exception.Message }
    }
}
