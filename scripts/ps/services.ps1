param()

. "$PSScriptRoot\common.ps1"

$serviceData = Get-AllServices
$servicesAll = @($serviceData.items)
$cpuMap = @{}
$hasPid = $false
foreach ($service in $servicesAll) {
    if ($service.pid -and [int]$service.pid -gt 0) {
        $hasPid = $true
        break
    }
}
if ($hasPid) {
    try {
        $cpuMap = Get-ProcessCpuUsage -SampleMs 750
    } catch {
        $cpuMap = @{}
    }
}
foreach ($service in $servicesAll) {
    $pid = $service.pid
    if ($pid -and $cpuMap.ContainsKey($pid)) {
        $service.cpu_percent = $cpuMap[$pid]
    } else {
        $service.cpu_percent = $null
    }
}

$servicesRunning = @($servicesAll | Where-Object { $_.state -eq "Running" })
$servicesStopped = @($servicesAll | Where-Object { $_.state -eq "Stopped" })
$servicesDisabled = @($servicesAll | Where-Object { $_.start_mode -eq "Disabled" -or $_.start_value -eq 4 })
$servicesUnknown = @($servicesAll | Where-Object { $_.state -eq "Unknown" })

$summary = [ordered]@{
    total = $servicesAll.Count
    running = $servicesRunning.Count
    stopped = $servicesStopped.Count
    disabled = $servicesDisabled.Count
    unknown = $servicesUnknown.Count
    source = $serviceData.source
}

$out = [ordered]@{
    ok = $true
    summary = $summary
    services = $servicesAll
}

$out | ConvertTo-Json -Depth 8
