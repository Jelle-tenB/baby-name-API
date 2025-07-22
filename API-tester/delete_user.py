"""
This endpoint allows a user to delete their account.
The user must be logged in (have a valid cookie) to delete their account.
The user must be the only member of a group to automatically delete the group.
"""

# Standard Library
from json import loads

# Third-Party Libraries
from fastapi import Depends, HTTPException, Request, Cookie, APIRouter
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, limiter, validate_token


delete_user_router = APIRouter()

@delete_user_router.delete("/delete_user",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example":
                        {"success": "user ab1234 has successfully been deleted"}
        }}},
        400: {
            "description": "bad Request - unsuccessful response",
            "content": {
                "application/json": {
                    "example": {"error: not logged in"}
}}}})
@limiter.limit("10/minute")
async def delete_user(
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None)
):

    """DELETE, request to remove user based on the user's cookie."""

    # Check if the user is logged in and so has the correct cookie.
    if not session_token:
        raise HTTPException(status_code=401, detail="not logged in")

    # Reads the cookie.
    user_info = loads(session_token)
    user_id = user_info["id"]
    token = user_info["session_token"]
    user_name = user_info["username"]
    await validate_token(token, user_id, db)


    # Query to see which groups the user might be in.
    async with db.execute("""
        SELECT 
            lu.group_id
        FROM link_users lu
        WHERE lu.group_id IN (
            SELECT group_id FROM link_users WHERE user_id = ?
        );
    """, (user_id,)) as cursor:

        rows = await cursor.fetchall()

    try:
        for (group_id,) in rows:
            await db.execute("DELETE FROM link_users WHERE group_id = ? AND user_id = ?", (group_id, user_id))

        await db.execute("DELETE FROM user_liked WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM user_disliked WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()

    except Error as e:
        raise HTTPException(status_code=500, detail="error: database error") from e

    # Check for groups with no users
    async with db.execute("""
        SELECT g.group_id
        FROM groups g
        LEFT JOIN link_users lu ON g.group_id = lu.group_id
        WHERE lu.user_id IS NULL
    """) as cursor:
        empty_groups = await cursor.fetchall()

    if empty_groups:
        # Delete groups that have no users linked
        for (group_id,) in empty_groups:
            await db.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
        await db.commit()

    return JSONResponse(status_code=200, content={"success": f"{user_name} has successfully been deleted"})
