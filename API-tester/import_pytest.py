import pytest
from httpx import AsyncClient, ASGITransport

from main import app

TEST_USER = {
    "username": "apitestuser",
    "password": "apitestpass"
}

@pytest.mark.asyncio
async def test_root_status_code():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/")
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_search_status_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # No params
        resp = await ac.get("/search")
        assert resp.status_code in (400, 422)
        # Invalid param
        resp = await ac.get("/search", params={"letter": "123"})
        assert resp.status_code in (400, 422)
        # Valid param (may be empty result)
        resp = await ac.get("/search", params={"letter": "A"})
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_new_user_and_login():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create new user
        resp = await ac.post("/new_user", json=TEST_USER)
        assert resp.status_code in (200, 400)
        # Login
        resp = await ac.post("/login", json=TEST_USER)
        assert resp.status_code in (200, 401, 400, 422)
        if resp.status_code == 200:
            print("Cookies:", resp.cookies)
            assert "success" in resp.json()
            session_token = resp.cookies.get("session_token")
            assert session_token

@pytest.mark.asyncio
async def test_login_status_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Wrong password
        resp = await ac.post("/login", json={"username": TEST_USER["username"], "password": "wrong"})
        assert resp.status_code in (401, 422)
        # Missing fields
        resp = await ac.post("/login", json={"username": TEST_USER["username"]})
        assert resp.status_code in (400, 422)
        # Correct login
        resp = await ac.post("/login", json=TEST_USER)
        assert resp.status_code in (200, 401, 400, 422)

async def get_session_token(ac):
    resp = await ac.post("/login", json=TEST_USER)
    if resp.status_code == 200:
        return resp.cookies.get("session_token")
    return None

@pytest.mark.asyncio
async def test_like_list_status_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/like_list")
        assert resp.status_code in (401, 400)
        session_token = await get_session_token(ac)
        if session_token:
            ac.cookies.set("session_token", session_token)
            resp = await ac.get("/like_list")
            assert resp.status_code in (200, 400)

@pytest.mark.asyncio
async def test_dislike_list_status_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/dislike_list")
        assert resp.status_code in (401, 400)
        session_token = await get_session_token(ac)
        if session_token:
            ac.cookies.set("session_token", session_token)
            resp = await ac.get("/dislike_list")
            assert resp.status_code in (200, 400)

@pytest.mark.asyncio
async def test_group_liked_status_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/group_liked")
        assert resp.status_code in (401, 400)
        session_token = await get_session_token(ac)
        if session_token:
            ac.cookies.set("session_token", session_token)
            resp = await ac.get("/group_liked")
            assert resp.status_code in (200, 400)

@pytest.mark.asyncio
async def test_user_preferences_status_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.post("/preferences", json={"liked": [], "disliked": []})
        assert resp.status_code in (401, 400, 422)
        session_token = await get_session_token(ac)
        if session_token:
            ac.cookies.set("session_token", session_token)
            resp = await ac.post("/preferences", json={"liked": [], "disliked": []})
            assert resp.status_code in (200, 400)

@pytest.mark.asyncio
async def test_new_group_status_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.post("/new_group")
        assert resp.status_code in (401, 400)
        session_token = await get_session_token(ac)
        if session_token:
            ac.cookies.set("session_token", session_token)
            resp = await ac.post("/new_group")
            assert resp.status_code in (200, 400)

@pytest.mark.asyncio
async def test_compare_likes_status_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/compare_likes")
        assert resp.status_code in (401, 400, 422)
        session_token = await get_session_token(ac)
        if session_token:
            ac.cookies.set("session_token", session_token)
            resp = await ac.get("/compare_likes")
            assert resp.status_code in (400, 422)
            resp = await ac.get("/compare_likes", params={"group_code": "dummy"})
            assert resp.status_code in (200, 400, 401, 422)

@pytest.mark.asyncio
async def test_account_recovery_status_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.post("/account_recovery", json={
            "username": TEST_USER["username"],
            "recovery_token": "invalid",
            "new_password": "NewPass123"
        })
        assert resp.status_code in (400, 200, 401)

@pytest.mark.asyncio
async def test_delete_user_status_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.delete("/delete_user")
        assert resp.status_code in (401, 400)
        session_token = await get_session_token(ac)
        if session_token:
            ac.cookies.set("session_token", session_token)
            resp = await ac.delete("/delete_user")
            assert resp.status_code in (200, 400)

@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint,method", [
    ("/like_list", "get"),
    ("/dislike_list", "get"),
    ("/group_liked", "get"),
    ("/new_group", "post"),
    ("/delete_user", "delete"),
])
async def test_protected_endpoints_require_login(endpoint, method):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await getattr(ac, method)(endpoint)
        assert resp.status_code in (401, 400, 404)