"""Test application with test-only routes mounted on an app instance."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from app.core.errors import AppError
from app.core.settings import Settings
from app.main import create_app

LEAKY_MESSAGE = "db-pw-hunter2 at /srv/app/secret.py"


class ConflictError(AppError):
    status_code = 409
    code = "out_of_stock"
    title = "Product out of stock"


class Item(BaseModel):
    quantity: int


@pytest.fixture
def app(make_settings: Callable[..., Settings]) -> FastAPI:
    application = create_app(make_settings(app_env="test"))

    @application.get("/t/items/{item_id}")
    async def get_item(item_id: int) -> dict[str, int]:
        return {"id": item_id}

    @application.post("/t/items")
    async def post_item(item: Item) -> dict[str, int]:
        return {"quantity": item.quantity}

    @application.get("/t/slow/{name}")
    async def slow(name: str) -> dict[str, Any]:
        log = logging.getLogger("app.test.slow")
        log.info("start %s", name)
        await asyncio.sleep(0.05)
        log.info("end %s", name)
        return {"name": name}

    @application.get("/t/conflict")
    async def conflict() -> None:
        raise ConflictError("One or more items are no longer available.")

    @application.get("/t/boom")
    async def boom() -> None:
        raise RuntimeError(LEAKY_MESSAGE)

    return application
