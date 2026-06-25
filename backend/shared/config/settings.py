from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    aws_region: str = "ap-south-1"
    log_level: str = "INFO"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "maati_trace_ai"
    postgres_user: str = "postgres"
    postgres_password: str = "Mikaelson"

    jwt_secret: str = "change-this-local-only"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    h3_default_resolution: int = 12
    h3_min_resolution: int = 7
    h3_max_resolution: int = 12
    max_farm_h3_cells: int = 20000
    max_polygon_vertices: int = 500

    local_lakehouse_path: str = "./local_lakehouse"
    s3_lakehouse_bucket: str = ""
    athena_database: str = ""
    athena_workgroup: str = ""

    boundary_index_service_url: str = "http://localhost:8004"
    district_boundary_service_url: str = "http://localhost:8005"
    stac_catalog_service_url: str = "http://localhost:8007"

    default_stac_provider: str = "planetary_computer"
    planetary_computer_stac_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
    earth_search_stac_url: str = "https://earth-search.aws.element84.com/v1"
    copernicus_stac_url: str = "https://catalogue.dataspace.copernicus.eu/stac"
    nasa_cmr_stac_url: str = "https://cmr.earthdata.nasa.gov/stac"
    nasa_cmr_cloudstac_url: str = "https://cmr.earthdata.nasa.gov/cloudstac"
    nasa_cmr_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
