from httpx import AsyncClient

from app.tests.factories import role_payload, user_payload


async def test_list_users_with_permission(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"]["items"], list)
    assert "meta" in resp.json()["data"]


async def test_list_users_no_permission(client: AsyncClient, user_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/users", headers=user_headers)
    assert resp.status_code == 403


async def test_list_users_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/admin/users")
    assert resp.status_code == 401


async def test_create_user_success(client: AsyncClient, admin_headers: dict[str, str]):
    payload = user_payload()
    resp = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={k: v for k, v in payload.items() if k != "password"} | {"password": payload["password"]},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["email"] == payload["email"]


async def test_create_user_duplicate_email(client: AsyncClient, admin_headers: dict[str, str]):
    payload = user_payload()
    await client.post("/api/v1/admin/users", headers=admin_headers, json=payload)
    payload2 = user_payload(email=payload["email"])
    resp = await client.post("/api/v1/admin/users", headers=admin_headers, json=payload2)
    assert resp.status_code == 409


async def test_get_user_found(client: AsyncClient, admin_headers: dict[str, str]):
    payload = user_payload()
    create = await client.post("/api/v1/admin/users", headers=admin_headers, json=payload)
    uid = create.json()["data"]["id"]
    resp = await client.get(f"/api/v1/admin/users/{uid}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == uid


async def test_get_user_not_found(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/users/9999", headers=admin_headers)
    assert resp.status_code == 404


async def test_toggle_active(client: AsyncClient, admin_headers: dict[str, str]):
    payload = user_payload()
    create = await client.post("/api/v1/admin/users", headers=admin_headers, json=payload)
    uid = create.json()["data"]["id"]
    original_active = create.json()["data"]["is_active"]
    resp = await client.patch(f"/api/v1/admin/users/{uid}/toggle-active", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] != original_active


async def test_create_user_with_roles(client: AsyncClient, admin_headers: dict[str, str]):
    rp = role_payload()
    role_resp = await client.post("/api/v1/admin/roles", headers=admin_headers, json=rp)
    rid = role_resp.json()["data"]["id"]
    payload = user_payload()
    resp = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={**payload, "role_ids": [rid]},
    )
    assert resp.status_code == 201
    role_names = [r["name"] for r in resp.json()["data"]["roles"]]
    assert rp["name"] in role_names


async def test_assign_role_success(client: AsyncClient, admin_headers: dict[str, str]):
    user_resp = await client.post(
        "/api/v1/admin/users", headers=admin_headers, json=user_payload()
    )
    uid = user_resp.json()["data"]["id"]
    rp = role_payload()
    role_resp = await client.post("/api/v1/admin/roles", headers=admin_headers, json=rp)
    rid = role_resp.json()["data"]["id"]
    resp = await client.post(
        f"/api/v1/admin/users/{uid}/roles",
        headers=admin_headers,
        json={"role_id": rid},
    )
    assert resp.status_code == 200
    role_names = [r["name"] for r in resp.json()["data"]["roles"]]
    assert rp["name"] in role_names


async def test_assign_role_duplicate(client: AsyncClient, admin_headers: dict[str, str]):
    user_resp = await client.post(
        "/api/v1/admin/users", headers=admin_headers, json=user_payload()
    )
    uid = user_resp.json()["data"]["id"]
    role_resp = await client.post(
        "/api/v1/admin/roles", headers=admin_headers, json=role_payload()
    )
    rid = role_resp.json()["data"]["id"]
    await client.post(f"/api/v1/admin/users/{uid}/roles", headers=admin_headers, json={"role_id": rid})
    resp = await client.post(f"/api/v1/admin/users/{uid}/roles", headers=admin_headers, json={"role_id": rid})
    assert resp.status_code == 409


async def test_revoke_role_success(client: AsyncClient, admin_headers: dict[str, str]):
    user_resp = await client.post(
        "/api/v1/admin/users", headers=admin_headers, json=user_payload()
    )
    uid = user_resp.json()["data"]["id"]
    rp = role_payload()
    role_resp = await client.post("/api/v1/admin/roles", headers=admin_headers, json=rp)
    rid = role_resp.json()["data"]["id"]
    await client.post(f"/api/v1/admin/users/{uid}/roles", headers=admin_headers, json={"role_id": rid})
    resp = await client.delete(f"/api/v1/admin/users/{uid}/roles/{rid}", headers=admin_headers)
    assert resp.status_code == 200
    role_names = [r["name"] for r in resp.json()["data"]["roles"]]
    assert rp["name"] not in role_names


async def test_assign_direct_permission_success(client: AsyncClient, admin_headers: dict[str, str]):
    user_resp = await client.post(
        "/api/v1/admin/users", headers=admin_headers, json=user_payload()
    )
    uid = user_resp.json()["data"]["id"]
    from app.tests.factories import permission_payload
    pp = permission_payload()
    perm_resp = await client.post("/api/v1/admin/permissions", headers=admin_headers, json=pp)
    pid = perm_resp.json()["data"]["id"]
    resp = await client.post(
        f"/api/v1/admin/users/{uid}/permissions",
        headers=admin_headers,
        json={"permission_id": pid},
    )
    assert resp.status_code == 200
    direct_perm_names = [p["name"] for p in resp.json()["data"]["direct_permissions"]]
    assert pp["name"] in direct_perm_names


async def test_revoke_direct_permission_success(client: AsyncClient, admin_headers: dict[str, str]):
    user_resp = await client.post(
        "/api/v1/admin/users", headers=admin_headers, json=user_payload()
    )
    uid = user_resp.json()["data"]["id"]
    from app.tests.factories import permission_payload
    pp = permission_payload()
    perm_resp = await client.post("/api/v1/admin/permissions", headers=admin_headers, json=pp)
    pid = perm_resp.json()["data"]["id"]
    await client.post(
        f"/api/v1/admin/users/{uid}/permissions",
        headers=admin_headers,
        json={"permission_id": pid},
    )
    resp = await client.delete(
        f"/api/v1/admin/users/{uid}/permissions/{pid}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    direct_perm_names = [p["name"] for p in resp.json()["data"]["direct_permissions"]]
    assert pp["name"] not in direct_perm_names


async def test_list_users_filter_by_email(client: AsyncClient, admin_headers: dict[str, str]):
    p1 = user_payload()
    p2 = user_payload()
    await client.post("/api/v1/admin/users", headers=admin_headers, json=p1)
    await client.post("/api/v1/admin/users", headers=admin_headers, json=p2)
    resp = await client.get(f"/api/v1/admin/users?email={p1['email']}", headers=admin_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["email"] == p1["email"]


async def test_list_users_filter_by_is_active(client: AsyncClient, admin_headers: dict[str, str]):
    active_payload = user_payload()
    inactive_payload = user_payload()
    await client.post("/api/v1/admin/users", headers=admin_headers, json=active_payload)
    create = await client.post("/api/v1/admin/users", headers=admin_headers, json=inactive_payload)
    uid = create.json()["data"]["id"]
    await client.patch(f"/api/v1/admin/users/{uid}/toggle-active", headers=admin_headers)

    resp = await client.get("/api/v1/admin/users?is_active=false", headers=admin_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert all(not u["is_active"] for u in items)
    assert any(u["email"] == inactive_payload["email"] for u in items)


async def test_list_users_pagination(client: AsyncClient, admin_headers: dict[str, str]):
    for _ in range(3):
        await client.post("/api/v1/admin/users", headers=admin_headers, json=user_payload())
    resp = await client.get("/api/v1/admin/users?page=1&page_size=2", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 2
    assert data["meta"]["total"] == 4  # 3 created + 1 admin
    assert data["meta"]["has_next"] is True
    assert data["meta"]["page_size"] == 2
