import pytest
from httpx import AsyncClient


class TestCategories:
    async def test_list_categories_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/categories")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_categories_with_data(self, client: AsyncClient, category):
        resp = await client.get("/api/v1/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Category"

    async def test_get_category_by_id(self, client: AsyncClient, category):
        resp = await client.get(f"/api/v1/categories/{category.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Category"

    async def test_get_category_not_found(self, client: AsyncClient):
        from uuid import uuid4
        resp = await client.get(f"/api/v1/categories/{uuid4()}")
        assert resp.status_code == 404

    async def test_create_category(self, client: AsyncClient):
        resp = await client.post("/api/v1/categories", json={"name": "New Cat"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Cat"
        assert data["slug"] == "new-cat"
        assert "id" in data

    async def test_create_category_duplicate_name(self, client: AsyncClient, category):
        resp = await client.post("/api/v1/categories", json={"name": category.name})
        assert resp.status_code == 409

    async def test_create_category_invalid(self, client: AsyncClient):
        resp = await client.post("/api/v1/categories", json={"name": ""})
        assert resp.status_code == 422

    async def test_update_category(self, client: AsyncClient, category):
        resp = await client.put(
            f"/api/v1/categories/{category.id}",
            json={"name": "Updated Category"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Category"

    async def test_update_category_not_found(self, client: AsyncClient):
        from uuid import uuid4
        resp = await client.put(
            f"/api/v1/categories/{uuid4()}",
            json={"name": "Nope"},
        )
        assert resp.status_code == 404

    async def test_delete_category(self, client: AsyncClient, category):
        resp = await client.delete(f"/api/v1/categories/{category.id}")
        assert resp.status_code == 204

    async def test_delete_category_not_found(self, client: AsyncClient):
        from uuid import uuid4
        resp = await client.delete(f"/api/v1/categories/{uuid4()}")
        assert resp.status_code == 404
