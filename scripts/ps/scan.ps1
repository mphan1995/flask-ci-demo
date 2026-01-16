param(
    [Parameter(Mandatory = $true)][string]$RulesPath
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

$os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
$system = [ordered]@{
    computer = $env:COMPUTERNAME
    os = $os.Caption
    version = $os.Version
    build = $os.BuildNumber
}

$ruleResults = @()
foreach ($rule in $rules) {
    $statusInfo = Get-RuleStatus -Rule $rule
    $ruleResults += [ordered]@{
        id = $rule.id
        title = $rule.title
        group = $rule.group
        risk = $rule.risk
        type = $rule.type
        status = $statusInfo.status
        notes = $rule.notes
        details = $statusInfo.details
    }
}

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
$servicesRunning = @(
    $servicesAll |
        Where-Object { $_.state -eq "Running" } |
        Sort-Object -Property name |
        ForEach-Object {
            [ordered]@{
                name = $_.name
                display_name = $_.display_name
                start_mode = $_.start_mode
                start_value = $_.start_value
                state = $_.state
                cpu_percent = $_.cpu_percent
            }
        }
)
$servicesStopped = @($servicesAll | Where-Object { $_.state -eq "Stopped" })
$servicesDisabled = @($servicesAll | Where-Object { $_.start_mode -eq "Disabled" -or $_.start_value -eq 4 })
$servicesUnknown = @($servicesAll | Where-Object { $_.state -eq "Unknown" })

$servicesSummary = [ordered]@{
    total = $servicesAll.Count
    running = $servicesRunning.Count
    stopped = $servicesStopped.Count
    disabled = $servicesDisabled.Count
    unknown = $servicesUnknown.Count
    source = $serviceData.source
}

$suggested = @($ruleResults | Where-Object { $_.risk -eq "LOW" -and $_.status -eq "Enabled" } | ForEach-Object { $_.id })

$out = [ordered]@{
    ok = $true
    admin = (Test-Admin)
    system = $system
    rules = $ruleResults
    services_summary = $servicesSummary
    services_running = $servicesRunning
    services_all = $servicesAll
    suggested_actions = $suggested
}

$out | ConvertTo-Json -Depth 8
