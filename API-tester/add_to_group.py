"""
Let the user add themselves to a group,
By providing the group code and their cookie.
Maximum of 2 groups per user and max 2 users per group.
"""

# Standard Library
from typing import Annotated
from json import loads, dumps

# Third-Party Libraries
from pydantic import BaseModel, Field as field
from fastapi import HTTPException, APIRouter, Depends, Cookie, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, limiter, validate_token


add_to_group_router = APIRouter()


class Item(BaseModel):
    group_code: Annotated[
        str, field(description="provide the 6 hexidecimal group code")]


@add_to_group_router.post("/add_to_group",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example": {"success: user added to group ab1234"}
            }}},
        400:
            {"description": "bad Request - unsuccessful response",
            "content": {
                "application/json": {
                    "example": {"error: login failed"}
}}}})
@limiter.limit("10/minute")
async def add_to_group(
    request: Request, # pylint: disable=unused-argument
    item: Item,
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None)
):

    """POST request to add a user to given group.
    A maximum of 2 groups per user and max 2 users per group."""

    # Check if the user is logged in and so has the correct cookie.
    if not session_token:
        raise HTTPException(status_code=401, detail="not logged in")

    # Read the cookie.
    data = loads(session_token)
    user_id = data["id"]
    token = data["session_token"]
    username = data["username"]

    await validate_token(token, user_id, db)

    group_code = item.group_code.lower()

    # Query to check how many groups a user is in.
    count_user ="""
    SELECT COUNT(*)
    FROM link_users
    WHERE user_id = ?;
    """
    try:
        async with db.execute(count_user, (user_id,)) as cursor:
            row = await cursor.fetchone()
            user_count = row[0] if row else None
    except Error as e:
        raise HTTPException(status_code=500, detail="error: database error") from e

    # Query to check if the group exists.
    check_group = """
    SELECT group_id
    FROM groups
    WHERE group_code = ?;
    """

    try:
        async with db.execute(check_group, (group_code,)) as cursor:
            row = await cursor.fetchone()
            group_id = row[0] if row else None
    except Error as e:
        raise HTTPException(status_code=500, detail="error: database error") from e

    if group_id is None:
        return JSONResponse(
            content={"error": f"group {group_code} does not exist"},
            status_code=404)

    # Prevent users from having more than 2 groups.
    if user_count is None:
        raise HTTPException(status_code=400, detail="error: user not found")
    elif user_count >= 2:
        return JSONResponse(
        content={"error": f"user {username} already has 2 groups"},
        status_code=401)

    try:
        # Query to add the user to the given group.
        query = """
        INSERT INTO link_users (user_id, group_id)
        SELECT ?, group_id
        FROM groups
        WHERE group_code = ?;
        """

        await db.execute(query, (user_id, group_code))
        await db.commit()

        response = JSONResponse(status_code=200,
                        content=f"success: user added to group {group_code}")

        data["group_codes"] = data["group_codes"] + [group_code]

        cookie_data = dumps(data)
        response.set_cookie(
            key="session_token",
            value=cookie_data
        )
        print(cookie_data)

        return response

    except Error as e:
        raise HTTPException(status_code=400, detail="error: database error") from e
