from httpx import AsyncClient


async def test_list_roles(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/roles", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"]["items"], list)
    assert "meta" in resp.json()["data"]


async def test_list_roles_no_permission(client: AsyncClient, user_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/roles", headers=user_headers)
    assert resp.status_code == 403


async def test_create_role_success(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "editor", "display_name": "Editor", "guard_name": "api"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == "editor"


async def test_create_role_duplicate(client: AsyncClient, admin_headers: dict[str, str]):
    await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "editor", "display_name": "Editor", "guard_name": "api"},
    )
    resp = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "editor", "display_name": "Editor Again", "guard_name": "api"},
    )
    assert resp.status_code == 409


async def test_get_role_found(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "viewer", "display_name": "Viewer", "guard_name": "api"},
    )
    rid = create.json()["data"]["id"]
    resp = await client.get(f"/api/v1/admin/roles/{rid}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == rid
    assert "permissions" in resp.json()["data"]


async def test_get_role_not_found(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/roles/9999", headers=admin_headers)
    assert resp.status_code == 404


async def test_update_role(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "updater", "display_name": "Updater", "guard_name": "api"},
    )
    rid = create.json()["data"]["id"]
    resp = await client.patch(
        f"/api/v1/admin/roles/{rid}",
        headers=admin_headers,
        json={"display_name": "Updater Updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["display_name"] == "Updater Updated"


async def test_delete_role(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "todelete", "display_name": "To Delete", "guard_name": "api"},
    )
    rid = create.json()["data"]["id"]
    resp = await client.delete(f"/api/v1/admin/roles/{rid}", headers=admin_headers)
    assert resp.status_code == 204
    get_resp = await client.get(f"/api/v1/admin/roles/{rid}", headers=admin_headers)
    assert get_resp.status_code == 404


async def test_assign_permission_to_role(client: AsyncClient, admin_headers: dict[str, str]):
    role_resp = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "assigntest", "display_name": "Assign Test", "guard_name": "api"},
    )
    rid = role_resp.json()["data"]["id"]
    perm_resp = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "custom.read", "display_name": "Custom Read", "guard_name": "api"},
    )
    pid = perm_resp.json()["data"]["id"]
    resp = await client.post(
        f"/api/v1/admin/roles/{rid}/permissions",
        headers=admin_headers,
        json={"permission_id": pid},
    )
    assert resp.status_code == 200
    perm_names = [p["name"] for p in resp.json()["data"]["permissions"]]
    assert "custom.read" in perm_names


async def test_revoke_permission_from_role(client: AsyncClient, admin_headers: dict[str, str]):
    role_resp = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "revoketest", "display_name": "Revoke Test", "guard_name": "api"},
    )
    rid = role_resp.json()["data"]["id"]
    perm_resp = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "custom.write", "display_name": "Custom Write", "guard_name": "api"},
    )
    pid = perm_resp.json()["data"]["id"]
    await client.post(
        f"/api/v1/admin/roles/{rid}/permissions",
        headers=admin_headers,
        json={"permission_id": pid},
    )
    resp = await client.delete(
        f"/api/v1/admin/roles/{rid}/permissions/{pid}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    perm_names = [p["name"] for p in resp.json()["data"]["permissions"]]
    assert "custom.write" not in perm_names


async def test_list_roles_filter_by_name(client: AsyncClient, admin_headers: dict[str, str]):
    await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "manager", "display_name": "Manager", "guard_name": "api"},
    )
    await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "viewer", "display_name": "Viewer", "guard_name": "api"},
    )
    resp = await client.get("/api/v1/admin/roles?name=man", headers=admin_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["name"] == "manager"


async def test_list_roles_pagination(client: AsyncClient, admin_headers: dict[str, str]):
    for i in range(3):
        await client.post(
            "/api/v1/admin/roles",
            headers=admin_headers,
            json={"name": f"paged_role_{i}", "display_name": f"Paged {i}", "guard_name": "api"},
        )
    resp = await client.get("/api/v1/admin/roles?page=1&page_size=2", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 2
    # admin_headers fixture seeds 1 superadmin role; 3 more created here → 4 total
    assert data["meta"]["total"] == 4
    assert data["meta"]["has_next"] is True


async def test_list_roles_sort_by_name(client: AsyncClient, admin_headers: dict[str, str]):
    await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "zzz_role", "display_name": "ZZZ", "guard_name": "api"},
    )
    await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "aaa_role", "display_name": "AAA", "guard_name": "api"},
    )
    resp = await client.get("/api/v1/admin/roles?sort_by=name&sort_order=asc", headers=admin_headers)
    assert resp.status_code == 200
    names = [r["name"] for r in resp.json()["data"]["items"]]
    assert names == sorted(names)
