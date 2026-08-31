from services.raster_processor_service.app.processor_registry import register_processor
from services.raster_processor_service.app.processors import (
    dem,
    era5_land,
    gpm_imerg,
    jrc_surface_water,
    landsat_c2_l2,
    modis_et,
    modis_lai_fpar,
    sentinel1_rtc,
    smap_l4,
    soilgrids,
    weather_forecast,
    worldcover,
)


def register_all_processors() -> None:
    register_processor("sentinel1_rtc", sentinel1_rtc.process)
    register_processor("landsat_c2_l2", landsat_c2_l2.process)
    register_processor("cop_dem_glo30", dem.process)
    register_processor("esa_worldcover", worldcover.process)
    register_processor("jrc_surface_water", jrc_surface_water.process)
    register_processor("gpm_imerg_daily", gpm_imerg.process)
    register_processor("era5_land_daily", era5_land.process)
    register_processor("soilgrids_wcs", soilgrids.process)
    register_processor("smap_l4_sm", smap_l4.process)
    register_processor("modis_et", modis_et.process)
    register_processor("modis_lai_fpar", modis_lai_fpar.process)
    register_processor("open_meteo_forecast", weather_forecast.process)
