from httpx import AsyncClient


async def test_list_users_with_permission(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json()["data"], list)


async def test_list_users_no_permission(client: AsyncClient, user_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/users", headers=user_headers)
    assert resp.status_code == 403


async def test_list_users_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/admin/users")
    assert resp.status_code == 401


async def test_create_user_success(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "created@test.com",
            "username": "createduser",
            "full_name": "Created User",
            "password": "Password1",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["email"] == "created@test.com"


async def test_create_user_duplicate_email(client: AsyncClient, admin_headers: dict[str, str]):
    payload = {
        "email": "dupadmin@test.com",
        "username": "dupadmin1",
        "full_name": "Dup",
        "password": "Password1",
    }
    await client.post("/api/v1/admin/users", headers=admin_headers, json=payload)
    payload["username"] = "dupadmin2"
    resp = await client.post("/api/v1/admin/users", headers=admin_headers, json=payload)
    assert resp.status_code == 409


async def test_get_user_found(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "getme@test.com",
            "username": "getmeuser",
            "full_name": "Get Me",
            "password": "Password1",
        },
    )
    uid = create.json()["data"]["id"]
    resp = await client.get(f"/api/v1/admin/users/{uid}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == uid


async def test_get_user_not_found(client: AsyncClient, admin_headers: dict[str, str]):
    resp = await client.get("/api/v1/admin/users/9999", headers=admin_headers)
    assert resp.status_code == 404


async def test_toggle_active(client: AsyncClient, admin_headers: dict[str, str]):
    create = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "toggle@test.com",
            "username": "toggleuser",
            "full_name": "Toggle User",
            "password": "Password1",
        },
    )
    uid = create.json()["data"]["id"]
    original_active = create.json()["data"]["is_active"]
    resp = await client.patch(f"/api/v1/admin/users/{uid}/toggle-active", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] != original_active


async def test_create_user_with_roles(client: AsyncClient, admin_headers: dict[str, str]):
    role_resp = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "testrole", "display_name": "Test Role", "guard_name": "api"},
    )
    rid = role_resp.json()["data"]["id"]
    resp = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "withrole@test.com",
            "username": "withroleuser",
            "full_name": "With Role",
            "password": "Password1",
            "role_ids": [rid],
        },
    )
    assert resp.status_code == 201
    role_names = [r["name"] for r in resp.json()["data"]["roles"]]
    assert "testrole" in role_names


async def test_assign_role_success(client: AsyncClient, admin_headers: dict[str, str]):
    user_resp = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "assignrole@test.com",
            "username": "assignroleuser",
            "full_name": "Assign Role",
            "password": "Password1",
        },
    )
    uid = user_resp.json()["data"]["id"]
    role_resp = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "assignablerole", "display_name": "Assignable", "guard_name": "api"},
    )
    rid = role_resp.json()["data"]["id"]
    resp = await client.post(
        f"/api/v1/admin/users/{uid}/roles",
        headers=admin_headers,
        json={"role_id": rid},
    )
    assert resp.status_code == 200
    role_names = [r["name"] for r in resp.json()["data"]["roles"]]
    assert "assignablerole" in role_names


async def test_assign_role_duplicate(client: AsyncClient, admin_headers: dict[str, str]):
    user_resp = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "duproleasgn@test.com",
            "username": "duproleasgnuser",
            "full_name": "Dup Role",
            "password": "Password1",
        },
    )
    uid = user_resp.json()["data"]["id"]
    role_resp = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "dupablerole", "display_name": "Dupable", "guard_name": "api"},
    )
    rid = role_resp.json()["data"]["id"]
    await client.post(f"/api/v1/admin/users/{uid}/roles", headers=admin_headers, json={"role_id": rid})
    resp = await client.post(f"/api/v1/admin/users/{uid}/roles", headers=admin_headers, json={"role_id": rid})
    assert resp.status_code == 409


async def test_revoke_role_success(client: AsyncClient, admin_headers: dict[str, str]):
    user_resp = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "revokerole@test.com",
            "username": "revokeroleuser",
            "full_name": "Revoke Role",
            "password": "Password1",
        },
    )
    uid = user_resp.json()["data"]["id"]
    role_resp = await client.post(
        "/api/v1/admin/roles",
        headers=admin_headers,
        json={"name": "revokablerole", "display_name": "Revokable", "guard_name": "api"},
    )
    rid = role_resp.json()["data"]["id"]
    await client.post(f"/api/v1/admin/users/{uid}/roles", headers=admin_headers, json={"role_id": rid})
    resp = await client.delete(f"/api/v1/admin/users/{uid}/roles/{rid}", headers=admin_headers)
    assert resp.status_code == 200
    role_names = [r["name"] for r in resp.json()["data"]["roles"]]
    assert "revokablerole" not in role_names


async def test_assign_direct_permission_success(client: AsyncClient, admin_headers: dict[str, str]):
    user_resp = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "assignperm@test.com",
            "username": "assignpermuser",
            "full_name": "Assign Perm",
            "password": "Password1",
        },
    )
    uid = user_resp.json()["data"]["id"]
    perm_resp = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "custom.assign", "display_name": "Custom Assign", "guard_name": "api"},
    )
    pid = perm_resp.json()["data"]["id"]
    resp = await client.post(
        f"/api/v1/admin/users/{uid}/permissions",
        headers=admin_headers,
        json={"permission_id": pid},
    )
    assert resp.status_code == 200
    direct_perm_names = [p["name"] for p in resp.json()["data"]["direct_permissions"]]
    assert "custom.assign" in direct_perm_names


async def test_revoke_direct_permission_success(client: AsyncClient, admin_headers: dict[str, str]):
    user_resp = await client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "revokeperm@test.com",
            "username": "revokepermuser",
            "full_name": "Revoke Perm",
            "password": "Password1",
        },
    )
    uid = user_resp.json()["data"]["id"]
    perm_resp = await client.post(
        "/api/v1/admin/permissions",
        headers=admin_headers,
        json={"name": "custom.revoke", "display_name": "Custom Revoke", "guard_name": "api"},
    )
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
    assert "custom.revoke" not in direct_perm_names
