#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-maati_trace_ai}"
DB_USER="${POSTGRES_USER:-postgres}"
BACKEND_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FINAL_ONLY="${FINAL_ONLY:-0}"

files=()
if [[ "$FINAL_ONLY" != "1" ]]; then
  files+=(
    "$BACKEND_ROOT/data_contracts/sql/20260901_01_crop_observation_service.sql"
    "$BACKEND_ROOT/data_contracts/sql/20260901_02_crop_observation_seed_kala_jeera_config.sql"
    "$BACKEND_ROOT/data_contracts/sql/20260901_03_crop_observation_local_media.sql"
    "$BACKEND_ROOT/data_contracts/sql/20260901_04_crop_observation_seed_remaining_practice_fields.sql"
    "$BACKEND_ROOT/data_contracts/sql/20260901_05_crop_observation_fix_missing_option_translations.sql"
    "$BACKEND_ROOT/data_contracts/sql/20260903_06_crop_observation_evidence_tts.sql"
    "$BACKEND_ROOT/data_contracts/sql/20260903_07_crop_observation_seed_coconut_mango.sql"
    "$BACKEND_ROOT/data_contracts/sql/20260910_10_crop_observation_fix_missing_field_translations.sql"
    "$BACKEND_ROOT/data_contracts/sql/20260910_11_crop_observation_seed_mango_defaults.sql"
    "$BACKEND_ROOT/data_contracts/sql/20260911_12_crop_observation_seed_coconut_defaults.sql"
  )
fi
files+=("$BACKEND_ROOT/data_contracts/sql/20260909_09_crop_observation_production_finalize.sql")

for file in "${files[@]}"; do
  echo "Applying $(basename "$file")..."
  psql -v ON_ERROR_STOP=1 -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$file"
done

echo "Crop Observation migrations complete."
