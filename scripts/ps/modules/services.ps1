function Get-ObjectPropertyValue {
    param(
        [object]$Object,
        [string]$Name
    )
    if ($null -eq $Object) {
        return $null
    }
    $prop = $Object.PSObject.Properties[$Name]
    if ($null -eq $prop) {
        return $null
    }
    return $prop.Value
}

function Normalize-ServiceStartType {
    param([string]$StartType)
    if (-not $StartType) {
        return "Manual"
    }
    $normalized = $StartType.ToString().Trim().ToLowerInvariant()
    switch ($normalized) {
        "auto" { return "Automatic" }
        "automatic" { return "Automatic" }
        "automatic (delayed start)" { return "Automatic" }
        "automaticdelayedstart" { return "Automatic" }
        "manual" { return "Manual" }
        "disabled" { return "Disabled" }
        "boot" { return "Boot" }
        "system" { return "System" }
        default { return "Manual" }
    }
}

function Convert-ServiceStartValueToType {
    param([int]$Value)
    switch ($Value) {
        0 { return "Boot" }
        1 { return "System" }
        2 { return "Automatic" }
        3 { return "Manual" }
        4 { return "Disabled" }
        default { return "Manual" }
    }
}

function Convert-ServiceStartTypeToValue {
    param([string]$StartType)
    $normalized = Normalize-ServiceStartType -StartType $StartType
    switch ($normalized) {
        "Boot" { return 0 }
        "System" { return 1 }
        "Automatic" { return 2 }
        "Manual" { return 3 }
        "Disabled" { return 4 }
        default { return 3 }
    }
}

function Resolve-ServiceStartSpec {
    param([object]$StartType)
    if ($null -eq $StartType) {
        return @{ StartType = $null; StartValue = $null }
    }
    if ($StartType -is [int] -or ($StartType -is [string] -and $StartType -match '^\d+$')) {
        $value = [int]$StartType
        return @{
            StartType = (Convert-ServiceStartValueToType -Value $value)
            StartValue = $value
        }
    }
    $normalized = Normalize-ServiceStartType -StartType $StartType
    return @{
        StartType = $normalized
        StartValue = (Convert-ServiceStartTypeToValue -StartType $normalized)
    }
}

function Test-IsServiceType {
    param([int]$TypeValue)
    if ($null -eq $TypeValue) {
        return $true
    }
    return (($TypeValue -band 0x10) -ne 0 -or ($TypeValue -band 0x20) -ne 0)
}

function Get-ServiceRegistryInfo {
    param([string]$Name)
    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\$Name"
    if (-not (Test-Path $regPath)) {
        return @{ Exists = $false; Path = $regPath }
    }
    $props = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
    $startRaw = Get-ObjectPropertyValue -Object $props -Name "Start"
    $startValue = if ($null -ne $startRaw) { [int]$startRaw } else { $null }
    $displayName = Get-ObjectPropertyValue -Object $props -Name "DisplayName"
    $typeValue = Get-ObjectPropertyValue -Object $props -Name "Type"
    return @{
        Exists = $true
        Path = $regPath
        StartValue = $startValue
        DisplayName = $displayName
        TypeValue = $typeValue
    }
}

function Set-ServiceRegistryStartValue {
    param(
        [string]$Name,
        [int]$StartValue
    )
    $regInfo = Get-ServiceRegistryInfo -Name $Name
    if (-not $regInfo.Exists) {
        return @{ status = "NotFound"; target = $Name; error = "registry key not found" }
    }
    try {
        $current = Get-ItemProperty -Path $regInfo.Path -Name Start -ErrorAction SilentlyContinue
        if ($current -and $null -ne $current.Start) {
            Set-ItemProperty -Path $regInfo.Path -Name Start -Value $StartValue -Force -ErrorAction Stop | Out-Null
        } else {
            New-ItemProperty -Path $regInfo.Path -Name Start -Value $StartValue -PropertyType DWord -Force -ErrorAction Stop | Out-Null
        }
        $verifyProps = Get-ItemProperty -Path $regInfo.Path -Name Start -ErrorAction SilentlyContinue
        $verify = if ($verifyProps) { $verifyProps.Start } else { $null }
        if ($verify -ne $StartValue) {
            return @{ status = "Error"; target = $Name; error = "registry start value not set correctly" }
        }
        return @{ status = "Ok"; target = $Name; start_value = $StartValue }
    } catch {
        return @{ status = "Error"; target = $Name; error = $_.Exception.Message }
    }
}

function Get-ServiceSnapshot {
    param([string]$Name)
    $svc = Get-Service -Name $Name -ErrorAction SilentlyContinue
    $cim = Get-CimInstance -ClassName Win32_Service -Filter "Name='$Name'" -ErrorAction SilentlyContinue
    $regInfo = Get-ServiceRegistryInfo -Name $Name
    $found = $false
    if ($svc -or $cim -or $regInfo.Exists) {
        $found = $true
    }
    $state = "Unknown"
    if ($svc) {
        $state = $svc.Status.ToString()
    } elseif ($cim) {
        $state = $cim.State
    }
    $startMode = $null
    if ($cim) {
        $startMode = $cim.StartMode
    } elseif ($svc) {
        $startMode = $svc.StartType.ToString()
    } elseif ($regInfo.Exists -and $null -ne $regInfo.StartValue) {
        $startMode = Convert-ServiceStartValueToType -Value $regInfo.StartValue
    }
    $displayName = if ($svc) { $svc.DisplayName } elseif ($regInfo.DisplayName) { $regInfo.DisplayName } else { $Name }
    return [ordered]@{
        name = $Name
        display_name = $displayName
        found = $found
        state = $state
        start_mode = $startMode
        start_value = $regInfo.StartValue
        registry_found = $regInfo.Exists
    }
}

function Get-AllServices {
    $items = @{}
    $source = "cim"
    try {
        $services = Get-CimInstance -ClassName Win32_Service -ErrorAction Stop
        foreach ($svc in $services) {
            $items[$svc.Name] = [ordered]@{
                name = $svc.Name
                display_name = $svc.DisplayName
                state = $svc.State
                start_mode = $svc.StartMode
                start_value = $null
                pid = if ($null -ne $svc.ProcessId) { [int]$svc.ProcessId } else { $null }
                source = "cim"
            }
        }
    } catch {
        $source = "get-service"
        $services = @()
        try {
            $services = Get-Service
        } catch {
            $services = @()
            $source = "none"
        }
        foreach ($svc in $services) {
            $items[$svc.Name] = [ordered]@{
                name = $svc.Name
                display_name = $svc.DisplayName
                state = $svc.Status.ToString()
                start_mode = $svc.StartType.ToString()
                start_value = $null
                pid = $null
                source = "get-service"
            }
        }
    }

    $regRoot = "HKLM:\SYSTEM\CurrentControlSet\Services"
    if (Test-Path $regRoot) {
        Get-ChildItem -Path $regRoot | ForEach-Object {
            $name = $_.PSChildName
            $props = Get-ItemProperty -Path $_.PSPath -ErrorAction SilentlyContinue
            $typeValue = Get-ObjectPropertyValue -Object $props -Name "Type"
            if (-not (Test-IsServiceType -TypeValue $typeValue)) {
                return
            }
            $startRaw = Get-ObjectPropertyValue -Object $props -Name "Start"
            $startValue = if ($null -ne $startRaw) { [int]$startRaw } else { $null }
            $displayName = Get-ObjectPropertyValue -Object $props -Name "DisplayName"
            if ($items.ContainsKey($name)) {
                $item = $items[$name]
                if ($null -ne $startValue) { $item.start_value = $startValue }
                if (-not $item.display_name -and $displayName) { $item.display_name = $displayName }
                if (-not $item.start_mode -and $null -ne $startValue) { $item.start_mode = Convert-ServiceStartValueToType -Value $startValue }
                $items[$name] = $item
            } else {
                $items[$name] = [ordered]@{
                    name = $name
                    display_name = $displayName
                    state = "Unknown"
                    start_mode = if ($null -ne $startValue) { Convert-ServiceStartValueToType -Value $startValue } else { $null }
                    start_value = $startValue
                    pid = $null
                    source = "registry"
                }
            }
        }
    }

    $list = $items.Values | Sort-Object -Property name
    return [ordered]@{
        items = $list
        source = $source
    }
}

function Safe-SetServiceStartType {
    param(
        [string]$Name,
        [string]$StartType,
        [bool]$StopService,
        [bool]$StartService = $false
    )

    $startSpec = Resolve-ServiceStartSpec -StartType $StartType
    $svc = Get-Service -Name $Name -ErrorAction SilentlyContinue
    $regInfo = Get-ServiceRegistryInfo -Name $Name
    if (-not $svc -and -not $regInfo.Exists) {
        return @{ status = "NotFound"; target = $Name }
    }

    $normalized = $startSpec.StartType
    $errors = @()
    if ($svc -and $normalized -in @("Automatic", "Manual", "Disabled")) {
        try {
            Set-Service -Name $Name -StartupType $normalized -ErrorAction Stop
        } catch {
            $errors += $_.Exception.Message
        }

        if ($errors.Count -gt 0) {
            $scStart = switch ($normalized) {
                "Automatic" { "auto" }
                "Manual" { "demand" }
                "Disabled" { "disabled" }
                default { "demand" }
            }
            $scOutput = & sc.exe config $Name start= $scStart 2>&1
            if ($LASTEXITCODE -ne 0) {
                $errors += "sc.exe config failed: $scOutput"
            }
        }
    }

    if ($null -ne $startSpec.StartValue) {
        $regRes = Set-ServiceRegistryStartValue -Name $Name -StartValue $startSpec.StartValue
        if ($regRes.status -ne "Ok") {
            if ($regRes.error) {
                $errors += $regRes.error
            } else {
                $errors += "registry update failed"
            }
        }
    }

    $modeOk = $true
    $post = Get-ServiceSnapshot -Name $Name
    if ($normalized -and $post.start_mode) {
        if ((Normalize-ServiceStartType -StartType $post.start_mode) -ne $normalized) {
            $modeOk = $false
        }
    }
    if (-not $modeOk) {
        $errors += "start mode not set to $normalized"
    }
    if ($null -ne $startSpec.StartValue -and $null -ne $post.start_value -and $post.start_value -ne $startSpec.StartValue) {
        $errors += "start value not set to $($startSpec.StartValue)"
    }

    if ($StopService -and $svc -and $svc.Status -eq "Running") {
        try {
            Stop-Service -Name $Name -Force -ErrorAction Stop
        } catch {
            $errors += $_.Exception.Message
        }
        $svc = Get-Service -Name $Name -ErrorAction SilentlyContinue
        if ($svc -and $svc.Status -eq "Running") {
            $errors += "service still running"
        }
    }

    if ($StartService -and $svc -and $normalized -ne "Disabled") {
        try {
            Start-Service -Name $Name -ErrorAction Stop
        } catch {
            $errors += $_.Exception.Message
        }
        $svc = Get-Service -Name $Name -ErrorAction SilentlyContinue
        if ($svc -and $svc.Status -ne "Running") {
            $errors += "service not running"
        }
    }

    if ($errors.Count -gt 0) {
        return @{
            status = "Error"
            target = $Name
            error = ($errors -join "; ")
            start_mode = $post.start_mode
            start_value = $post.start_value
            state = $post.state
        }
    }
    return @{
        status = "Ok"
        target = $Name
        start_mode = $post.start_mode
        start_value = $post.start_value
        state = $post.state
    }
}
