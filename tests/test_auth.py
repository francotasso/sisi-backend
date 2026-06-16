import pytest
from httpx import AsyncClient

SUPABASE_AUTH = "https://ganrqmmrwoqfiynjookl.supabase.co/auth/v1"


class TestAuth:
    async def test_login_success(self, client: AsyncClient, mock_supabase_auth):
        mock_supabase_auth.post(
            f"{SUPABASE_AUTH}/token?grant_type=password",
        ).respond(
            200,
            json={
                "access_token": "fake-token",
                "token_type": "bearer",
                "user": {"id": "123", "email": "test@test.com"},
            },
        )

        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "fake-token"
        assert data["token_type"] == "bearer"

    async def test_login_failure(self, client: AsyncClient, mock_supabase_auth):
        mock_supabase_auth.post(
            f"{SUPABASE_AUTH}/token?grant_type=password",
        ).respond(400, json={"error": "invalid_grant"})

        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "bad@test.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    async def test_register_success(self, client: AsyncClient, mock_supabase_auth):
        mock_supabase_auth.post(
            f"{SUPABASE_AUTH}/admin/users",
        ).respond(
            200,
            json={
                "id": "new-user-id",
                "email": "new@test.com",
                "user_metadata": {"role": "admin"},
                "created_at": "2024-01-01T00:00:00Z",
            },
        )

        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@test.com", "password": "password123", "role": "admin"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == "new-user-id"

    async def test_register_duplicate(self, client: AsyncClient, mock_supabase_auth):
        mock_supabase_auth.post(
            f"{SUPABASE_AUTH}/admin/users",
        ).respond(409, json={"error": "User already exists"})

        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "dup@test.com", "password": "password123"},
        )
        assert resp.status_code == 409

    async def test_list_users(self, client: AsyncClient, mock_supabase_auth):
        mock_supabase_auth.get(
            f"{SUPABASE_AUTH}/admin/users",
        ).respond(
            200,
            json={
                "users": [
                    {
                        "id": "1",
                        "email": "a@test.com",
                        "user_metadata": {"role": "admin"},
                        "created_at": "2024-01-01T00:00:00Z",
                    },
                ]
            },
        )

        resp = await client.get("/api/v1/auth/users")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["users"]) == 1

    async def test_update_user(self, client: AsyncClient, mock_supabase_auth):
        mock_supabase_auth.put(
            f"{SUPABASE_AUTH}/admin/users/user-123",
        ).respond(200, json={"id": "user-123", "email": "updated@test.com"})

        resp = await client.put(
            "/api/v1/auth/users/user-123",
            json={"email": "updated@test.com"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "updated@test.com"

    async def test_delete_user(self, client: AsyncClient, mock_supabase_auth):
        mock_supabase_auth.delete(
            f"{SUPABASE_AUTH}/admin/users/user-123",
        ).respond(204)

        resp = await client.delete("/api/v1/auth/users/user-123")
        assert resp.status_code == 200
        assert resp.json()["message"] == "User deleted successfully"

    async def test_unauthorized_access(self, client_no_auth: AsyncClient):
        resp = await client_no_auth.post(
            "/api/v1/categories", json={"name": "Should Fail"}
        )
        assert resp.status_code == 401
