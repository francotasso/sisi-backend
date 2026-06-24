from unittest.mock import patch

import pytest
from httpx import AsyncClient


class TestProducts:
    async def test_list_products_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/products")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_products_with_data(self, client: AsyncClient, product):
        resp = await client.get("/api/v1/products")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Test Product"

    async def test_list_products_pagination(self, client: AsyncClient, product):
        resp = await client.get("/api/v1/products?skip=0&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["skip"] == 0
        assert data["limit"] == 10

    async def test_get_product_by_slug(self, client: AsyncClient, product):
        resp = await client.get(f"/api/v1/products/{product.slug}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Product"
        assert resp.json()["slug"] == "test-product"

    async def test_get_product_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/products/non-existent-slug")
        assert resp.status_code == 404

    async def test_create_product(self, client: AsyncClient, category):
        payload = {
            "name": "New Product",
            "price": 15.50,
            "category_id": str(category.id),
        }
        resp = await client.post("/api/v1/products", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Product"
        assert data["slug"] == "new-product"
        assert data["category_name"] == category.name

    async def test_create_product_with_specs_and_faqs(self, client: AsyncClient, category):
        payload = {
            "name": "Full Product",
            "price": 99.99,
            "category_id": str(category.id),
            "specs": {"brand": "TestBrand", "size": "100ml"},
            "faqs": [
                {"question": "Q1?", "answer": "A1"},
                {"question": "Q2?", "answer": "A2"},
            ],
        }
        resp = await client.post("/api/v1/products", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["specs"]["brand"] == "TestBrand"
        assert len(data["faqs"]) == 2

    async def test_create_product_invalid(self, client: AsyncClient):
        resp = await client.post("/api/v1/products", json={"name": "", "price": -1})
        assert resp.status_code == 422

    async def test_update_product(self, client: AsyncClient, product):
        resp = await client.put(
            f"/api/v1/products/{product.id}",
            json={"name": "Updated Product", "price": 49.99},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Product"

    async def test_update_product_not_found(self, client: AsyncClient):
        from uuid import uuid4
        resp = await client.put(
            f"/api/v1/products/{uuid4()}",
            json={"name": "Nope"},
        )
        assert resp.status_code == 404

    async def test_soft_delete_product(self, client: AsyncClient, product):
        resp = await client.delete(f"/api/v1/products/{product.id}")
        assert resp.status_code == 204

        resp = await client.get("/api/v1/products")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_soft_delete_product_not_found(self, client: AsyncClient):
        from uuid import uuid4
        resp = await client.delete(f"/api/v1/products/{uuid4()}")
        assert resp.status_code == 404

    async def test_export_products(self, client: AsyncClient, product):
        resp = await client.get("/api/v1/products/export")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Product"

    async def test_bulk_create_products(self, client: AsyncClient, category):
        payload = {
            "items": [
                {
                    "name": "Bulk 1",
                    "price": 10.00,
                    "category_id": str(category.id),
                },
                {
                    "name": "Bulk 2",
                    "price": 20.00,
                    "category_id": str(category.id),
                },
            ]
        }
        resp = await client.post("/api/v1/products/bulk", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["created"] == 2
        assert len(data["products"]) == 2

    async def test_bulk_replace_all(self, client: AsyncClient, category, product):
        payload = {
            "items": [
                {
                    "name": "Replacement",
                    "price": 5.00,
                    "category_id": str(category.id),
                }
            ]
        }
        resp = await client.put("/api/v1/products/bulk", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 1

        resp = await client.get("/api/v1/products")
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["name"] == "Replacement"

    async def test_get_products_by_slugs(self, client: AsyncClient, product, category, db_session):
        from app.modules.products.models import Product
        second = Product(name="Second Product", slug="second-product", price=25.00, category_id=category.id)
        db_session.add(second)
        await db_session.flush()

        resp = await client.get("/api/v1/products/batch?slugs=test-product,second-product")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        slugs = {p["slug"] for p in data}
        assert slugs == {"test-product", "second-product"}
        assert "specs" not in data[0]
        assert "faqs" not in data[0]

    async def test_get_products_by_slugs_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/products/batch?slugs=nonexistent1,nonexistent2")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_products_by_slugs_no_slugs(self, client: AsyncClient):
        resp = await client.get("/api/v1/products/batch?slugs=")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_newest_products(self, client: AsyncClient, product, category, db_session):
        from app.modules.products.models import Product
        second = Product(name="Second Product", slug="second-product", price=25.00, category_id=category.id)
        db_session.add(second)
        await db_session.flush()

        resp = await client.get("/api/v1/products/newest?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        slugs = {p["slug"] for p in data}
        assert slugs == {"test-product", "second-product"}

    async def test_get_best_sellers(self, client: AsyncClient, category, db_session):
        from app.modules.products.models import Product
        p1 = Product(name="Best Seller 1", slug="best-1", price=10.00, category_id=category.id, best_seller=True)
        p2 = Product(name="Best Seller 2", slug="best-2", price=20.00, category_id=category.id, best_seller=True)
        p3 = Product(name="Normal", slug="normal", price=30.00, category_id=category.id, best_seller=False)
        db_session.add_all([p1, p2, p3])
        await db_session.flush()

        resp = await client.get("/api/v1/products/best-sellers?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        slugs = {p["slug"] for p in data}
        assert slugs == {"best-1", "best-2"}

    async def test_upload_image(self, client: AsyncClient, product):
        with patch("cloudinary.uploader.upload") as mock_upload:
            mock_upload.return_value = {"secure_url": "https://res.cloudinary.com/demo/image/upload/v1/products/abc123.jpg"}
            resp = await client.post(
                f"/api/v1/products/{product.id}/image",
                files={"file": ("test.png", b"fake-image-content", "image/png")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["image"] == "https://res.cloudinary.com/demo/image/upload/v1/products/abc123.jpg"

    async def test_upload_image_invalid_type(self, client: AsyncClient, product):
        resp = await client.post(
            f"/api/v1/products/{product.id}/image",
            files={"file": ("test.pdf", b"fake-content", "application/pdf")},
        )
        assert resp.status_code == 422

    async def test_upload_image_product_not_found(self, client: AsyncClient):
        from uuid import uuid4
        resp = await client.post(
            f"/api/v1/products/{uuid4()}/image",
            files={"file": ("test.png", b"fake-image-content", "image/png")},
        )
        assert resp.status_code == 404
