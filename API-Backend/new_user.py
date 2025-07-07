"""
Lets the user create an account.
By giving a username and password.
The username must be unique.
The password must be between 8 and 32 characters.
The user will be given a recovery token that they must store.

Also automatically logs the user in by creating a cookie.
"""

# Standard Library
from typing import Annotated
from secrets import token_hex
from datetime import timedelta
from json import dumps
from datetime import datetime

# Third-Party Libraries
from pydantic import BaseModel, Field as field
from fastapi import Depends, HTTPException, APIRouter, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, hash_pwd, timelater, set_recovery_token, limiter


new_user_router = APIRouter()


class Item(BaseModel):
    username: Annotated[
        str, field(description= "username must be unique", min_length=4, max_length=12)]
    password: Annotated[
        str, field(description= "password", min_length=8, max_length=32)]


@new_user_router.post("/new_user",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example":
                        {"success": "'username' successfully created.",
                         "recovery token": "'recovery_token'"}
        }}},
        400:
            {"description": "bad request - unsuccessful response",
            "content": {
                "application/json": {
                    "example":
                        {"error: 'username' is already taken."}
}}}})
@limiter.limit("10/minute")
async def create_new_user(
    item: Item,
    request: Request, # pylint: disable=unused-argument
    db: Connection = Depends(get_db)
):

    """POST request to add a new user to the database and return a recovery token.\n
    The user MUST store their own recovery token.\n
    Username MUST be unique and between 4 and 12 characters long.\n
    Password MUST be between 8 and 32 characters long.\n
    The user will be logged in automatically by creating a session token cookie.\n"""

    headers = request.headers

    hashed_password = hash_pwd(item.password)
    session_token = token_hex(20)
    session_expiration = timelater()
    recovery_token = await set_recovery_token()

    username = item.username.lower()

    # Query to save the user login information.
    query = """
    INSERT INTO users (username, password, session_token, session_expiration, recovery_token, last_login)
    VALUES (?, ?, ?, ?, ?, ?);
    """

    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        async with db.execute(query, (username, hashed_password, session_token, session_expiration, recovery_token, now)) as cursor:
            await db.commit()
            user_id = cursor.lastrowid
    except Error as e:
        raise HTTPException(status_code=400, detail=f"error: {username} is already taken.") from e

    response = JSONResponse(content={"success":f"{username} successfully created.",
                                     "recovery token": f"{recovery_token}"},
                            status_code=200)

    maxage = int(timedelta(hours=12).total_seconds())

    origin = request.headers.get("origin")

    if not origin:
        origin = headers["host"]

    if origin in ["https://babynamegenerator.roads-technology.nl",
                "https://apibabynamegenerator.roads-technology.nl",
                "http://127.0.0.1:5000",
                "http://127.0.0.1:5501",
                "127.0.0.1:5000",
                "127.0.0.1:5501"]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = """DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"""
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    else:
        response.headers["Access-Control-Allow-Origin"] = "null"  # Block unauthorized origins

    data = {
            "id": user_id,
            "session_token": session_token,
            "username": str(username),
            "group_codes": []}

    cookie_data = dumps(data)

    # Sets the cookie for the user.
    if origin in ["http://127.0.0.1:5000",
                    "http://127.0.0.1:5501",
                    "127.0.0.1:5000",
                    "127.0.0.1:5501"]:
        response.set_cookie(
            key='session_token',
            value=cookie_data,
            httponly=False,  # Prevent JavaScript from accessing the cookie
            secure=True,    # Use True in production to send cookie over HTTPS only
            max_age=maxage,
            samesite='lax',    # Helps with CSRF protection
            domain='127.0.0.1')
    else:
        response.set_cookie(
            key='session_token',
            value=cookie_data,
            httponly=True,  # Prevent JavaScript from accessing the cookie
            secure=True,    # Use True in production to send cookie over HTTPS only
            max_age=maxage,
            samesite='lax',    # Helps with CSRF protection
            domain='.roads-technology.nl')

    return response
