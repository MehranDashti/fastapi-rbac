import pytest
from httpx import AsyncClient


async def test_signup_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/signup", json={
        "email": "new@test.com",
        "username": "newuser",
        "full_name": "New User",
        "password": "Password1",
    })
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["email"] == "new@test.com"
    assert data["username"] == "newuser"


async def test_signup_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@test.com", "username": "dup1", "full_name": "Dup", "password": "Password1"}
    await client.post("/api/v1/auth/signup", json=payload)
    payload["username"] = "dup2"
    resp = await client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == 409


async def test_signup_weak_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/signup", json={
        "email": "weak@test.com",
        "username": "weakuser",
        "full_name": "Weak",
        "password": "abc",
    })
    assert resp.status_code == 422


async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json={
        "email": "login@test.com",
        "username": "loginuser",
        "full_name": "Login User",
        "password": "Password1",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com",
        "password": "Password1",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json={
        "email": "badpw@test.com",
        "username": "badpwuser",
        "full_name": "Bad",
        "password": "Password1",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "badpw@test.com",
        "password": "WrongPass1",
    })
    assert resp.status_code == 401


async def test_refresh_success(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json={
        "email": "refresh@test.com",
        "username": "refreshuser",
        "full_name": "Refresh",
        "password": "Password1",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "refresh@test.com",
        "password": "Password1",
    })
    refresh_token = login.json()["data"]["refresh_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()["data"]


async def test_refresh_with_access_token(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json={
        "email": "badrefresh@test.com",
        "username": "badrefreshuser",
        "full_name": "Bad",
        "password": "Password1",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "badrefresh@test.com",
        "password": "Password1",
    })
    access_token = login.json()["data"]["access_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


async def test_logout_authenticated(client: AsyncClient, user_headers: dict[str, str]):
    resp = await client.post("/api/v1/auth/logout", headers=user_headers)
    assert resp.status_code == 204


async def test_logout_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 401


async def test_get_profile(client: AsyncClient, user_headers: dict[str, str]):
    resp = await client.get("/api/v1/auth/profile", headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "email" in data


async def test_get_profile_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/auth/profile")
    assert resp.status_code == 401


async def test_update_profile_name(client: AsyncClient, user_headers: dict[str, str]):
    resp = await client.patch(
        "/api/v1/auth/profile",
        headers=user_headers,
        json={"full_name": "Updated Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["full_name"] == "Updated Name"


async def test_update_profile_password(client: AsyncClient, user_headers: dict[str, str]):
    resp = await client.patch(
        "/api/v1/auth/profile",
        headers=user_headers,
        json={"password": "NewPassword1"},
    )
    assert resp.status_code == 200
