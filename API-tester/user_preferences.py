"""
Lets add names to their list of liked or disliked names.
Requires the user to be logged in.
Takes a list of name_id(s) to be liked or disliked.
"""

# Standard library imports
from json import loads
from typing import List, Optional

# Third-party library imports
from fastapi import HTTPException, APIRouter, Depends, Cookie, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error
from pydantic import BaseModel, Field as field

# Local application imports
from imports import get_db, limiter, validate_token


user_preferences_router = APIRouter()


class Item(BaseModel):
    """Model for the user preferences request body."""
    disliked: Optional[List[int]] = field(
        default=None,
        description="list of name_ids to be disliked"
    )
    liked: Optional[List[int]] = field(
        default=None,
        description="list of name_ids to be liked"
    )


@user_preferences_router.post("/preferences",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example":
                        {"success": "all (dis)liked names added"}
        }}},
        400:
            {"description": "bad request - unsuccessful response",
            "content": {
                "application/json": {
                    "example": {"error: couldnt find user"}
}}}})
@limiter.limit("10/minute")
async def user_preferences(
    # Request might seem unused, but it is used by the limiter
    item: Item,
    request: Request, # pylint: disable=unused-argument
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None),
):

    """POST request to store the names a user has liked or disliked.
    Can handle batches of names."""

    liked = item.liked
    disliked = item.disliked

    if not liked and not disliked:
        raise HTTPException(status_code=400, detail="error: no names to (dis)like provided")

    if not session_token:
        raise HTTPException(status_code=401, detail="error: not logged in")

    # Reads the cookie.
    user_info = loads(session_token)
    user_id = user_info["id"]
    token = user_info["session_token"]
    await validate_token(token, user_id, db)

    disliked_names_to_insert = []
    liked_names_to_insert = []

    if liked:
        # First, get the list of name_ids the user has already liked
        placeholders = ",".join("?" for _ in liked)
        async with db.execute(
            f"SELECT name_id FROM user_disliked WHERE user_id = ? AND name_id IN ({placeholders})",
            (user_id, *liked)
        ) as cursor:
            disliked_ids = {row[0] for row in await cursor.fetchall()}

        # Filter out liked name_ids from the ones the user is trying to dislike
        names_disliked = [name_id for name_id in liked if name_id not in disliked_ids]

        liked_names_to_insert = [(name_id, user_id) for name_id in names_disliked]

        liked_query = "INSERT OR IGNORE INTO user_liked (name_id, user_id) VALUES (?, ?);"

        try:
            await db.executemany(liked_query, liked_names_to_insert)
            await db.commit()
        except Error as e:
            raise HTTPException(status_code=400, detail="error: database error") from e


    if disliked:
        # First, get the list of name_ids the user has already liked
        placeholders = ",".join("?" for _ in disliked)
        async with db.execute(
            f"SELECT name_id FROM user_liked WHERE user_id = ? AND name_id IN ({placeholders})",
            (user_id, *disliked)
        ) as cursor:
            liked_ids = {row[0] for row in await cursor.fetchall()}

        # Filter out liked name_ids from the ones the user is trying to dislike
        names_liked = [name_id for name_id in disliked if name_id not in liked_ids]

        disliked_names_to_insert = [(name_id, user_id) for name_id in names_liked]

        disliked_query = "INSERT OR IGNORE INTO user_disliked (name_id, user_id) VALUES (?, ?);"

        try:
            await db.executemany(disliked_query, disliked_names_to_insert)
            await db.commit()
        except Error as e:
            raise HTTPException(status_code=400, detail="error: database error") from e


    return JSONResponse(content={"success": "all (dis)liked names added"}, status_code=200)
