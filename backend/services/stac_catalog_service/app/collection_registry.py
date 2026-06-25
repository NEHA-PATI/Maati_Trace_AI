from typing import Any


DATASET_REGISTRY: list[dict[str, Any]] = [
    {
        "dataset_key": "sentinel_2_l2a",
        "display_name": "Sentinel-2 L2A",
        "priority": 1,
        "category": "optical_satellite",
        "providers": {
            "planetary_computer": ["sentinel-2-l2a"],
            "earth_search": ["sentinel-2-l2a", "sentinel-2-c1-l2a"],
            "copernicus": ["SENTINEL-2"],
        },
        "expected_assets": [
            "coastal",
            "blue",
            "green",
            "red",
            "rededge1",
            "rededge2",
            "rededge3",
            "nir",
            "nir08",
            "nir09",
            "swir16",
            "swir22",
            "scl",
            "visual",
        ],
        "derived_features": [
            "NDVI",
            "EVI",
            "SAVI",
            "NDMI",
            "NDWI",
            "MNDWI",
            "BSI",
            "NBR",
            "cloud_free_pixel_percentage",
            "vegetation_anomaly",
            "crop_vigor_score",
        ],
        "maatitrace_use": [
            "crop_health",
            "water_stress",
            "bare_soil_detection",
            "crop_damage",
            "yield_model_input",
        ],
        "hot_stream_use": True,
        "cold_batch_use": True,
        "compute_frequency": "5_day_or_cloud_free_scene",
    },
    {
        "dataset_key": "landsat_c2_l2",
        "display_name": "Landsat Collection 2 Level-2",
        "priority": 2,
        "category": "optical_thermal_satellite",
        "providers": {
            "planetary_computer": ["landsat-c2-l2"],
            "earth_search": ["landsat-c2-l2"],
        },
        "expected_assets": [
            "blue",
            "green",
            "red",
            "nir08",
            "swir16",
            "swir22",
            "lwir11",
            "qa_pixel",
            "qa_radsat",
        ],
        "derived_features": [
            "NDVI",
            "NDMI",
            "NBR",
            "BSI",
            "LST",
            "heat_stress",
            "thermal_anomaly",
        ],
        "maatitrace_use": [
            "historical_baseline",
            "heat_stress",
            "drought_stress",
            "yield_risk",
        ],
        "hot_stream_use": False,
        "cold_batch_use": True,
        "compute_frequency": "8_to_16_day_scene",
    },
    {
        "dataset_key": "sentinel_1_sar",
        "display_name": "Sentinel-1 SAR",
        "priority": 3,
        "category": "radar_satellite",
        "providers": {
            "earth_search": ["sentinel-1-grd"],
            "copernicus": ["SENTINEL-1"],
        },
        "expected_assets": [
            "vv",
            "vh",
            "hh",
            "hv",
            "thumbnail",
        ],
        "derived_features": [
            "VV_backscatter",
            "VH_backscatter",
            "VV_VH_ratio",
            "RVI",
            "SAR_anomaly",
            "flood_signal",
            "soil_moisture_proxy",
            "crop_structure_proxy",
        ],
        "maatitrace_use": [
            "flood_detection",
            "monsoon_monitoring",
            "cloud_proof_crop_monitoring",
            "waterlogging",
            "disaster_assessment",
        ],
        "hot_stream_use": True,
        "cold_batch_use": True,
        "compute_frequency": "event_based_or_6_to_12_day",
    },
    {
        "dataset_key": "dem",
        "display_name": "Copernicus DEM / SRTM / NASADEM",
        "priority": 4,
        "category": "static_terrain",
        "providers": {
            "planetary_computer": [
                "cop-dem-glo-30",
                "cop-dem-glo-90",
                "nasadem",
            ],
            "earth_search": [
                "cop-dem-glo-30",
                "cop-dem-glo-90",
            ],
            "nasa_cmr": [
                "NASADEM",
            ],
        },
        "expected_assets": [
            "data",
            "elevation",
            "dem",
        ],
        "derived_features": [
            "elevation",
            "slope",
            "aspect",
            "flow_accumulation",
            "terrain_wetness_index",
            "flood_prone_score",
            "erosion_risk",
        ],
        "maatitrace_use": [
            "flood_risk",
            "waterlogging",
            "irrigation_planning",
            "soil_erosion_risk",
        ],
        "hot_stream_use": False,
        "cold_batch_use": True,
        "compute_frequency": "one_time_static",
    },
    {
        "dataset_key": "modis_viirs",
        "display_name": "MODIS / VIIRS",
        "priority": 5,
        "category": "coarse_resolution_satellite",
        "providers": {
            "nasa_cmr": [
                "MODIS",
                "VIIRS",
            ],
            "planetary_computer": [
                "modis-09A1-061",
                "modis-13Q1-061",
                "modis-11A2-061",
                "viirs-09A1-001",
            ],
        },
        "expected_assets": [
            "sur_refl",
            "ndvi",
            "evi",
            "lst",
            "qa",
        ],
        "derived_features": [
            "regional_vegetation_anomaly",
            "regional_LST",
            "fire_risk_context",
            "district_level_crop_condition",
        ],
        "maatitrace_use": [
            "district_level_monitoring",
            "regional_anomaly",
            "backup_context_when_high_res_cloudy",
        ],
        "hot_stream_use": False,
        "cold_batch_use": True,
        "compute_frequency": "regional_periodic",
    },
    {
        "dataset_key": "land_cover",
        "display_name": "ESA WorldCover / Land Cover",
        "priority": 6,
        "category": "static_or_annual_land_cover",
        "providers": {
            "planetary_computer": [
                "esa-worldcover",
            ],
            "earth_search": [
                "esa-worldcover",
            ],
        },
        "expected_assets": [
            "map",
            "classification",
            "data",
        ],
        "derived_features": [
            "land_cover_class",
            "cropland_mask",
            "crop_non_crop_validation",
            "builtup_water_tree_context",
        ],
        "maatitrace_use": [
            "farm_boundary_validation",
            "cropland_mask",
            "model_covariate",
        ],
        "hot_stream_use": False,
        "cold_batch_use": True,
        "compute_frequency": "annual_or_static",
    },
    {
        "dataset_key": "jrc_water",
        "display_name": "JRC Global Surface Water / Water Layers",
        "priority": 7,
        "category": "static_or_slow_water_layer",
        "providers": {
            "planetary_computer": [
                "jrc-gsw",
            ],
        },
        "expected_assets": [
            "occurrence",
            "seasonality",
            "recurrence",
            "transition",
            "extent",
        ],
        "derived_features": [
            "water_occurrence",
            "water_seasonality",
            "waterbody_proximity",
            "waterlogging_risk",
            "historical_flood_risk",
        ],
        "maatitrace_use": [
            "flood_risk",
            "waterlogging",
            "farm_near_water_risk",
        ],
        "hot_stream_use": False,
        "cold_batch_use": True,
        "compute_frequency": "static_or_slow_update",
    },
    {
        "dataset_key": "gpm_imerg",
        "display_name": "GPM IMERG Rainfall",
        "priority": 8,
        "category": "rainfall_raster",
        "providers": {
            "nasa_cmr": [
                "GPM_3IMERG",
                "IMERG",
            ],
            "planetary_computer": [
                "gpm-imerg-hhr",
            ],
        },
        "expected_assets": [
            "precipitation",
            "precipitationCal",
            "probabilityLiquidPrecipitation",
            "randomError",
        ],
        "derived_features": [
            "daily_rainfall",
            "rainfall_3d",
            "rainfall_7d",
            "rainfall_15d",
            "dry_spell_days",
            "heavy_rainfall_event",
            "flood_trigger",
        ],
        "maatitrace_use": [
            "irrigation_alert",
            "flood_risk",
            "disease_risk",
            "yield_model_input",
        ],
        "hot_stream_use": True,
        "cold_batch_use": True,
        "compute_frequency": "daily_or_subdaily_aggregate",
    },
]


def list_registered_datasets() -> list[dict[str, Any]]:
    return DATASET_REGISTRY


def get_registered_dataset(dataset_key: str) -> dict[str, Any] | None:
    for dataset in DATASET_REGISTRY:
        if dataset["dataset_key"] == dataset_key:
            return dataset
    return None


def get_candidate_collection_ids(
    dataset_key: str,
    provider: str,
) -> list[str]:
    dataset = get_registered_dataset(dataset_key)

    if dataset is None:
        return []

    return dataset.get("providers", {}).get(provider, [])