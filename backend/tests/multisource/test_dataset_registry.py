from services.stac_catalog_service.app.collection_registry import (
    get_dataset_contract,
    list_registered_datasets,
)


def test_expected_multisource_datasets_registered():
    keys = {row["dataset_key"] for row in list_registered_datasets()}
    assert {
        "sentinel_2_l2a",
        "sentinel_1_rtc",
        "landsat_c2_l2",
        "gpm_imerg",
        "cop_dem_glo30",
        "esa_worldcover",
        "jrc_surface_water",
        "era5_land",
        "soilgrids_v2",
        "smap_l4_sm",
        "modis_et",
        "modis_lai_fpar",
        "weather_forecast",
    }.issubset(keys)


def test_sentinel2_contract_stays_on_existing_processor_and_table():
    dataset = get_dataset_contract("sentinel_2_l2a")
    assert dataset is not None
    assert dataset.processor_key == "sentinel2_existing"
    assert dataset.storage.postgres_table == "h3_sentinel2_features"
    assert dataset.processing_version == "s2_zonal_v1"


def test_old_registry_aliases_resolve():
    assert get_dataset_contract("sentinel_1_sar").dataset_key == "sentinel_1_rtc"
    assert get_dataset_contract("dem").dataset_key == "cop_dem_glo30"
    assert get_dataset_contract("land_cover").dataset_key == "esa_worldcover"
