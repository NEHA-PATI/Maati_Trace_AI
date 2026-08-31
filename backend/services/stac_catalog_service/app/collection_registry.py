from __future__ import annotations

from typing import Any

from services.stac_catalog_service.app.dataset_contracts import (
    AssetContract,
    DatasetContract,
    ProviderContract,
    StorageContract,
)


# IMPORTANT:
# - Sentinel-2 key and legacy shape are preserved.
# - The registry now also describes how each dataset is acquired, processed,
#   and persisted. Scientific transformations remain in raster_processor_service.
# - Generic MODIS/VIIRS has been replaced by product-specific entries.

_DATASET_CONTRACTS: dict[str, DatasetContract] = {
    "sentinel_2_l2a": DatasetContract(
        dataset_key="sentinel_2_l2a",
        display_name="Sentinel-2 L2A",
        priority=1,
        category="optical_satellite",
        temporal_type="scene",
        processor_key="sentinel2_existing",
        providers={
            "planetary_computer": ProviderContract(
                source_adapter="stac", collection_ids=["sentinel-2-l2a"], priority=1
            ),
            "earth_search": ProviderContract(
                source_adapter="stac",
                collection_ids=["sentinel-2-l2a", "sentinel-2-c1-l2a"],
                priority=2,
            ),
            "copernicus": ProviderContract(
                source_adapter="stac", collection_ids=["SENTINEL-2"], priority=3
            ),
        },
        assets=[
            AssetContract(canonical_name="coastal", aliases=["B01", "coastal"], required=False),
            AssetContract(canonical_name="blue", aliases=["B02", "blue"]),
            AssetContract(canonical_name="green", aliases=["B03", "green"]),
            AssetContract(canonical_name="red", aliases=["B04", "red"]),
            AssetContract(canonical_name="rededge1", aliases=["B05", "rededge1"], required=False),
            AssetContract(canonical_name="rededge2", aliases=["B06", "rededge2"], required=False),
            AssetContract(canonical_name="rededge3", aliases=["B07", "rededge3"], required=False),
            AssetContract(canonical_name="nir", aliases=["B08", "nir"]),
            AssetContract(canonical_name="nir08", aliases=["B8A", "nir08"], required=False),
            AssetContract(canonical_name="swir16", aliases=["B11", "swir16"]),
            AssetContract(canonical_name="swir22", aliases=["B12", "swir22"]),
            AssetContract(canonical_name="scl", aliases=["SCL", "scl"], resampling="nearest"),
        ],
        native_resolution_m=10,
        derived_features=[
            "NDVI", "GNDVI", "EVI", "SAVI", "NDMI", "NDWI", "MNDWI",
            "MSI", "BSI", "NBR", "NBR2", "NDRE", "RECI", "FVC_proxy", "NIRv",
        ],
        maatitrace_use=[
            "crop_greenness", "crop_growth", "crop_moisture", "bare_soil",
            "crop_condition", "future_ml_input",
        ],
        hot_stream_use=True,
        cold_batch_use=True,
        compute_frequency="5_day_or_cloud_free_scene",
        storage=StorageContract(
            spatial_level="h3",
            postgres_table="h3_sentinel2_features",
            parquet_dataset="h3_sentinel2_features",
        ),
        processing_version="s2_zonal_v1",
    ),
    "sentinel_1_rtc": DatasetContract(
        dataset_key="sentinel_1_rtc",
        display_name="Sentinel-1 RTC",
        priority=2,
        category="radar_satellite",
        temporal_type="scene",
        processor_key="sentinel1_rtc",
        providers={
            "planetary_computer": ProviderContract(
                source_adapter="stac",
                collection_ids=["sentinel-1-rtc"],
                priority=1,
                auth_type="planetary_computer_account",
            ),
        },
        assets=[
            AssetContract(canonical_name="vv", aliases=["vv", "VV"], required=False),
            AssetContract(canonical_name="vh", aliases=["vh", "VH"], required=False),
            AssetContract(canonical_name="hh", aliases=["hh", "HH"], required=False),
            AssetContract(canonical_name="hv", aliases=["hv", "HV"], required=False),
        ],
        native_resolution_m=10,
        derived_features=["VV", "VH", "VV_dB", "VH_dB", "VH_VV_ratio", "RVI"],
        maatitrace_use=[
            "cloud_proof_crop_monitoring", "crop_structure", "waterlogging_context",
            "flood_context", "future_water_stress_model",
        ],
        hot_stream_use=True,
        cold_batch_use=True,
        compute_frequency="6_to_12_day_scene",
        storage=StorageContract(
            spatial_level="h3",
            postgres_table="h3_sentinel1_features",
            parquet_dataset="h3_sentinel1_features",
        ),
        processing_version="s1_rtc_zonal_v1",
        metadata={"require_one_polarization_pair": ["VV", "VH"]},
    ),
    "landsat_c2_l2": DatasetContract(
        dataset_key="landsat_c2_l2",
        display_name="Landsat Collection 2 Level-2",
        priority=3,
        category="optical_thermal_satellite",
        temporal_type="scene",
        processor_key="landsat_c2_l2",
        providers={
            "planetary_computer": ProviderContract(
                source_adapter="stac", collection_ids=["landsat-c2-l2"], priority=1
            ),
            "earth_search": ProviderContract(
                source_adapter="stac", collection_ids=["landsat-c2-l2"], priority=2
            ),
        },
        assets=[
            AssetContract(canonical_name="blue", aliases=["blue", "SR_B2"]),
            AssetContract(canonical_name="green", aliases=["green", "SR_B3"]),
            AssetContract(canonical_name="red", aliases=["red", "SR_B4"]),
            AssetContract(canonical_name="nir", aliases=["nir08", "nir", "SR_B5"]),
            AssetContract(canonical_name="swir16", aliases=["swir16", "SR_B6"]),
            AssetContract(canonical_name="swir22", aliases=["swir22", "SR_B7"]),
            AssetContract(canonical_name="surface_temperature", aliases=["lwir11", "ST_B10"], required=False),
            AssetContract(canonical_name="qa_pixel", aliases=["qa_pixel", "QA_PIXEL"], resampling="nearest"),
            AssetContract(canonical_name="qa_radsat", aliases=["qa_radsat", "QA_RADSAT"], required=False, resampling="nearest"),
        ],
        native_resolution_m=30,
        derived_features=["NDVI", "NDMI", "MSI", "BSI", "NBR", "surface_temperature"],
        maatitrace_use=["true_surface_temperature", "heat_context", "drought_context", "historical_baseline"],
        hot_stream_use=True,
        cold_batch_use=True,
        compute_frequency="8_to_16_day_scene",
        storage=StorageContract(
            spatial_level="h3",
            postgres_table="h3_landsat_features",
            parquet_dataset="h3_landsat_features",
        ),
        processing_version="landsat_c2_l2_zonal_v1",
    ),
    "gpm_imerg": DatasetContract(
        dataset_key="gpm_imerg",
        display_name="GPM IMERG Early Daily V07",
        priority=4,
        category="rainfall",
        temporal_type="daily",
        processor_key="gpm_imerg_daily",
        providers={
            "nasa_cmr": ProviderContract(
                source_adapter="cmr",
                short_name="GPM_3IMERGDE",
                version="07",
                priority=1,
                auth_type="earthdata_bearer",
            ),
        },
        variables=["precipitation"],
        native_resolution_m=10000,
        derived_features=["daily_precipitation_mm"],
        maatitrace_use=["rainfall_context", "irrigation_context", "flood_trigger", "future_ml_input"],
        hot_stream_use=True,
        cold_batch_use=True,
        compute_frequency="daily",
        storage=StorageContract(
            spatial_level="farm",
            postgres_table="farm_weather_observations",
            parquet_dataset="farm_weather_observations",
        ),
        processing_version="gpm_imerg_daily_v1",
        metadata={"product_run": "early", "product_version": "V07"},
    ),
    "cop_dem_glo30": DatasetContract(
        dataset_key="cop_dem_glo30",
        display_name="Copernicus DEM GLO-30",
        priority=5,
        category="static_terrain",
        temporal_type="static",
        processor_key="cop_dem_glo30",
        providers={
            "planetary_computer": ProviderContract(
                source_adapter="stac", collection_ids=["cop-dem-glo-30"], priority=1
            )
        },
        assets=[AssetContract(canonical_name="data", aliases=["data", "elevation", "dem"])],
        native_resolution_m=30,
        derived_features=["elevation", "slope", "aspect"],
        maatitrace_use=["erosion_context", "drainage_context", "waterlogging_context"],
        hot_stream_use=False,
        cold_batch_use=True,
        compute_frequency="one_time_static",
        storage=StorageContract(
            spatial_level="h3",
            postgres_table="h3_terrain_features",
            parquet_dataset="h3_terrain_features",
        ),
        processing_version="cop_dem_glo30_zonal_v1",
    ),
    "esa_worldcover": DatasetContract(
        dataset_key="esa_worldcover",
        display_name="ESA WorldCover",
        priority=6,
        category="static_or_annual_land_cover",
        temporal_type="annual",
        processor_key="esa_worldcover",
        providers={
            "planetary_computer": ProviderContract(
                source_adapter="stac", collection_ids=["esa-worldcover"], priority=1
            ),
            "earth_search": ProviderContract(
                source_adapter="stac", collection_ids=["esa-worldcover"], priority=2
            ),
        },
        assets=[AssetContract(canonical_name="map", aliases=["map", "classification", "data"], resampling="nearest")],
        native_resolution_m=10,
        derived_features=["dominant_landcover", "class_fractions"],
        maatitrace_use=["farm_boundary_context", "cropland_context", "model_covariate"],
        hot_stream_use=False,
        cold_batch_use=True,
        compute_frequency="annual_or_static",
        storage=StorageContract(
            spatial_level="h3",
            postgres_table="h3_landcover_features",
            parquet_dataset="h3_landcover_features",
        ),
        processing_version="worldcover_zonal_v1",
    ),
    "jrc_surface_water": DatasetContract(
        dataset_key="jrc_surface_water",
        display_name="JRC Global Surface Water",
        priority=7,
        category="static_or_slow_water_layer",
        temporal_type="static",
        processor_key="jrc_surface_water",
        providers={
            "planetary_computer": ProviderContract(
                source_adapter="stac", collection_ids=["jrc-gsw"], priority=1
            )
        },
        assets=[
            AssetContract(canonical_name="occurrence", aliases=["occurrence"]),
            AssetContract(canonical_name="recurrence", aliases=["recurrence"], required=False),
            AssetContract(canonical_name="seasonality", aliases=["seasonality"], required=False),
            AssetContract(canonical_name="extent", aliases=["extent"], required=False, resampling="nearest"),
        ],
        native_resolution_m=30,
        derived_features=["water_occurrence", "water_recurrence", "water_seasonality", "permanent_water_fraction"],
        maatitrace_use=["historical_water_context", "waterlogging_context", "flood_context"],
        hot_stream_use=False,
        cold_batch_use=True,
        compute_frequency="static_or_slow_update",
        storage=StorageContract(
            spatial_level="h3",
            postgres_table="h3_surface_water_features",
            parquet_dataset="h3_surface_water_features",
        ),
        processing_version="jrc_gsw_zonal_v1",
    ),
    "era5_land": DatasetContract(
        dataset_key="era5_land",
        display_name="ERA5-Land",
        priority=8,
        category="weather_reanalysis",
        temporal_type="daily",
        processor_key="era5_land_daily",
        providers={
            "cds": ProviderContract(
                source_adapter="cds",
                collection_ids=["reanalysis-era5-land"],
                priority=1,
                auth_type="cds_api_key",
            )
        },
        variables=[
            "2m_temperature", "2m_dewpoint_temperature",
            "volumetric_soil_water_layer_1", "volumetric_soil_water_layer_2",
            "volumetric_soil_water_layer_3", "volumetric_soil_water_layer_4",
            "skin_temperature",
        ],
        native_resolution_m=9000,
        derived_features=["daily_temperature", "daily_dewpoint", "soil_water_layers", "skin_temperature"],
        maatitrace_use=["weather_context", "soil_water_context", "future_ml_input"],
        hot_stream_use=False,
        cold_batch_use=True,
        compute_frequency="daily_with_reanalysis_latency",
        storage=StorageContract(
            spatial_level="farm",
            postgres_table="farm_reanalysis_daily",
            parquet_dataset="farm_reanalysis_daily",
        ),
        processing_version="era5_land_daily_v1",
        metadata={
            "note": "V1 intentionally uses non-accumulated daily statistics. Rainfall is sourced from GPM to avoid mis-aggregating ERA5-Land accumulated fields."
        },
    ),
    "soilgrids_v2": DatasetContract(
        dataset_key="soilgrids_v2",
        display_name="SoilGrids 250 m",
        priority=9,
        category="soil",
        temporal_type="static",
        processor_key="soilgrids_wcs",
        providers={
            "soilgrids_wcs": ProviderContract(
                source_adapter="wcs",
                priority=1,
                auth_type="none",
                metadata={"base_url": "https://maps.isric.org/mapserv"},
            )
        },
        variables=["phh2o", "soc", "nitrogen", "clay", "sand", "silt", "bdod", "cec", "cfvo"],
        native_resolution_m=250,
        derived_features=["soil_property_by_depth"],
        maatitrace_use=["soil_context", "nutrition_context", "water_holding_context", "future_ml_input"],
        hot_stream_use=False,
        cold_batch_use=True,
        compute_frequency="one_time_static",
        storage=StorageContract(
            spatial_level="h3",
            postgres_table="h3_soilgrids_features",
            parquet_dataset="h3_soilgrids_features",
        ),
        processing_version="soilgrids_wcs_zonal_v1",
        metadata={
            "depths_cm": [[0, 5], [5, 15], [15, 30], [30, 60], [60, 100], [100, 200]],
            "quantile": "Q0.5",
        },
    ),
    "smap_l4_sm": DatasetContract(
        dataset_key="smap_l4_sm",
        display_name="SMAP L4 Soil Moisture V8",
        priority=10,
        category="soil_moisture",
        temporal_type="subdaily",
        processor_key="smap_l4_sm",
        providers={
            "nasa_cmr": ProviderContract(
                source_adapter="cmr",
                short_name="SPL4SMGP",
                version="8",
                priority=1,
                auth_type="earthdata_bearer",
            )
        },
        variables=["sm_surface", "sm_rootzone"],
        native_resolution_m=9000,
        derived_features=["surface_soil_moisture", "root_zone_soil_moisture"],
        maatitrace_use=["regional_soil_moisture_context", "future_water_stress_model"],
        hot_stream_use=False,
        cold_batch_use=True,
        compute_frequency="3_hourly",
        storage=StorageContract(
            spatial_level="farm",
            postgres_table="farm_smap_observations",
            parquet_dataset="farm_smap_observations",
        ),
        processing_version="smap_l4_v8_farm_v1",
    ),
    "modis_et": DatasetContract(
        dataset_key="modis_et",
        display_name="MODIS Terra/Aqua MOD16A3GF Net Evapotranspiration (Annual, Gap-Filled)",
        priority=11,
        category="evapotranspiration",
        temporal_type="annual",
        processor_key="modis_et",
        providers={
            # No 8-day COG-converted MOD16A2 product exists on any registered
            # provider, and the installed GDAL build has no HDF4 driver, so
            # the raw MOD16A2 HDF4-EOS granules from NASA CMR cannot be
            # opened at all. MOD16A3GF (annual, gap-filled) is the closest
            # real MODIS ET/PET product available as GDAL-readable COGs.
            "planetary_computer": ProviderContract(
                source_adapter="stac",
                collection_ids=["modis-16A3GF-061"],
                priority=1,
            )
        },
        assets=[
            AssetContract(canonical_name="ET_500m", aliases=["ET_500m"], scale=0.1, unit="kg/m^2/year"),
            AssetContract(canonical_name="PET_500m", aliases=["PET_500m"], scale=0.1, unit="kg/m^2/year"),
            AssetContract(canonical_name="LE_500m", aliases=["LE_500m"], required=False, scale=10000.0, unit="J/m^2/day"),
            AssetContract(canonical_name="PLE_500m", aliases=["PLE_500m"], required=False, scale=10000.0, unit="J/m^2/day"),
            AssetContract(canonical_name="ET_QC_500m", aliases=["ET_QC_500m"], required=False, unit="Percent"),
        ],
        native_resolution_m=500,
        derived_features=["ET", "PET", "latent_heat", "potential_latent_heat"],
        maatitrace_use=["water_balance_context", "irrigation_context", "future_ml_input"],
        hot_stream_use=False,
        cold_batch_use=True,
        compute_frequency="annual_gap_filled",
        storage=StorageContract(
            spatial_level="farm",
            postgres_table="farm_modis_et_observations",
            parquet_dataset="farm_modis_et_observations",
        ),
        processing_version="mod16a3gf_v061_farm_v1",
        metadata={
            "note": (
                "Source changed from MOD16A2 (8-day, HDF4 via NASA CMR) to "
                "MOD16A3GF (annual, gap-filled, COG via Planetary Computer). "
                "period_start/period_end on each stored record cover a full "
                "calendar year, not an 8-day window."
            )
        },
    ),
    "modis_lai_fpar": DatasetContract(
        dataset_key="modis_lai_fpar",
        display_name="MODIS Terra LAI/FPAR MOD15A2H V061",
        priority=12,
        category="vegetation_structure",
        temporal_type="composite",
        processor_key="modis_lai_fpar",
        providers={
            "planetary_computer": ProviderContract(
                source_adapter="stac",
                collection_ids=["modis-15A2H-061"],
                priority=1,
            )
        },
        assets=[
            AssetContract(canonical_name="lai", aliases=["Lai_500m", "lai"], required=True, scale=0.1),
            AssetContract(canonical_name="fpar", aliases=["Fpar_500m", "fpar"], required=True, scale=0.01),
            AssetContract(canonical_name="lai_stddev", aliases=["LaiStdDev_500m"], required=False, scale=0.1),
            AssetContract(canonical_name="fpar_stddev", aliases=["FparStdDev_500m"], required=False, scale=0.01),
            AssetContract(canonical_name="qc", aliases=["FparLai_QC"], required=False, resampling="nearest"),
        ],
        native_resolution_m=500,
        derived_features=["LAI", "FPAR"],
        maatitrace_use=["crop_growth_context", "canopy_structure_context", "future_ml_input"],
        hot_stream_use=False,
        cold_batch_use=True,
        compute_frequency="8_day_composite",
        storage=StorageContract(
            spatial_level="farm",
            postgres_table="farm_modis_vegetation_observations",
            parquet_dataset="farm_modis_vegetation_observations",
        ),
        processing_version="mod15a2h_v061_farm_v1",
    ),
    "weather_forecast": DatasetContract(
        dataset_key="weather_forecast",
        display_name="Operational Weather Forecast",
        priority=13,
        category="weather_forecast",
        temporal_type="forecast",
        processor_key="open_meteo_forecast",
        providers={
            "open_meteo": ProviderContract(
                source_adapter="json_api",
                priority=1,
                auth_type="none",
                metadata={"url": "https://api.open-meteo.com/v1/forecast"},
            )
        },
        variables=[
            "temperature_2m", "relative_humidity_2m", "precipitation",
            "wind_speed_10m", "wind_direction_10m", "shortwave_radiation",
            "et0_fao_evapotranspiration", "vapour_pressure_deficit",
        ],
        derived_features=["hourly_weather_forecast"],
        maatitrace_use=["irrigation_planning", "spray_timing_context", "risk_forecasting"],
        hot_stream_use=True,
        cold_batch_use=False,
        compute_frequency="forecast_refresh",
        storage=StorageContract(
            spatial_level="farm",
            postgres_table="farm_weather_forecasts",
            parquet_dataset="farm_weather_forecasts",
        ),
        processing_version="open_meteo_forecast_v1",
    ),
}


# Backward aliases from the old descriptive registry. New code should use canonical keys.
_DATASET_ALIASES = {
    "sentinel_1_sar": "sentinel_1_rtc",
    "dem": "cop_dem_glo30",
    "land_cover": "esa_worldcover",
    "jrc_water": "jrc_surface_water",
    "modis_viirs": "modis_lai_fpar",
}


def resolve_dataset_key(dataset_key: str) -> str:
    normalized = dataset_key.strip()
    return _DATASET_ALIASES.get(normalized, normalized)


def get_dataset_contract(dataset_key: str) -> DatasetContract | None:
    return _DATASET_CONTRACTS.get(resolve_dataset_key(dataset_key))


def list_dataset_contracts() -> list[DatasetContract]:
    return sorted(_DATASET_CONTRACTS.values(), key=lambda item: item.priority)


def list_registered_datasets() -> list[dict[str, Any]]:
    return [item.legacy_dict() for item in list_dataset_contracts()]


def get_registered_dataset(dataset_key: str) -> dict[str, Any] | None:
    dataset = get_dataset_contract(dataset_key)
    return dataset.legacy_dict() if dataset else None


def get_candidate_collection_ids(dataset_key: str, provider: str) -> list[str]:
    dataset = get_dataset_contract(dataset_key)
    if dataset is None:
        return []
    provider_contract = dataset.providers.get(provider)
    if provider_contract is None or not provider_contract.enabled:
        return []
    return provider_contract.collection_ids
