"""
Login API endpoint for the application.
This endpoint allows a user to log in using their username and password.
It returns a cookie which contains:
    id,
    session token,
    username,
    group_codes,
    max_age (24 hours).
In that order.
With a maximum of 5 attempts, user will be locked out after the fifth failed attempt.
"""

# Standard Library
from typing import Annotated
from json import dumps
from datetime import timedelta, datetime

# Third-Party Libraries
from fastapi import HTTPException, APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field as field
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, pwd_context, save_session_token, limiter


login_router = APIRouter()

MAX_ATTEMPTS = 5  # Maximum allowed login attempts
LOCKOUT_DURATION = timedelta(minutes=10)  # Lockout duration after max attempts


class Item(BaseModel):
    """Model for the login request body."""
    # Annotated is used to add metadata to the fields, such as description and constraints.
    username: Annotated[
        str, field(description= "username", min_length=4, max_length=12)]
    password: Annotated[
        str, field(description= "password", min_length=8, max_length=32)]


@login_router.post("/login",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example":
                        {"success": "username",
                        "id": 1}
        }}},
        400: {
            "description": "bad request - unsuccessful response",
            "content": {
                "application/json": {
                    "example":
                        {"error: incorrect username or password."}
}}}})
#@limiter.limit("5/minute")
async def login(
    item: Item,
    request: Request, # pylint: disable=unused-argument
    db: Connection = Depends(get_db)
):

    """
    Login API endpoint for the application.\n
    This endpoint allows a user to log in using their username and password.\n
    It returns a cookie which contains:
        id,
        session token,
        username,
        group_codes,
        max_age (24 hours).
    In that order.\n
    With a maximum of 5 attempts, user will be locked out after the fifth failed attempt.
    """

    # Query to find the user's data.
    query = """
    SELECT username, password, user_id FROM users WHERE username = ?;
    """

    groupcode_query = """
    SELECT CAST(g.group_code AS TEXT),
        u.username
    FROM link_users AS lu_self
    JOIN groups AS g 
    ON g.group_id = lu_self.group_id
    LEFT JOIN link_users AS lu_other 
    ON lu_other.group_id = lu_self.group_id
    AND lu_other.user_id <> lu_self.user_id
    LEFT JOIN users AS u 
    ON u.user_id = lu_other.user_id
    WHERE lu_self.user_id = ?
    ORDER BY g.group_code, u.username;
    """

    username = item.username.lower()

    try:
        # Check if the user exists in the database.
        async with db.execute(query, (username,)) as cursor:
            row = await cursor.fetchone()

        # Check lockout status BEFORE verifying password
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        ip_address = (
            x_forwarded_for.split(",")[0].strip()
            if x_forwarded_for
            else (getattr(request.client, "host", None) or "unknown")
        )

        if not row:
            # if the user does not exist, increment the failed login attempts
            last_attempt = datetime.now().replace(microsecond=0)
            # Try to update first
            result = await db.execute("""
                UPDATE failed_logins
                SET attempts = attempts + 1,
                    last_attempt = ?
                WHERE ip = ?""",
                (last_attempt, ip_address))
            await db.commit()

            if result.rowcount == 0:
                # No existing record was updated → insert new
                await db.execute("""
                    INSERT INTO failed_logins (ip, attempts, last_attempt)
                    VALUES (?, ?, ?)""",
                    (ip_address, 1, last_attempt))
                await db.commit()

            async with db.execute("""
            SELECT attempts, last_attempt FROM failed_logins
            WHERE ip = ?
            ORDER BY last_attempt DESC LIMIT 1
            """, (ip_address,)) as cursor:
                attempts_row = await cursor.fetchone()

            if attempts_row:
                attempts, last_attempt = attempts_row
                last_attempt = datetime.strptime(last_attempt, "%Y-%m-%d %H:%M:%S")
                now = datetime.now().replace(microsecond=0)

                if attempts >= MAX_ATTEMPTS:
                    unlock_time = last_attempt + LOCKOUT_DURATION
                    remaining = (unlock_time - now).total_seconds()
                    if remaining > 0:
                        raise HTTPException(
                            status_code=429,
                            detail=f"error: ip locked for {int(remaining)} seconds."
                        )
            raise HTTPException(status_code=401, detail="error: incorrect username or password")

        # Verifies the user's password.
        hashed_pwd = row[1]
        user_id = row[2]

        async with db.execute("""
            SELECT attempts, last_attempt FROM failed_logins
            WHERE ip = ?
            ORDER BY last_attempt DESC LIMIT 1
        """, (ip_address,)) as cursor:
            attempts_row = await cursor.fetchone()

        if attempts_row:
            attempts, last_attempt = attempts_row
            last_attempt = datetime.strptime(last_attempt, "%Y-%m-%d %H:%M:%S")
            now = datetime.now().replace(microsecond=0)

            if attempts >= MAX_ATTEMPTS:
                unlock_time = last_attempt + LOCKOUT_DURATION
                remaining = (unlock_time - now).total_seconds()
                if remaining > 0:
                    raise HTTPException(
                        status_code=429,
                        detail=f"error: ip locked for {int(remaining)} seconds."
                    )

        # Now verify the password
        if not pwd_context.verify(item.password, hashed_pwd):
            last_attempt = datetime.now().replace(microsecond=0)
            # Try to update first
            result = await db.execute("""
                UPDATE failed_logins
                SET attempts = attempts + 1,
                    last_attempt = ?
                WHERE ip = ?""",
                (last_attempt, ip_address))
            await db.commit()

            if result.rowcount == 0:
                # No existing record was updated → insert new
                await db.execute("""
                    INSERT INTO failed_logins (ip, attempts, last_attempt)
                    VALUES (?, ?, ?)""",
                    (ip_address, 1, last_attempt))
                await db.commit()

            raise HTTPException(status_code=401, detail="error: incorrect username or password")


        # Saves the session token to the DB.
        session_token = await save_session_token(user_id=user_id, db=db)

        async with db.execute(groupcode_query, (user_id,)) as cursor:
            rows = await cursor.fetchall()

        group_codes = {group_code: (username or "") for group_code, username in rows}

        response = JSONResponse(
            content={"success": f"{username}",
                "id": f"{user_id}",
                "group codes": group_codes},
                status_code=200)

        origin = request.headers.get("origin")

        if not origin:
            origin = request.headers["host"]
            print(origin, "test1")

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
            "username": str(username)}

        data["group_codes"] = group_codes
        cookie_data = dumps(data)

        maxage = int(timedelta(hours=24).total_seconds())

        # Sets the cookie for the user.
        if origin in ["http://127.0.0.1:5000",
                      "http://127.0.0.1:5501",
                      "127.0.0.1:5000",
                      "127.0.0.1:5501"]:
            response.set_cookie(
                key='session_token',
                value=cookie_data,
                httponly=False,
                secure=True,    # Use True in production to send cookie over HTTPS only
                max_age=maxage,
                samesite='lax',    # Helps with CSRF protection
                domain='127.0.0.1')
        else:
            response.set_cookie(
                key='session_token',
                value=cookie_data,
                httponly=False,
                secure=True,    # Use True in production to send cookie over HTTPS only
                max_age=maxage,
                samesite='lax',    # Helps with CSRF protection
                domain='.roads-technology.nl')

    except Error as e:
        raise HTTPException(status_code=401, detail="error: incorrect username or password") from e

    await db.execute("DELETE FROM failed_logins WHERE ip = ?", (ip_address,))
    await db.commit()

    return response
