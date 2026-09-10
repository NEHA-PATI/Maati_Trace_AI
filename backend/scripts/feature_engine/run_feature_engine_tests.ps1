$ErrorActionPreference = "Stop"
$BackendRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $BackendRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$env:PYTHONPATH = "$BackendRoot"

Write-Host "[1/3] Compiling backend Python..."
python -m compileall -q services shared tests\feature_engine

Write-Host "[2/3] Running feature-engine tests..."
pytest -q tests\feature_engine

Write-Host "[3/3] Running farm registration schema + service tests..."
pytest -q services\farm_registry_service\tests\test_schemas.py services\farm_registry_service\tests\test_service.py tests\feature_engine

Write-Host "Feature-engine focused validation completed."
