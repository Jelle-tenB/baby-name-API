"""
Lets the user create a new group.
Needs the user to be logged in.
The user can only have 2 groups at a time.
Max 2 users per group.

Returns a group code that is 6 characters long.
The group code is unique and is used to identify the group.
"""
#TODO: fix this endpoint!

# Standard Library
from json import loads, dumps
from secrets import token_hex

# Third-Party Libraries
from fastapi import HTTPException, APIRouter, Depends, Cookie, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, limiter


new_group_router = APIRouter()


async def check_group_code(db):
    """Check to see if the group_code is unique before returning"""

    while True:
        group_code = str(token_hex(3))
        query = "SELECT 1 FROM groups WHERE group_code = ?;"
        params: tuple[str] = (group_code,)
        async with db.execute(query, params) as cursor:
            # If no result is found, it means the code is unique
            if not await cursor.fetchone():
                return group_code


@new_group_router.post("/new_group",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example":
                        {"success": "new group created",
                        "group_code": "group_code"}
        }}},
        400:
            {"description": "bad request - unsuccessful response",
            "content": {
                "application/json": {
                    "example":
                        {"error: database error"}
}}}})
@limiter.limit("10/minute")
async def new_group(
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None)
):

    """POST request to make a new group and gives a 6 character group code back.
    A maximum of 2 groups per user and max 2 users per group."""

    if not session_token:
        raise HTTPException(status_code=401, detail="error: not logged in")

    # Reads the cookie.
    data = loads(session_token)
    user_id = int(data["id"])
    user_name = data["username"]

    group_code = await check_group_code(db)

    try:
        # Query to see how many groups the user might be in.
        existing_group = """
        SELECT COUNT(*) FROM link_users WHERE user_id = ?;
        """

        params: tuple[int] = (user_id,) # type: ignore
        async with db.execute(existing_group, params) as cursor:
            row = await cursor.fetchone()
            group_count = row[0] if row else 0

        # Prevents users from having more than 2 groups.
        if group_count >= 2:
            return JSONResponse(
                content={"error": f"user {user_name} already has 2 groups"},
                status_code=400)

        # Query to save the group code.
        insert_code = """
        INSERT INTO groups (group_code) VALUES (?) RETURNING group_id;
        """

        params: tuple[str] = (group_code,) # type: ignore
        async with db.execute(insert_code, params) as cursor:
            row = await cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=500, detail="error: could not retrieve group_id")
            group_id = int(row[0])
            await db.commit()

        # Query to save the link between users.
        insert_link = """
        INSERT INTO link_users (user_id, group_id) VALUES (?, ?);
        """

        params: tuple[int, int] = (user_id, group_id,)
        await db.execute(insert_link, params)
        await db.commit()

        response = JSONResponse(
            content={"success": "new group created",
                    "group_code": group_code},
            status_code=200)

        data["group_codes"].update({group_code: ""})
        cookie_data = dumps(data)
        response.set_cookie(
            key="session_token",
            value=cookie_data
        )

        return response

    except Error as e:
        raise HTTPException(status_code=400, detail="error: database error") from e
