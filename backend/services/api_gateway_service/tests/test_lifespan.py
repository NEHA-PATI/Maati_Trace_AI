from __future__ import annotations

import asyncio

from fastapi import FastAPI

from services.api_gateway_service.app import main
from services.api_gateway_service.app.proxy import UPSTREAM_CLIENT_STATE_KEY


class FakeAsyncClient:
    def __init__(self) -> None:
        self.is_closed = False

    async def aclose(self) -> None:
        self.is_closed = True


def test_gateway_uses_one_client_for_the_application_lifetime(monkeypatch) -> None:
    application = FastAPI()
    client = FakeAsyncClient()
    monkeypatch.setattr(main, "create_upstream_client", lambda: client)

    async def exercise_lifespan() -> None:
        async with main.lifespan(application):
            assert (
                getattr(application.state, UPSTREAM_CLIENT_STATE_KEY)
                is client
            )
            assert not client.is_closed
        assert client.is_closed

    asyncio.run(exercise_lifespan())
