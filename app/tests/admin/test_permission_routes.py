from httpx import AsyncClient

from app.tests.factories import permission_payload


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
    pp = permission_payload()
    resp = await client.post("/api/v1/admin/permissions", headers=admin_headers, json=pp)
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == pp["name"]


async def test_create_permission_duplicate(client: AsyncClient, admin_headers: dict[str, str]):
    pp = permission_payload()
    await client.post("/api/v1/admin/permissions", headers=admin_headers, json=pp)
    pp2 = permission_payload(name=pp["name"])
    resp = await client.post("/api/v1/admin/permissions", headers=admin_headers, json=pp2)
    assert resp.status_code == 409


async def test_get_permission_found(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/permissions", headers=admin_headers, json=permission_payload()
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
        "/api/v1/admin/permissions", headers=admin_headers, json=permission_payload()
    )
    pid = create.json()["data"]["id"]
    resp = await client.patch(
        f"/api/v1/admin/permissions/{pid}",
        headers=admin_headers,
        json={"display_name": "Updated Display Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["display_name"] == "Updated Display Name"


async def test_delete_permission(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/permissions", headers=admin_headers, json=permission_payload()
    )
    pid = create.json()["data"]["id"]
    resp = await client.delete(f"/api/v1/admin/permissions/{pid}", headers=admin_headers)
    assert resp.status_code == 204
    get_resp = await client.get(f"/api/v1/admin/permissions/{pid}", headers=admin_headers)
    assert get_resp.status_code == 404


async def test_list_permissions_filter_by_name(client: AsyncClient, admin_headers: dict[str, str]):
    pp1 = permission_payload(name="zfilter_articles.read")
    pp2 = permission_payload(name="zfilter_articles.write")
    await client.post("/api/v1/admin/permissions", headers=admin_headers, json=pp1)
    await client.post("/api/v1/admin/permissions", headers=admin_headers, json=pp2)
    resp = await client.get("/api/v1/admin/permissions?name=zfilter_articles.write", headers=admin_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["name"] == "zfilter_articles.write"


async def test_list_permissions_pagination(client: AsyncClient, admin_headers: dict[str, str]):
    for _ in range(3):
        await client.post(
            "/api/v1/admin/permissions", headers=admin_headers, json=permission_payload()
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
        "/api/v1/admin/permissions", headers=admin_headers, json=permission_payload()
    )
    await client.post(
        "/api/v1/admin/permissions", headers=admin_headers, json=permission_payload()
    )
    resp = await client.get("/api/v1/admin/permissions?sort_by=name&sort_order=asc", headers=admin_headers)
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()["data"]["items"]]
    assert names == sorted(names)
