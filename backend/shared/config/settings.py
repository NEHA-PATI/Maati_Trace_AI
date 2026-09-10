from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_env: str = "local"
    log_level: str = "INFO"
    cors_allowed_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "https://app.maatitrace.com"
    )

    # PostgreSQL - password is intentionally required from environment.
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "maati_trace_ai"
    postgres_user: str = "postgres"
    postgres_password: str

    # Authentication
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "maatitrace-auth"
    jwt_audience: str = "maatitrace-web"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    password_hash_scheme: str = "bcrypt"

    # OTP controls
    signup_otp_expire_minutes: int = 10
    signup_otp_max_attempts: int = 5

    # Google OAuth
    google_client_id: str = ""
    google_allowed_domain: str = ""

    # Email
    mail_provider: str = "console"
    mail_from_email: str = "no-reply@maatitrace.in"
    mail_from_name: str = "MaatiTrace"
    brevo_api_key: str = ""
    mail_http_timeout_seconds: int = 20

    # H3
    h3_default_resolution: int = 12
    h3_min_resolution: int = 7
    h3_max_resolution: int = 12
    max_farm_h3_cells: int = 20000
    max_polygon_vertices: int = 500

    # Storage
    storage_mode: str = "local"
    local_lakehouse_path: str = "./local_lakehouse"
    s3_lakehouse_bucket: str = ""
    aws_region: str = "ap-south-1"
    athena_database: str = ""
    athena_workgroup: str = ""

    # Crop observation media. V1 defaults to LOCAL filesystem storage (see
    # services/crop_observation_service/app/storage/local.py) so the diary is
    # fully usable without any AWS setup — the object_key layout is already
    # S3-shaped, so flipping media_storage_backend to "S3" later needs no
    # database or frontend changes, only crop_observation_s3_bucket filled in.
    media_storage_backend: str = "LOCAL"
    crop_observation_s3_bucket: str = ""
    s3_presigned_upload_ttl_seconds: int = 300
    s3_presigned_download_ttl_seconds: int = 300
    max_images_per_owner: int = 2
    max_image_bytes: int = 8 * 1024 * 1024
    allowed_image_mime_types: str = "image/jpeg,image/png,image/webp"
    max_audio_per_owner: int = 1
    max_audio_bytes: int = 6 * 1024 * 1024
    max_audio_duration_seconds: int = 60
    max_instruction_audio_duration_seconds: int = 40
    allowed_audio_mime_types: str = (
        "audio/webm,audio/ogg,audio/mp4,audio/mpeg,audio/wav,audio/x-wav"
    )
    cartesia_tts_enabled: bool = False
    cartesia_api_key: str = ""
    cartesia_api_base: str = "https://api.cartesia.ai"
    cartesia_api_version: str = "2026-08-14"
    cartesia_tts_model: str = "sonic-3.6-2026-08-27"
    cartesia_odia_voice_id: str = ""
    cartesia_english_voice_id: str = ""
    cartesia_tts_output_container: str = "mp3"
    cartesia_tts_speed: float = 0.95
    cartesia_tts_volume: float = 1.0
    cartesia_connect_timeout_seconds: int = 5
    cartesia_read_timeout_seconds: int = 30

    # Local media root, relative to the crop_observation_service package
    # unless given as an absolute path. system/ holds admin-curated crop and
    # stage media (images, instruction audio); farmer/ holds farmer uploads.
    local_media_root: str = "storage"
    local_system_media_dir: str = "system"
    local_farmer_media_dir: str = "farmer"
    default_locale: str = "or-IN"
    allowed_locales: str = "en-IN,or-IN"

    # Service URLs
    api_gateway_service_url: str = "http://localhost:8000"
    auth_service_url: str = "http://localhost:8002"
    boundary_index_service_url: str = "http://localhost:8004"
    district_boundary_service_url: str = "http://localhost:8005"
    farm_registry_service_url: str = "http://localhost:8006"
    profile_service_url: str = "http://localhost:8003"
    stac_catalog_service_url: str = "http://localhost:8007"
    raster_processor_service_url: str = "http://localhost:8008"
    lakehouse_writer_service_url: str = "http://localhost:8009"
    hot_stream_orchestrator_service_url: str = "http://localhost:8010"
    analytics_query_service_url: str = "http://localhost:8011"
    observability_service_url: str = "http://localhost:8014"
    crop_observation_service_url: str = "http://localhost:8015"

    # API gateway upstream connection pool
    gateway_upstream_timeout_seconds: float = 180.0
    gateway_connect_timeout_seconds: float = 10.0
    gateway_max_connections: int = 100
    gateway_max_keepalive_connections: int = 20
    gateway_keepalive_expiry_seconds: float = 30.0

    # STAC providers
    default_stac_provider: str = "planetary_computer"
    planetary_computer_stac_url: str = (
        "https://planetarycomputer.microsoft.com/api/stac/v1"
    )
    earth_search_stac_url: str = "https://earth-search.aws.element84.com/v1"
    copernicus_stac_url: str = "https://catalogue.dataspace.copernicus.eu/stac"
    nasa_cmr_stac_url: str = "https://cmr.earthdata.nasa.gov/stac"
    nasa_cmr_cloudstac_url: str = "https://cmr.earthdata.nasa.gov/cloudstac"
    nasa_cmr_enabled: bool = False

    # Multi-source catalog / remote access
    catalog_http_timeout_seconds: int = 120
    source_download_timeout_seconds: int = 600

    # NASA Earthdata / CMR. Token must be supplied through .env when used.
    earthdata_token: str = ""
    nasa_cmr_granules_url: str = "https://cmr.earthdata.nasa.gov/search/granules.json"

    # Copernicus Climate Data Store (ERA5-Land)
    cds_api_url: str = "https://cds.climate.copernicus.eu/api"
    cds_api_key: str = ""
    era5_max_days_per_request: int = 31

    # SoilGrids WCS
    soilgrids_wcs_base_url: str = "https://maps.isric.org/mapserv"

    # Weather forecast provider
    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"

    # Raster processing
    raster_http_timeout_seconds: int = 120
    raster_max_pixels_per_request: int = 250000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def allowed_image_mime_types_list(self) -> list[str]:
        return [v.strip() for v in self.allowed_image_mime_types.split(",") if v.strip()]

    @property
    def allowed_audio_mime_types_list(self) -> list[str]:
        return [v.strip() for v in self.allowed_audio_mime_types.split(",") if v.strip()]

    @property
    def allowed_locales_list(self) -> list[str]:
        return [v.strip() for v in self.allowed_locales.split(",") if v.strip()]


settings = Settings()
