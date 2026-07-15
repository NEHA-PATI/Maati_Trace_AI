from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings
from shared.errors.api_errors import bad_request
from shared.logging.json_logging import configure_json_logging
from services.stac_catalog_service.app.collection_registry import (
    get_candidate_collection_ids,
    list_registered_datasets,
)
from services.stac_catalog_service.app.providers import (
    StacProviderError,
    get_provider_url,
    list_supported_providers,
)
from services.stac_catalog_service.app.schemas import (
    CollectionAssetsResponse,
    DatasetAvailabilityItem,
    DatasetAvailabilityRequest,
    DatasetAvailabilityResponse,
    DatasetRegistryItem,
    HealthResponse,
    LatestSceneRequest,
    ProviderCollectionResponse,
    StacSearchRequest,
    StacSearchResponse,
)
from services.stac_catalog_service.app.stac_client import (
    StacCatalogError,
    extract_asset_summary_keys,
    get_collection_details,
    list_provider_collections,
    search_items,
)

SERVICE_NAME = "stac_catalog_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title="STAC Catalog Service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health/live", response_model=HealthResponse)
def live():
    return HealthResponse(
        service=SERVICE_NAME,
        status="live",
        environment=settings.app_env,
    )


@app.get("/health/ready", response_model=HealthResponse)
def ready():
    return HealthResponse(
        service=SERVICE_NAME,
        status="ready",
        environment=settings.app_env,
    )


@app.get("/v1/stac/providers")
def providers():
    return {
        "providers": list_supported_providers(),
        "default_provider": settings.default_stac_provider,
    }


@app.get("/v1/stac/datasets", response_model=list[DatasetRegistryItem])
def datasets():
    return list_registered_datasets()


@app.get("/v1/stac/providers/{provider}/collections", response_model=ProviderCollectionResponse)
def provider_collections(provider: str):
    try:
        collections = list_provider_collections(provider)
        return ProviderCollectionResponse(
            provider=provider,
            stac_url=get_provider_url(provider),
            collection_count=len(collections),
            collections=collections,
        )
    except (StacProviderError, StacCatalogError) as exc:
        raise bad_request(str(exc), code="STAC_PROVIDER_ERROR") from exc


@app.post("/v1/stac/datasets/availability", response_model=DatasetAvailabilityResponse)
def dataset_availability(payload: DatasetAvailabilityRequest):
    try:
        provider_collections_list = list_provider_collections(payload.provider)
    except (StacProviderError, StacCatalogError) as exc:
        raise bad_request(str(exc), code="STAC_PROVIDER_ERROR") from exc

    provider_collection_map = {
        collection["id"]: collection for collection in provider_collections_list
    }

    response_items: list[DatasetAvailabilityItem] = []

    for dataset in list_registered_datasets():
        candidate_ids = get_candidate_collection_ids(
            dataset_key=dataset["dataset_key"],
            provider=payload.provider,
        )

        available_ids = [
            collection_id
            for collection_id in candidate_ids
            if collection_id in provider_collection_map
        ]

        matched_collections = [
            provider_collection_map[collection_id]
            for collection_id in available_ids
        ]

        response_items.append(
            DatasetAvailabilityItem(
                dataset_key=dataset["dataset_key"],
                display_name=dataset["display_name"],
                provider=payload.provider,
                candidate_collection_ids=candidate_ids,
                available_collection_ids=available_ids,
                is_available=bool(available_ids),
                matched_collections=matched_collections,
            )
        )

    return DatasetAvailabilityResponse(
        provider=payload.provider,
        datasets=response_items,
    )


@app.get(
    "/v1/stac/providers/{provider}/collections/{collection_id}/assets",
    response_model=CollectionAssetsResponse,
)
def collection_assets(provider: str, collection_id: str):
    try:
        details = get_collection_details(
            provider=provider,
            collection_id=collection_id,
        )
    except (StacProviderError, StacCatalogError) as exc:
        raise bad_request(str(exc), code="STAC_COLLECTION_ERROR") from exc

    asset_keys = extract_asset_summary_keys(details)

    return CollectionAssetsResponse(
        provider=provider,
        collection_id=collection_id,
        title=details.get("title"),
        description=details.get("description"),
        available_asset_keys_from_summaries=asset_keys,
        summaries=details.get("summaries") or {},
    )


@app.post("/v1/stac/search", response_model=StacSearchResponse)
def search(payload: StacSearchRequest):
    try:
        items = search_items(
            provider=payload.provider,
            collection_id=payload.collection_id,
            bbox=payload.bbox,
            start_date=payload.start_date,
            end_date=payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
            limit=payload.limit,
        )
    except (StacProviderError, StacCatalogError) as exc:
        raise bad_request(str(exc), code="STAC_SEARCH_ERROR") from exc

    return StacSearchResponse(
        provider=payload.provider,
        collection_id=payload.collection_id,
        returned_count=len(items),
        items=items,
    )


@app.post("/v1/stac/latest", response_model=StacSearchResponse)
def latest(payload: LatestSceneRequest):
    try:
        items = search_items(
            provider=payload.provider,
            collection_id=payload.collection_id,
            bbox=payload.bbox,
            start_date=payload.start_date,
            end_date=payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
            limit=10,
        )
    except (StacProviderError, StacCatalogError) as exc:
        raise bad_request(str(exc), code="STAC_LATEST_ERROR") from exc

    latest_items = items[:1]

    return StacSearchResponse(
        provider=payload.provider,
        collection_id=payload.collection_id,
        returned_count=len(latest_items),
        items=latest_items,
    )
