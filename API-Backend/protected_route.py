"""
Route to handle login with a session token in the cookie.
Requires a valid session token to be passed in the cookie.
The session token is validated and a new session token is generated and returned in the cookie.
"""

# Standard library imports
from json import dumps, loads
from datetime import timedelta

# Third-party library imports
from fastapi import HTTPException, Depends, Cookie, APIRouter, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection

# Local application imports
from imports import get_db, save_session_token, limiter, validate_token


cookie_router = APIRouter()


@cookie_router.get("/cookie",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example":
                        {"success": "username",
                        "Id": 1}
        }}},
        400:
            {"description": "bad request - unsuccessful response",
            "content": {
                "application/json": {
                    "example":
                        {"error: login failed"}
}}}})
@limiter.limit("10/minute")
async def protected_route(
    request: Request, # pylint: disable=unused-argument
    session_token: str = Cookie(None),
    db: Connection = Depends(get_db)
):

    """GET request to login with an authorisation token in the cookie."""

    if not session_token:
        raise HTTPException(status_code=401, detail="error: not logged in")

    # Reads the cookie.
    user_info = loads(session_token)
    user_id = user_info["id"]
    token = user_info["session_token"]
    username = user_info["username"]
    await validate_token(token, user_id, db)

    #Saves and returns the new session token.
    session_token = await save_session_token(user_id=user_id, db=db)

    maxage = int(timedelta(hours=12).total_seconds())

    # Query to find a user's group code
    groupcode_query = """
        SELECT g.group_code,
            u.username
        FROM link_users AS lu_self
        JOIN link_users AS lu_other 
        ON lu_other.group_id = lu_self.group_id
        AND lu_other.user_id <> lu_self.user_id
        JOIN groups AS g 
        ON g.group_id = lu_self.group_id
        JOIN users AS u 
        ON u.user_id = lu_other.user_id
        WHERE lu_self.user_id = ?
        ORDER BY g.group_code, u.username;
        """

    async with db.execute(groupcode_query, (user_id,)) as cursor:
        rows = await cursor.fetchall()

    group_codes = {group_code: username for group_code, username in rows}

    data = {
        "id": user_id,
        "session_token": session_token,
        "username": str(username),}

    data["group_codes"] = group_codes
    cookie_data = dumps(data)

    response = JSONResponse(
        content={"success": f"{username}",
                "id": f"{user_id}",
                "group codes": group_codes},
                status_code=200)

    origin = request.headers.get("origin")
    if not origin:
        origin = request.headers["host"]

    if origin in ["https://babynamegenerator.roads-technology.nl",
                  "https://apibabynamegenerator.roads-technology.nl",
                  "http://127.0.0.1:5000",
                  "http://127.0.0.1:5501",
                  "127.0.0.1:5000",
                  "127.0.0.1:5501",
                  "127.0.0.1:5500"]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = """DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"""
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    else:
        response.headers["Access-Control-Allow-Origin"] = "null"  # Block unauthorized origins

    if origin in ["http://127.0.0.1:5000",
                  "http://127.0.0.1:5501",
                  "127.0.0.1:5000",
                  "127.0.0.1:5501",
                  "127.0.0.1:5500"]:
        response.set_cookie(
            key='session_token',
            value=cookie_data,
            httponly=False,  # Prevent JavaScript from accessing the cookie
            secure=False,    # Use True in production to send cookie over HTTPS only
            max_age=maxage,
            samesite='lax',    # Helps with CSRF protection
            domain='127.0.0.1')
    else:
        response.set_cookie(
            key='session_token',
            value=cookie_data,
            httponly=False,  # Prevent JavaScript from accessing the cookie
            secure=True,    # Use True in production to send cookie over HTTPS only
            max_age=maxage,
            samesite='lax',    # Helps with CSRF protection
            domain='.roads-technology.nl')

    return response
