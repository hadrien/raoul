import httpx
from asgi_lifespan import LifespanManager
from pytest import fixture
from starlette.testclient import TestClient


@fixture
async def client():
    from raoul import app

    async with LifespanManager(app):
        async with httpx.AsyncClient(app=app, base_url="http://app.local") as client:
            yield client


async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200, (res.status_code, res.content)


def test_websocket():
    from raoul import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.send_bytes(b"this is not a pipe")
