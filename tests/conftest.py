import os
import asyncio
import pytest
from typing import AsyncIterator

# Ensure no real Azure calls by default in test env
os.environ.setdefault("AZURE_SUBSCRIPTION_ID", "test-sub-id")
os.environ.setdefault("AZURE_RESOURCE_GROUP", "test-rg")


@pytest.fixture(scope="session")
def event_loop() -> AsyncIterator[asyncio.AbstractEventLoop]:
    # pytest-asyncio: custom session loop on Windows
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

