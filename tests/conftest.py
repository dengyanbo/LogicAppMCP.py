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

import inspect

# Basic asyncio test support without external plugin

def pytest_pyfunc_call(pyfuncitem):
    testfunction = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunction):
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(testfunction(**pyfuncitem.funcargs))
        return True
    marker = pyfuncitem.get_closest_marker("asyncio")
    if marker:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(pyfuncitem.obj(**pyfuncitem.funcargs))
        return True
    return None
