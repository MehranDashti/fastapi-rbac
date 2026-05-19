from httpx import AsyncClient


async def test_list_permissions(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/permissions", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"]["items"], list)
    assert "meta" in resp.json()["data"]


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
    assert resp.json()["data"]["name"] == "posts.read"


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
    pid = create.json()["data"]["id"]
    resp = await client.get(f"/api/v1/admin/permissions/{pid}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == pid


async def test_get_permission_not_found(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/permissions/9999", headers=admin_headers)
    assert resp.status_code == 404


async def test_update_permission(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "posts.delete", "display_name": "Delete Posts", "guard_name": "api"},
    )
    pid = create.json()["data"]["id"]
    resp = await client.patch(
        f"/api/v1/admin/permissions/{pid}",
        headers=admin_headers,
        json={"display_name": "Delete Posts Updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["display_name"] == "Delete Posts Updated"


async def test_delete_permission(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "posts.archive", "display_name": "Archive Posts", "guard_name": "api"},
    )
    pid = create.json()["data"]["id"]
    resp = await client.delete(f"/api/v1/admin/permissions/{pid}", headers=admin_headers)
    assert resp.status_code == 204
    get_resp = await client.get(f"/api/v1/admin/permissions/{pid}", headers=admin_headers)
    assert get_resp.status_code == 404


async def test_list_permissions_filter_by_name(client: AsyncClient, admin_headers: dict[str, str]):
    await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "articles.read", "display_name": "Read Articles", "guard_name": "api"},
    )
    await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "articles.write", "display_name": "Write Articles", "guard_name": "api"},
    )
    resp = await client.get("/api/v1/admin/permissions?name=write", headers=admin_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["name"] == "articles.write"


async def test_list_permissions_pagination(client: AsyncClient, admin_headers: dict[str, str]):
    for i in range(3):
        await client.post(
            "/api/v1/admin/permissions",
            headers=admin_headers,
            json={"name": f"paged.perm{i}", "display_name": f"Paged {i}", "guard_name": "api"},
        )
    resp = await client.get("/api/v1/admin/permissions?page=1&page_size=2", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 2
    # admin_headers fixture seeds 12 system permissions; 3 more created here → 15 total
    assert data["meta"]["total"] == 15
    assert data["meta"]["has_next"] is True
    assert data["meta"]["page_size"] == 2


async def test_list_permissions_sort_by_name(client: AsyncClient, admin_headers: dict[str, str]):
    await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "zzz.last", "display_name": "Last", "guard_name": "api"},
    )
    await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "aaa.first", "display_name": "First", "guard_name": "api"},
    )
    resp = await client.get("/api/v1/admin/permissions?sort_by=name&sort_order=asc", headers=admin_headers)
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()["data"]["items"]]
    assert names == sorted(names)
