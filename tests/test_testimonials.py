import pytest
from httpx import AsyncClient


class TestTestimonials:
    async def test_list_testimonials_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/testimonials")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_testimonial(self, client: AsyncClient):
        payload = {
            "name": "John Doe",
            "text": "Great product!",
            "rating": 5,
        }
        resp = await client.post("/api/v1/testimonials", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "John Doe"
        assert data["rating"] == 5
        assert "id" in data

    async def test_create_testimonial_invalid_rating(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/testimonials",
            json={"name": "Bad", "text": "Bad", "rating": 6},
        )
        assert resp.status_code == 422

        resp = await client.post(
            "/api/v1/testimonials",
            json={"name": "Bad", "text": "Bad", "rating": 0},
        )
        assert resp.status_code == 422

    async def test_list_testimonials_with_data(self, client: AsyncClient):
        await client.post(
            "/api/v1/testimonials",
            json={"name": "A", "text": "T1", "rating": 4},
        )
        await client.post(
            "/api/v1/testimonials",
            json={"name": "B", "text": "T2", "rating": 5},
        )
        resp = await client.get("/api/v1/testimonials")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    async def test_get_testimonial_by_id(self, client: AsyncClient):
        created = await client.post(
            "/api/v1/testimonials",
            json={"name": "Find Me", "text": "Found!", "rating": 3},
        )
        tid = created.json()["id"]
        resp = await client.get(f"/api/v1/testimonials/{tid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Find Me"

    async def test_get_testimonial_not_found(self, client: AsyncClient):
        from uuid import uuid4
        resp = await client.get(f"/api/v1/testimonials/{uuid4()}")
        assert resp.status_code == 404

    async def test_delete_testimonial(self, client: AsyncClient):
        created = await client.post(
            "/api/v1/testimonials",
            json={"name": "Del", "text": "Delete me", "rating": 2},
        )
        tid = created.json()["id"]
        resp = await client.delete(f"/api/v1/testimonials/{tid}")
        assert resp.status_code == 204

        resp = await client.get(f"/api/v1/testimonials/{tid}")
        assert resp.status_code == 404

    async def test_delete_testimonial_not_found(self, client: AsyncClient):
        from uuid import uuid4
        resp = await client.delete(f"/api/v1/testimonials/{uuid4()}")
        assert resp.status_code == 404
