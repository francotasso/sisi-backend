import pytest
from httpx import AsyncClient


class TestStore:
    async def test_get_store_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/store")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Store not found. Please create one first."

    async def test_create_store(self, client: AsyncClient):
        payload = {
            "store_name": "My Store",
            "description": "Best store ever",
            "contact": {
                "phone": "123456789",
                "email": "store@test.com",
            },
            "hours": [
                {"day": "Monday", "open_time": "09:00", "close_time": "18:00"},
                {"day": "Sunday", "is_closed": True},
            ],
            "social_media": [
                {"platform": "Instagram", "url": "https://insta.com/store"},
            ],
        }
        resp = await client.post("/api/v1/store", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["store_name"] == "My Store"
        assert data["contact"]["phone"] == "123456789"
        assert len(data["hours"]) == 2
        assert len(data["social_media"]) == 1

    async def test_get_store_with_data(self, client: AsyncClient, store_data):
        await client.post("/api/v1/store", json=store_data)
        resp = await client.get("/api/v1/store")
        assert resp.status_code == 200
        data = resp.json()
        assert data["store_name"] == store_data["store_name"]
        assert data["contact"]["email"] == store_data["contact"]["email"]

    async def test_update_store(self, client: AsyncClient, store_data):
        await client.post("/api/v1/store", json=store_data)
        resp = await client.put(
            "/api/v1/store",
            json={"store_name": "Updated Store", "description": "Updated"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["store_name"] == "Updated Store"

    async def test_update_store_with_nested(self, client: AsyncClient, store_data):
        await client.post("/api/v1/store", json=store_data)
        resp = await client.put(
            "/api/v1/store",
            json={
                "contact": {"phone": "999999999"},
                "hours": [
                    {"day": "Friday", "open_time": "10:00", "close_time": "17:00"}
                ],
                "social_media": [],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["contact"]["phone"] == "999999999"
        assert len(data["hours"]) == 1

    async def test_create_store_twice(self, client: AsyncClient, store_data):
        await client.post("/api/v1/store", json=store_data)
        resp = await client.post("/api/v1/store", json=store_data)
        assert resp.status_code == 404


@pytest.fixture
def store_data(category):
    return {
        "store_name": "Test Store",
        "description": "A test store",
        "contact": {
            "phone": "111111111",
            "email": "test@store.com",
        },
        "hours": [
            {"day": "Monday", "open_time": "09:00", "close_time": "18:00"},
        ],
        "social_media": [
            {"platform": "Facebook", "url": "https://fb.com/store"},
        ],
    }
