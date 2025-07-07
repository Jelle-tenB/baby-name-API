import pytest
from httpx import AsyncClient, ASGITransport
import http.cookies
import json
from main import app

how_to_run = "pytest -n auto testing.py"

URL = "http://test"
TEST_USER = "aoiug9190"
TEST_PASSWORD = "validPassword123"
LIKED_NAMES = [1, 2]
DISLIKED_NAMES = [3, 4]
TEST_GROUP = "71cef3"

transport = ASGITransport(app=app)

# ------ NOT LOGGED IN TESTS ------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint,method", [
    ("/cookie", "get"),
    ("/like_list", "get"),
    ("/dislike_list", "get"),
    ("/group_liked", "get"),
    ("/compare_likes", "get"),
    ("/preferences", "post"),
    ("/liked", "post"),
    ("/disliked", "post"),
    ("/new_group", "post"),
    ("/add_to_group", "post"),
    ("/unlike", "delete"),
    ("/undislike", "delete"),
    ("/delete_user", "delete"),
])
async def test_protected_endpoints_require_login(endpoint, method):
    async with AsyncClient(
        transport=transport, base_url=URL
    ) as ac:
        resp = await getattr(ac, method)(endpoint)
        assert resp.status_code in (401, 422)
# -----------------------------------------------------------------

# ------ SIMILAR TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_similar_names():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        response = await client.get("/similar", params={"name_id": [1, 2]})

    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    assert all(isinstance(item, dict) for item in json_response)
# -----------------------------------------------------------------

# ------ SEARCH TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_search_valid_params():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        response = await client.get("/search",
                    params={"letter": "a", "gender": "m", "country": "US", "start": 1})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_search_invalid_letter():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        response = await client.get("/search",
                    params={"letter": "1"})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_search_invalid_params():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        response = await client.get("/search",
                    params={})
    assert response.status_code == 400
#-----------------------------------------------------------------


# ------ USER CREATION TESTS -------------------------------------
@pytest.mark.asyncio
async def test_create_new_user():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        response = await client.post("/new_user", json={
            "username": TEST_USER,
            "password": TEST_PASSWORD
        })

        assert response.status_code == 200

        json_response = response.json()
        assert "success" in json_response
        assert TEST_USER in json_response["success"]
        assert "recovery token" in json_response

        # Extract cookies
        # After receiving the response
        set_cookie = response.headers.get("set-cookie")
        assert set_cookie is not None

        cookie = http.cookies.SimpleCookie()
        cookie.load(set_cookie)

        # Extract and parse the actual cookie value
        session_token_str = cookie["session_token"].value

        # Convert the cookie value (a JSON string) to a dictionary
        session_token_dict = json.loads(session_token_str)

        # Save the dictionary directly to a file
        with open("session_token.json", "w", encoding="utf-8") as f:
            json.dump(session_token_dict, f, indent=2)

        # Save recovery token and session token to file
        with open("recovery_token.json", "w", encoding="utf-8") as f:
            json.dump({"recovery_token": json_response["recovery token"]}, f)

        assert "session_token" in set_cookie

@pytest.mark.asyncio
async def test_create_existing_user():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        response = await client.post("/new_user", json={
            "username": TEST_USER,
            "password": TEST_PASSWORD
        })

        # Assert status code
        assert response.status_code == 400

        # Check response body
        json_response = response.json()
        # assert "error" in json_response
        assert f"error: {TEST_USER} is already taken." in json_response['detail']

@pytest.mark.asyncio
async def test_create_user_invalid():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        response = await client.post("/new_user",
            json={
                "username": "a",
                "password": "short"
        })

        # Assert status code
        assert response.status_code == 422
# -----------------------------------------------------------------


# ------ USER PREFERENCES TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_user_preferences():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Set user preferences
        response = await client.post("/preferences",
            cookies={"session_token": json.dumps(session_token)},
            json={
                "liked": LIKED_NAMES,
                "disliked": DISLIKED_NAMES
        })
        # Assert status code
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_user_preferences_invalid():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)
            print(session_token)

        # Set user preferences with invalid data
        response = await client.post("/preferences",
            cookies={"session_token": json.dumps(session_token)},
            json={
                "liked": "invalid_data",
                "disliked": "invalid_data"
        })
        # Assert status code
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_user_preferences_empty():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Set user preferences with empty data
        response = await client.post("/preferences",
            cookies={"session_token": json.dumps(session_token)},
            json={
                "liked": [],
                "disliked": []
        })
        # Assert status code
        assert response.status_code == 400
# -------------------------------------------------------------------


# ------ USER LIKE_LIST TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_like_list():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Get user like list
        response = await client.get("/like_list",
                    cookies={"session_token": json.dumps(session_token)})

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        response_ids = [item["id"] for item in json_response]
        assert all(name_id in response_ids for name_id in LIKED_NAMES)
# -------------------------------------------------------------------

# ------ USER DISLIKE_LIST TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_dislike_list():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Get user dislike list
        response = await client.get("/dislike_list",
                    cookies={"session_token": json.dumps(session_token)})

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        response_ids = [item["id"] for item in json_response]
        assert all(name_id in response_ids for name_id in DISLIKED_NAMES)
# -------------------------------------------------------------------

# ------ CREATE NEW GROUP TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_create_new_group():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Create a new group
        response = await client.post("/new_group",
                    cookies={"session_token": json.dumps(session_token)})

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        group_codes = json_response["group_code"]

        session_token["group_codes"] += [group_codes]

        with open("session_token.json", "w", encoding="utf-8") as f:
            json.dump(session_token, f)

        assert "success" in json_response
        assert "group_code" in json_response
# -------------------------------------------------------------------

# ------ ADD TO GROUP TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_add_to_invalid_group():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Attempt to add a name to an invalid group
        response = await client.post("/add_to_group",
                    cookies={"session_token": json.dumps(session_token)},
                    json={"group_code": "invalid_group"})

        # Assert status code
        assert response.status_code == 404

        # Check response body
        json_response = response.json()
        assert "error" in json_response


@pytest.mark.asyncio
async def test_add_to_group():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Add a name to the group
        response = await client.post("/add_to_group",
                    cookies={"session_token": json.dumps(session_token)},
                    json={"group_code": TEST_GROUP})

        session_token["group_codes"].append(TEST_GROUP)

        with open("session_token.json", "w", encoding="utf-8") as f:
            json.dump(session_token, f)

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        assert "success" in json_response
        assert f"{TEST_GROUP}" in json_response
# -------------------------------------------------------------------

# ------ ACCOUNT RECOVERY TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_invalid_username_account_recovery():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        response = await client.post("/account_recovery", json={
            "username": "nonexistent_user",
            "recovery_token": "invalid_token",
            "new_password": "newPassword123"
        })

        # Assert status code
        assert response.status_code == 404

        # Check response body
        json_response = response.json()
        assert "error" in json_response['detail']

@pytest.mark.asyncio
async def test_invalid_token_account_recovery():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        response = await client.post("/account_recovery", json={
            "username": TEST_USER,
            "recovery_token": "invalid_token",
            "new_password": TEST_PASSWORD
        })

        # Assert status code
        assert response.status_code == 401

        # Check response body
        json_response = response.json()
        assert "error" in json_response['detail']

@pytest.mark.asyncio
async def test_valid_account_recovery():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("recovery_token.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            recovery_token = data["recovery_token"]

        response = await client.post("/account_recovery", json={
            "username": TEST_USER,
            "recovery_token": recovery_token,
            "new_password": "newValidPassword123"
        })

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        assert "success" in json_response
# ------------------------------------------------------------------

# ------ GROUP LIKED TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_group_liked():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Get group liked names
        response = await client.get("/group_liked",
                    cookies={"session_token": json.dumps(session_token)})

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        assert isinstance(json_response, list)
        assert len(json_response) > 0
# ------------------------------------------------------------------

# ------ COMPARE LIKES TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_compare_likes_invalid_group():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Attempt to compare likes with an invalid group code
        response = await client.get("/compare_likes",
                    cookies={"session_token": json.dumps(session_token)},
                    params={"group_code": "123456"})

        # Assert status code
        assert response.status_code == 400

        # Check response body
        json_response = response.json()
        assert "error" in json_response['detail']

@pytest.mark.asyncio
async def test_compare_likes():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Compare likes
        response = await client.get("/compare_likes",
                    cookies={"session_token": json.dumps(session_token)},
                    params={"group_code": TEST_GROUP})

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        assert isinstance(json_response, list)
        assert len(json_response) > 0
# ------------------------------------------------------------------

# ------ UNLIKE TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_unlike_invalid():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Attempt to unlike a name that is not liked
        response = await client.delete("/unlike",
                    cookies={"session_token": json.dumps(session_token)},
                    params={"name_ids": ["string"]})

        # Assert status code
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_unlike():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Unlike a name
        response = await client.delete("/unlike",
                    cookies={"session_token": json.dumps(session_token)},
                    params={"name_ids": [LIKED_NAMES[0]]})

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        assert "success" in json_response
        assert "deleted 1" in json_response["success"]
# ------------------------------------------------------------------

# ------ UNDISLIKE TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_undislike_invalid():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Attempt to undislike a name that is not disliked
        response = await client.delete("/undislike",
                    cookies={"session_token": json.dumps(session_token)},
                    params={"name_ids": ["string"]})

        # Assert status code
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_undislike():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)

        # Undislike a name
        response = await client.delete("/undislike",
                    cookies={"session_token": json.dumps(session_token)},
                    params={"name_ids": [DISLIKED_NAMES[0]]})

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        assert "success" in json_response
        assert "deleted 1" in json_response["success"]
# ------------------------------------------------------------------

# LEAVE THESE TESTS FOR LAST
# ------ DELETE GROUP TESTS ------------------------------------------
@pytest.mark.asyncio
async def test_delete_group():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)
            group_codes = session_token.get("group_codes")

        # Now delete the group
        response = await client.delete("/delete_group",
                    cookies={"session_token": json.dumps(session_token)},
                    params={"group_code": group_codes[0]})

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        assert "success" in json_response
        assert f"{group_codes[0]}" in json_response["success"]
# ------------------------------------------------------------------

# ------ USER DELETION TESTS ----------------------------------------
@pytest.mark.asyncio
async def test_delete_user():
    async with AsyncClient(transport=transport, base_url=URL) as client:
        with open("session_token.json", "r", encoding="utf-8") as f:
            session_token = json.load(f)
        # Now delete the user
        response = await client.delete("/delete_user",
                    cookies={"session_token": json.dumps(session_token)})

        # Assert status code
        assert response.status_code == 200

        # Check response body
        json_response = response.json()
        assert "success" in json_response
        assert f"{TEST_USER}" in json_response["success"]
# ------------------------------------------------------------------
