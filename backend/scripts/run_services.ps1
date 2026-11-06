param(
    [switch]$Stop,
    [switch]$Restart,
    [switch]$WaitForHealth,
    [int]$HealthTimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"
$BackendRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
Set-Location $BackendRoot
$Python = Join-Path $BackendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { $Python = "python" }

$services = @(
    @{ Name="api-gateway"; Module="services.api_gateway_service.app.main:app"; Port=8000; Env="services/api_gateway_service/.env" },
    @{ Name="auth"; Module="services.auth_service.app.main:app"; Port=8002; Env="services/auth_service/.env" },
    @{ Name="profile"; Module="services.profile_service.app.main:app"; Port=8003; Env="services/profile_service/.env" },
    @{ Name="boundary-index"; Module="services.boundary_index_service.app.main:app"; Port=8004; Env="services/boundary_index_service/.env" },
    @{ Name="district-boundary"; Module="services.district_boundary_service.app.main:app"; Port=8005; Env="services/district_boundary_service/.env" },
    @{ Name="farm-registry"; Module="services.farm_registry_service.app.main:app"; Port=8006; Env="services/farm_registry_service/.env" },
    @{ Name="stac-catalog"; Module="services.stac_catalog_service.app.main:app"; Port=8007; Env="services/stac_catalog_service/.env" },
    @{ Name="raster-processor"; Module="services.raster_processor_service.app.main:app"; Port=8008; Env="services/raster_processor_service/.env" },
    @{ Name="lakehouse-writer"; Module="services.lakehouse_writer_service.app.main:app"; Port=8009; Env="services/lakehouse_writer_service/.env" },
    @{ Name="hot-stream"; Module="services.hot_stream_orchestrator_service.app.main:app"; Port=8010; Env="services/hot_stream_orchestrator_service/.env" },
    @{ Name="analytics-query"; Module="services.analytics_query_service.app.main:app"; Port=8011; Env="services/analytics_query_service/.env" },
    @{ Name="observability"; Module="services.observability_service.app.main:app"; Port=8014; Env="services/observability_service/.env" },
    @{ Name="crop-observation"; Module="services.crop_observation_service.app.main:app"; Port=8015; Env="services/crop_observation_service/.env" },
    @{ Name="fpo-management"; Module="services.fpo_management_service.app.main:app"; Port=8016; Env="services/fpo_management_service/.env" }
)

function Get-Listener([int]$Port) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
}

if ($Stop -or $Restart) {
    foreach ($service in $services) {
        $listeners = @(Get-Listener $service.Port)
        foreach ($listener in $listeners) {
            Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    if ($Stop) { exit 0 }
    Start-Sleep -Seconds 1
}

foreach ($service in $services) {
    if (Get-Listener $service.Port) {
        Write-Host "$($service.Name): already listening on $($service.Port)"
        continue
    }
    $envFile = Join-Path $BackendRoot $service.Env
    if (-not (Test-Path -LiteralPath $envFile)) {
        throw "Missing service env file: $envFile"
    }
    $logDir = Join-Path $BackendRoot "logs\services"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $stdout = Join-Path $logDir "$($service.Name).out.log"
    $stderr = Join-Path $logDir "$($service.Name).err.log"
    $arguments = "-m uvicorn $($service.Module) --host 0.0.0.0 --port $($service.Port) --env-file `"$envFile`""
    # settings.py resolves its env file during module import. Pass the same
    # service-specific path explicitly so startup does not depend on whether
    # Uvicorn has loaded --env-file before importing the application.
    $env:MAATITRACE_ENV_FILE = $envFile
    Start-Process -FilePath $Python -ArgumentList $arguments -WorkingDirectory $BackendRoot -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden | Out-Null
    Write-Host "$($service.Name): started on $($service.Port) using $($service.Env)"
}

if ($WaitForHealth) {
    $deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)
    foreach ($service in $services) {
        $ready = $false
        while ((Get-Date) -lt $deadline) {
            try {
                $response = Invoke-WebRequest -Uri "http://127.0.0.1:$($service.Port)/health/ready" -UseBasicParsing -TimeoutSec 3
                if ($response.StatusCode -eq 200) { $ready = $true; break }
            } catch { Start-Sleep -Milliseconds 500 }
        }
        if ($ready) { Write-Host "$($service.Name): ready" } else { Write-Warning "$($service.Name): not ready" }
    }
}
