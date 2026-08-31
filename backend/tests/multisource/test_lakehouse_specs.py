from services.lakehouse_writer_service.app.environment_repository import TABLE_SPECS


def test_all_new_datasets_have_explicit_table_allowlist():
    assert set(TABLE_SPECS) == {
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
    }


def test_no_generic_arbitrary_table_write():
    for spec in TABLE_SPECS.values():
        assert spec.table.startswith(("h3_", "farm_"))
        assert "farm_id" in spec.columns
        assert "processing_version" in spec.columns
