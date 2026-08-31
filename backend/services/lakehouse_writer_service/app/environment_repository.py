from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine


class EnvironmentRepositoryError(RuntimeError):
    pass


@dataclass(frozen=True)
class TableSpec:
    table: str
    columns: tuple[str, ...]
    conflict_columns: tuple[str, ...]


COMMON = (
    "farm_id", "farmer_id", "fpo_id", "state_name", "district_name",
    "district_code", "block_name", "block_code",
)
PROVENANCE = (
    "source_provider", "source_collection", "source_item_id", "source_datetime",
    "processing_version", "parquet_uri",
)


TABLE_SPECS: dict[str, TableSpec] = {
    "sentinel_1_rtc": TableSpec(
        table="h3_sentinel1_features",
        columns=COMMON + (
            "snapshot_date", "scene_id", "scene_datetime", "h3_resolution", "h3_index",
            "mean_vv", "mean_vh", "mean_vv_db", "mean_vh_db", "vh_vv_ratio", "rvi",
            "observed_area_m2", "valid_area_m2", "invalid_area_m2", "valid_fraction",
            "orbit_direction", "relative_orbit", "native_resolution_m", "source_assets_used",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "snapshot_date", "scene_id", "h3_index", "processing_version"),
    ),
    "landsat_c2_l2": TableSpec(
        table="h3_landsat_features",
        columns=COMMON + (
            "snapshot_date", "scene_id", "scene_datetime", "scene_cloud_cover", "platform", "sensor",
            "h3_resolution", "h3_index", "mean_blue", "mean_green", "mean_red", "mean_nir",
            "mean_swir16", "mean_swir22", "ndvi", "ndmi", "msi", "bsi", "nbr",
            "surface_temp_k", "surface_temp_c", "observed_area_m2", "valid_area_m2",
            "invalid_area_m2", "valid_fraction", "optical_resolution_m", "thermal_resolution_m",
            "source_assets_used",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "snapshot_date", "scene_id", "h3_index", "processing_version"),
    ),
    "gpm_imerg": TableSpec(
        table="farm_weather_observations",
        columns=COMMON + (
            "observation_date", "precipitation_mm", "source_unit", "source_resolution_m",
            "aggregation_method", "source_dataset", "source_product_version", "source_item_ids",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "observation_date", "source_dataset", "processing_version"),
    ),
    "cop_dem_glo30": TableSpec(
        table="h3_terrain_features",
        columns=COMMON + (
            "h3_index", "h3_resolution", "mean_elevation_m", "min_elevation_m", "max_elevation_m",
            "mean_slope_deg", "max_slope_deg", "mean_aspect_deg", "observed_area_m2",
            "valid_area_m2", "valid_fraction", "source_dataset", "source_version",
            "native_resolution_m", "source_assets_used",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "h3_index", "source_dataset", "processing_version"),
    ),
    "esa_worldcover": TableSpec(
        table="h3_landcover_features",
        columns=COMMON + (
            "h3_index", "h3_resolution", "reference_year", "dominant_class", "dominant_fraction",
            "tree_cover_fraction", "shrubland_fraction", "grassland_fraction", "cropland_fraction",
            "built_fraction", "bare_sparse_fraction", "snow_ice_fraction", "permanent_water_fraction",
            "herbaceous_wetland_fraction", "mangrove_fraction", "moss_lichen_fraction",
            "observed_area_m2", "valid_area_m2", "valid_fraction", "source_dataset", "source_version",
            "native_resolution_m", "source_assets_used",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "h3_index", "reference_year", "source_dataset", "processing_version"),
    ),
    "jrc_surface_water": TableSpec(
        table="h3_surface_water_features",
        columns=COMMON + (
            "h3_index", "h3_resolution", "water_occurrence_pct", "water_recurrence_pct",
            "water_seasonality_months", "permanent_water_fraction", "historic_extent_fraction",
            "observed_area_m2", "valid_area_m2", "valid_fraction", "source_dataset",
            "source_reference_period", "native_resolution_m", "source_assets_used",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "h3_index", "source_dataset", "processing_version"),
    ),
    "era5_land": TableSpec(
        table="farm_reanalysis_daily",
        columns=COMMON + (
            "observation_date", "dataset_key", "temperature_mean_c", "temperature_min_c",
            "temperature_max_c", "dewpoint_mean_c", "skin_temperature_mean_c",
            "soil_water_0_7", "soil_water_7_28", "soil_water_28_100", "soil_water_100_289",
            "source_resolution_m", "aggregation_method", "source_version",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "observation_date", "dataset_key", "processing_version"),
    ),
    "soilgrids_v2": TableSpec(
        table="h3_soilgrids_features",
        columns=COMMON + (
            "h3_index", "h3_resolution", "property_key", "depth_top_cm", "depth_bottom_cm",
            "quantile", "value", "unit", "valid_fraction", "source_dataset", "source_version",
            "native_resolution_m", "source_assets_used",
        ) + PROVENANCE,
        conflict_columns=(
            "farm_id", "h3_index", "property_key", "depth_top_cm", "depth_bottom_cm",
            "quantile", "processing_version",
        ),
    ),
    "smap_l4_sm": TableSpec(
        table="farm_smap_observations",
        columns=COMMON + (
            "observed_at", "surface_soil_moisture", "root_zone_soil_moisture",
            "source_dataset", "source_version", "source_resolution_m", "aggregation_method",
            "source_granule_id",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "observed_at", "source_dataset", "processing_version"),
    ),
    "modis_et": TableSpec(
        table="farm_modis_et_observations",
        columns=COMMON + (
            "period_start", "period_end", "et_mm", "pet_mm", "latent_heat_j_m2_day",
            "potential_latent_heat_j_m2_day", "valid_fraction", "source_product", "source_version",
            "native_resolution_m", "aggregation_method",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "period_start", "source_product", "processing_version"),
    ),
    "modis_lai_fpar": TableSpec(
        table="farm_modis_vegetation_observations",
        columns=COMMON + (
            "period_start", "period_end", "lai", "fpar", "lai_stddev", "fpar_stddev",
            "valid_fraction", "source_product", "source_version", "native_resolution_m",
            "aggregation_method",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "period_start", "source_product", "processing_version"),
    ),
    "weather_forecast": TableSpec(
        table="farm_weather_forecasts",
        columns=COMMON + (
            "provider", "model", "issued_at", "valid_at", "temperature_2m_c",
            "relative_humidity_2m", "precipitation_mm", "wind_speed_10m", "wind_direction_10m",
            "shortwave_radiation", "et0_mm", "vapour_pressure_deficit", "source_resolution_m",
            "aggregation_method",
        ) + PROVENANCE,
        conflict_columns=("farm_id", "provider", "issued_at", "valid_at", "processing_version"),
    ),
}


def get_table_spec(dataset_key: str) -> TableSpec:
    spec = TABLE_SPECS.get(dataset_key)
    if spec is None:
        raise EnvironmentRepositoryError(f"Unsupported lakehouse dataset_key: {dataset_key}")
    return spec


def upsert_environment_rows(dataset_key: str, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    spec = get_table_spec(dataset_key)
    columns = list(spec.columns)
    col_sql = ", ".join(columns)
    values_sql = ", ".join(f":{column}" for column in columns)
    conflict_sql = ", ".join(spec.conflict_columns)
    update_columns = [column for column in columns if column not in spec.conflict_columns]
    update_sql = ",\n".join(
        f"{column} = EXCLUDED.{column}" for column in update_columns if column != "created_at"
    )
    query = text(
        f"""
        INSERT INTO {spec.table} ({col_sql})
        VALUES ({values_sql})
        ON CONFLICT ({conflict_sql}) DO UPDATE SET
            {update_sql},
            updated_at = now();
        """
    )

    prepared = []
    for row in rows:
        prepared.append({column: row.get(column) for column in columns})
    try:
        with engine.begin() as conn:
            conn.execute(query, prepared)
    except SQLAlchemyError as exc:
        raise EnvironmentRepositoryError(
            f"Failed writing {dataset_key} to {spec.table}: {exc}"
        ) from exc
    return len(rows)
