"""
Returns a list of all the names both users in a group have liked.
This is based on the user id of one of the users in the group.
That user has to be logged in.
"""

# Standard Library
from json import loads
from os import getenv

# Third-Party Libraries
from fastapi import HTTPException, APIRouter, Depends, Cookie, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, limiter, validate_token, load_project_dotenv


group_liked_router = APIRouter()
load_project_dotenv()

@group_liked_router.get("/group_liked",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example": [
                            {"group code": "ab1234",
                            "name id": 4,
                            "name": "Aadu"},
                            {"group code": "ab1234",
                            "name id": 5,
                            "name": "Aaf"}]
        }}},
        400:
            {"description": "bad request - unsuccessful response",
            "content": {
                "application/json": {
                    "example":
                        {"error: database error"}
}}}})
@limiter.limit("10/minute")
async def group_liked(
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None)
):

    """GET request to find the names BOTH users in a group have liked, based on 1 user id."""

    if not session_token:
        raise HTTPException(status_code=401, detail="not logged in")

    # Reads the user's cookie
    data = loads(session_token)
    user_id = data["id"]
    token = data["session_token"]

    await validate_token(token, user_id, db)

    # Query to find the names BOTH users in the group(s) have liked.
    query = getenv("GROUP_LIKED_NAMES")

    try:
        async with db.execute(query, (user_id,)) as cursor:
            results = await cursor.fetchall()
        if not results:
            return JSONResponse(
                content={"message": "no common likes found for this user in their groups."},
                status_code=200
            )
    except Error as e:
        raise HTTPException(status_code=400, detail="error: database error") from e

    # Format the response data
    response_data = [
        {"group code": row[0], "name id": row[1], "name": row[2]}
        for row in results]

    return JSONResponse(
        content=response_data,
        status_code=200)
