function Convert-RegistryPath {
    param([string]$Path)
    if (-not $Path) {
        return $Path
    }
    $normalized = $Path.Trim().Replace("/", "\")
    $upper = $normalized.ToUpperInvariant()
    if ($upper.StartsWith("REGISTRY::")) {
        return $normalized
    }
    if ($upper.StartsWith("HKLM:\")) {
        return "Registry::HKEY_LOCAL_MACHINE\" + $normalized.Substring(6)
    }
    if ($upper.StartsWith("HKLM\")) {
        return "Registry::HKEY_LOCAL_MACHINE\" + $normalized.Substring(5)
    }
    if ($upper.StartsWith("HKCU:\")) {
        return "Registry::HKEY_CURRENT_USER\" + $normalized.Substring(6)
    }
    if ($upper.StartsWith("HKCU\")) {
        return "Registry::HKEY_CURRENT_USER\" + $normalized.Substring(5)
    }
    if ($upper.StartsWith("HKEY_LOCAL_MACHINE\")) {
        return "Registry::" + $normalized
    }
    if ($upper.StartsWith("HKEY_CURRENT_USER\")) {
        return "Registry::" + $normalized
    }
    return $normalized
}

function Get-RegistryValue {
    param(
        [string]$Path,
        [string]$Name
    )
    $regPath = Convert-RegistryPath -Path $Path
    if (-not (Test-Path $regPath)) {
        return @{ Exists = $false; PathExists = $false }
    }

    try {
        $item = Get-Item -Path $regPath -ErrorAction Stop
        if ($item.GetValueNames() -contains $Name) {
            return @{
                Exists = $true
                PathExists = $true
                Value = $item.GetValue($Name)
                Kind = $item.GetValueKind($Name).ToString()
            }
        }
        return @{ Exists = $false; PathExists = $true }
    } catch {
        return @{ Exists = $false; PathExists = $false; Error = $_.Exception.Message }
    }
}

function Safe-SetRegistry {
    param(
        [string]$Path,
        [string]$Name,
        [object]$Value,
        [string]$ValueType
    )

    $regPath = Convert-RegistryPath -Path $Path
    try {
        if (-not (Test-Path $regPath)) {
            New-Item -Path $regPath -Force | Out-Null
        }
        $current = Get-RegistryValue -Path $Path -Name $Name
        $typeMismatch = $false
        if ($current['Exists'] -and $ValueType -and $current['Kind']) {
            $currentType = $current['Kind'].ToString().ToLowerInvariant()
            $desiredType = $ValueType.ToString().ToLowerInvariant()
            if ($currentType -ne $desiredType) {
                $typeMismatch = $true
            }
        }
        if ($current['Exists'] -and $typeMismatch) {
            Remove-ItemProperty -Path $regPath -Name $Name -ErrorAction Stop | Out-Null
            $current = @{ Exists = $false }
        }
        if ($current['Exists']) {
            Set-ItemProperty -Path $regPath -Name $Name -Value $Value -ErrorAction Stop | Out-Null
        } else {
            if ($ValueType) {
                New-ItemProperty -Path $regPath -Name $Name -Value $Value -PropertyType $ValueType -Force -ErrorAction Stop | Out-Null
            } else {
                New-ItemProperty -Path $regPath -Name $Name -Value $Value -Force -ErrorAction Stop | Out-Null
            }
        }

        $verify = Get-RegistryValue -Path $Path -Name $Name
        if (-not $verify['Exists'] -or $verify['Value'] -ne $Value) {
            return @{ status = "Error"; target = "$Path\\$Name"; error = "registry value not set correctly" }
        }
        if ($ValueType -and $verify['Kind']) {
            $verifyType = $verify['Kind'].ToString().ToLowerInvariant()
            $desiredType = $ValueType.ToString().ToLowerInvariant()
            if ($verifyType -ne $desiredType) {
                return @{ status = "Error"; target = "$Path\\$Name"; error = "registry value type mismatch" }
            }
        }
        return @{ status = "Ok"; target = "$Path\\$Name" }
    } catch {
        return @{ status = "Error"; target = "$Path\\$Name"; error = $_.Exception.Message }
    }
}

function Safe-RemoveRegistryValue {
    param(
        [string]$Path,
        [string]$Name
    )

    $regPath = Convert-RegistryPath -Path $Path
    try {
        if (-not (Test-Path $regPath)) {
            return @{ status = "Ok"; target = "$Path\\$Name"; removed = $false }
        }
        $current = Get-ItemProperty -Path $regPath -Name $Name -ErrorAction SilentlyContinue
        if ($null -eq $current) {
            return @{ status = "Ok"; target = "$Path\\$Name"; removed = $false }
        }
        Remove-ItemProperty -Path $regPath -Name $Name -ErrorAction Stop | Out-Null
        $verify = Get-RegistryValue -Path $Path -Name $Name
        if ($verify['Exists']) {
            return @{ status = "Error"; target = "$Path\\$Name"; error = "registry value still present" }
        }
        return @{ status = "Ok"; target = "$Path\\$Name"; removed = $true }
    } catch {
        return @{ status = "Error"; target = "$Path\\$Name"; error = $_.Exception.Message }
    }
}
