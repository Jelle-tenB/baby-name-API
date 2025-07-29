"""
This lets the user delete a group.
The user must be in the group to delete it.
The user must be logged in (have a valid cookie) to delete a group.
"""

# Standard Library
from json import loads, dumps

# Third-Party Libraries
from fastapi import HTTPException, Depends, Cookie, APIRouter, Query, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, limiter, validate_token


delete_group_router = APIRouter()


@delete_group_router.delete("/delete_group",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example":
                        {"success": "group ab1234 has successfully been deleted"}
        }}},
        400: {
            "description": "bad Request - unsuccessful response",
            "content": {
                "application/json": {
                    "example": {"error: not logged in"}
}}}})
@limiter.limit("10/minute")
async def delete_group(
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    group_code: str = Query(..., max_length=6, min_length=6, examples=["ab1234"]),
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None)
):

    """DELETE, request to remove a group based on the group code."""

    # Check if the user is logged in and so has the correct cookie.
    if not session_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    # Reads the cookie.
    user_info = loads(session_token)
    user_id = user_info["id"]
    token = user_info["session_token"]
    await validate_token(token, user_id, db)

    try:
        # Query to check if user is indeed in the given group.
        code_query = """
        SELECT user_id
        FROM link_users
        JOIN groups ON link_users.group_id = groups.group_id
        WHERE group_code = ?;
        """

        async with db.execute(code_query, (group_code,)) as cursor:
            rows = [row[0] for row in await cursor.fetchall()]

        token = loads(session_token)
        if user_id == token["id"]:
            if user_id in rows:
                pass
            else:
                raise HTTPException(status_code=401, detail=f"error: you are not in group {group_code}")
        else:
            raise HTTPException(status_code=401, detail=f"error: you are not in group {group_code}")

    except Error as e:
        raise HTTPException(status_code=400, detail="error: database error") from e

    # check if the group has 1 or 2 users
    count_query = """
        SELECT COUNT(*)
        FROM link_users
        WHERE group_id = (
            SELECT group_id
            FROM groups
            WHERE group_code = ?
        );
    """

    # delete dependent rows first
    delete_link_query = """
        DELETE FROM link_users
        WHERE group_id IN (
            SELECT group_id
            FROM groups
            WHERE group_code = ?
        );
    """

    # then delete parent rows
    delete_group_query = """
        DELETE FROM groups
        WHERE group_code = ?;
    """

    # delete only the link to the user, if there are 2 users in the group.
    only_link_query = """
        DELETE FROM link_users
        WHERE group_id = (
            SELECT group_id
            FROM groups
            WHERE group_code = ?
        )
        AND user_id = ?;
    """

    try:
        async with db.execute(count_query, (group_code,)) as cursor:
            row = await cursor.fetchone()
    except Error as e:
        raise HTTPException(status_code=500, detail="error: database error") from e

    if row[0] < 2:
        try:
            await db.execute(delete_link_query, (group_code,))
            await db.execute(delete_group_query, (group_code,))
            await db.commit()
        except Error as e:
            raise HTTPException(status_code=500, detail="error: database error") from e
    else:
        try:
            await db.execute(only_link_query, (group_code, user_id,))
            await db.commit()
        except Error as e:
            raise HTTPException(status_code=500, detail="error: database error") from e

    response = JSONResponse(status_code=200,
                    content={"success": f"group {group_code} has successfully been deleted for you"})

    del user_info["group_codes"][group_code]
    cookie_data = dumps(user_info)
    response.set_cookie(
        key="session_token",
        value=cookie_data
    )

    return response
