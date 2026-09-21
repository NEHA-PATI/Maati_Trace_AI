param(
  [string]$DbHost = "localhost",
  [int]$DbPort = 5432,
  [string]$Database = "maati_trace_ai",
  [string]$DbUser = "postgres",
  [string]$DbPassword = "",
  [switch]$FinalOnly
)

$ErrorActionPreference = "Stop"
$BackendRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
if ($DbPassword) { $env:PGPASSWORD = $DbPassword }

$Files = @()
if (-not $FinalOnly) {
  $Files += @(
    "20260901_01_crop_observation_service.sql",
    "20260901_02_crop_observation_seed_kala_jeera_config.sql",
    "20260901_03_crop_observation_local_media.sql",
    "20260901_04_crop_observation_seed_remaining_practice_fields.sql",
    "20260901_05_crop_observation_fix_missing_option_translations.sql",
    "20260903_06_crop_observation_evidence_tts.sql",
    "20260903_07_crop_observation_seed_coconut_mango.sql",
    "20260910_10_crop_observation_fix_missing_field_translations.sql",
    "20260910_11_crop_observation_seed_mango_defaults.sql"
    ,"20260911_12_crop_observation_seed_coconut_defaults.sql"
  ) | ForEach-Object { Join-Path $BackendRoot "data_contracts\sql\$_" }
}
$Files += Join-Path $BackendRoot "data_contracts\sql\20260909_09_crop_observation_production_finalize.sql"

foreach ($File in $Files) {
  Write-Host "Applying $(Split-Path $File -Leaf)..." -ForegroundColor Cyan
  & psql -v ON_ERROR_STOP=1 -h $DbHost -p $DbPort -U $DbUser -d $Database -f $File
  if ($LASTEXITCODE -ne 0) { throw "Migration failed: $File" }
}

Write-Host "Crop Observation migrations complete." -ForegroundColor Green
