from unittest.mock import patch

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
        assert data["short_description"] is None
        assert "id" in data

    async def test_create_category_with_image_url(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/categories",
            json={"name": "Cat With Image", "image": "https://example.com/cat.jpg"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["image"] == "https://example.com/cat.jpg"

    async def test_upload_category_image(self, client: AsyncClient, category):
        with patch("cloudinary.uploader.upload") as mock_upload:
            mock_upload.return_value = {"secure_url": "https://res.cloudinary.com/demo/image/upload/v1/categories/abc.jpg"}
            resp = await client.post(
                f"/api/v1/categories/{category.id}/image",
                files={"file": ("test.png", b"fake-image-content", "image/png")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["image"] == "https://res.cloudinary.com/demo/image/upload/v1/categories/abc.jpg"

    async def test_upload_category_image_invalid_type(self, client: AsyncClient, category):
        resp = await client.post(
            f"/api/v1/categories/{category.id}/image",
            files={"file": ("test.pdf", b"fake-content", "application/pdf")},
        )
        assert resp.status_code == 422

    async def test_upload_category_image_not_found(self, client: AsyncClient):
        from uuid import uuid4
        resp = await client.post(
            f"/api/v1/categories/{uuid4()}/image",
            files={"file": ("test.png", b"fake-image-content", "image/png")},
        )
        assert resp.status_code == 404

    async def test_create_category_with_short_description(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/categories",
            json={"name": "Cat With Desc", "short_description": "A nice category"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["short_description"] == "A nice category"

    async def test_create_category_duplicate_name(self, client: AsyncClient, category):
        resp = await client.post("/api/v1/categories", json={"name": category.name})
        assert resp.status_code == 409

    async def test_create_category_invalid(self, client: AsyncClient):
        resp = await client.post("/api/v1/categories", json={"name": ""})
        assert resp.status_code == 422

    async def test_update_category(self, client: AsyncClient, category):
        resp = await client.put(
            f"/api/v1/categories/{category.id}",
            json={
                "name": "Updated Category",
                "short_description": "Updated desc",
                "image": "https://example.com/new-image.jpg",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Category"
        assert data["short_description"] == "Updated desc"
        assert data["image"] == "https://example.com/new-image.jpg"

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
