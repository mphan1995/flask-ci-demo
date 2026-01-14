Set-StrictMode -Version Latest

$moduleRoot = Join-Path $PSScriptRoot "modules"
. (Join-Path $moduleRoot "core.ps1")
. (Join-Path $moduleRoot "registry.ps1")
. (Join-Path $moduleRoot "services.ps1")
. (Join-Path $moduleRoot "tasks.ps1")
. (Join-Path $moduleRoot "rules.ps1")
