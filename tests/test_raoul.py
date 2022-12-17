import httpx
from asgi_lifespan import LifespanManager
from pytest import fixture


@fixture
async def client():
    from raoul import app

    async with LifespanManager(app):
        async with httpx.AsyncClient(app=app, base_url="http://app.local") as client:
            yield client


def test_health():
    pass
