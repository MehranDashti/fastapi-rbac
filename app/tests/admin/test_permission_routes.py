from httpx import AsyncClient


async def test_list_permissions(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/permissions", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_permissions_no_permission(client: AsyncClient, user_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/permissions", headers=user_headers)
    assert resp.status_code == 403


async def test_list_permissions_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/admin/permissions")
    assert resp.status_code == 401


async def test_create_permission_success(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "posts.read", "display_name": "Read Posts", "guard_name": "api"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "posts.read"


async def test_create_permission_duplicate(client: AsyncClient, admin_headers: dict[str, str]):
    await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "posts.read", "display_name": "Read Posts", "guard_name": "api"},
    )
    resp = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "posts.read", "display_name": "Read Posts Again", "guard_name": "api"},
    )
    assert resp.status_code == 409


async def test_get_permission_found(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "posts.write", "display_name": "Write Posts", "guard_name": "api"},
    )
    pid = create.json()["id"]
    resp = await client.get(f"/api/v1/admin/permissions/{pid}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


async def test_get_permission_not_found(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/permissions/9999", headers=admin_headers)
    assert resp.status_code == 404


async def test_update_permission(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "posts.delete", "display_name": "Delete Posts", "guard_name": "api"},
    )
    pid = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/admin/permissions/{pid}",
        headers=admin_headers,
        json={"display_name": "Delete Posts Updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Delete Posts Updated"


async def test_delete_permission(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "posts.archive", "display_name": "Archive Posts", "guard_name": "api"},
    )
    pid = create.json()["id"]
    resp = await client.delete(f"/api/v1/admin/permissions/{pid}", headers=admin_headers)
    assert resp.status_code == 204
    get_resp = await client.get(f"/api/v1/admin/permissions/{pid}", headers=admin_headers)
    assert get_resp.status_code == 404
