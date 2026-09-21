$ErrorActionPreference = "Stop"
$BackendRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $BackendRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$env:PYTHONPATH = "$BackendRoot"

Write-Host "[1/4] Compiling backend Python..."
python -m compileall -q services shared tests

Write-Host "[2/4] Running feature-engine tests..."
pytest -q tests\feature_engine

Write-Host "[3/4] Running farm registration schema + service tests..."
pytest -q services\farm_registry_service\tests\test_schemas.py services\farm_registry_service\tests\test_service.py tests\feature_engine

Write-Host "[4/4] Running complete backend test suite..."
pytest -q

Write-Host "Backend validation completed."
