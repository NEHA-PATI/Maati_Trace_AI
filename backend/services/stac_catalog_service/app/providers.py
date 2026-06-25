# from shared.config.settings import settings


# class StacProviderError(ValueError):
#     pass


# def get_provider_url(provider: str) -> str:
#     provider_key = provider.strip().lower()

#     provider_urls = {
#         "planetary_computer": settings.planetary_computer_stac_url,
#         "earth_search": settings.earth_search_stac_url,
#         "copernicus": settings.copernicus_stac_url,
#         "nasa_cmr": settings.nasa_cmr_stac_url,
#     }

#     url = provider_urls.get(provider_key)

#     if not url:
#         raise StacProviderError(f"Unsupported STAC provider: {provider}")

#     return url


# def list_supported_providers() -> dict[str, str]:
#     return {
#         "planetary_computer": settings.planetary_computer_stac_url,
#         "earth_search": settings.earth_search_stac_url,
#         "copernicus": settings.copernicus_stac_url,
#         "nasa_cmr": settings.nasa_cmr_stac_url,
#     }

from shared.config.settings import settings


class StacProviderError(ValueError):
    pass


def get_provider_url(provider: str) -> str:
    provider_key = provider.strip().lower()

    provider_urls = {
        "planetary_computer": settings.planetary_computer_stac_url,
        "earth_search": settings.earth_search_stac_url,
        "copernicus": settings.copernicus_stac_url,
    }

    if settings.nasa_cmr_enabled:
        provider_urls["nasa_cmr"] = settings.nasa_cmr_stac_url
        provider_urls["nasa_cloudstac"] = settings.nasa_cmr_cloudstac_url

    url = provider_urls.get(provider_key)

    if not url:
        raise StacProviderError(
            f"Unsupported or disabled STAC provider: {provider}. "
            "For now use planetary_computer, earth_search, or copernicus."
        )

    return url


def list_supported_providers() -> dict[str, str]:
    providers = {
        "planetary_computer": settings.planetary_computer_stac_url,
        "earth_search": settings.earth_search_stac_url,
        "copernicus": settings.copernicus_stac_url,
    }

    if settings.nasa_cmr_enabled:
        providers["nasa_cmr"] = settings.nasa_cmr_stac_url
        providers["nasa_cloudstac"] = settings.nasa_cmr_cloudstac_url

    return providers