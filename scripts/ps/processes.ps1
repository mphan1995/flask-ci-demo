param()

. "$PSScriptRoot\common.ps1"

$processes = @()
$processSource = "cim"
try {
    $items = Get-CimInstance Win32_Process -ErrorAction Stop
    foreach ($proc in $items) {
        $processes += [ordered]@{
            name = $proc.Name
            pid = $proc.ProcessId
            working_set = if ($null -ne $proc.WorkingSetSize) { [int64]$proc.WorkingSetSize } else { 0 }
            path = $proc.ExecutablePath
        }
    }
} catch {
    $processSource = "get-process"
    try {
        $items = Get-Process
    } catch {
        $items = @()
        $processSource = "none"
    }
    foreach ($proc in $items) {
        $name = $proc.ProcessName
        if ($name -and -not $name.EndsWith(".exe")) {
            $name = "$name.exe"
        }
        $processes += [ordered]@{
            name = $name
            pid = $proc.Id
            working_set = if ($null -ne $proc.WorkingSet64) { [int64]$proc.WorkingSet64 } else { 0 }
            path = $proc.Path
        }
    }
}

$services = @()
$serviceSource = "cim"
try {
    $svcItems = Get-CimInstance Win32_Service -ErrorAction Stop
    foreach ($svc in $svcItems) {
        $services += [ordered]@{
            name = $svc.Name
            display_name = $svc.DisplayName
            state = $svc.State
            start_mode = $svc.StartMode
            pid = $svc.ProcessId
        }
    }
} catch {
    $serviceSource = "get-service"
    try {
        $svcItems = Get-Service
    } catch {
        $svcItems = @()
        $serviceSource = "none"
    }
    foreach ($svc in $svcItems) {
        $services += [ordered]@{
            name = $svc.Name
            display_name = $svc.DisplayName
            state = $svc.Status.ToString()
            start_mode = $svc.StartType.ToString()
            pid = $null
        }
    }
}

$out = [ordered]@{
    ok = $true
    process_source = $processSource
    service_source = $serviceSource
    processes = $processes
    services = $services
}

$out | ConvertTo-Json -Depth 8
