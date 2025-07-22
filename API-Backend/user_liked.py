"""
Lets add names to their list of liked names.
Requires the user to be logged in.
Takes a list of name_id(s) to be liked.
"""

# Standard library imports
from json import loads
from typing import Annotated, List

# Third-party library imports
from pydantic import BaseModel, Field as field
from fastapi import HTTPException, APIRouter, Depends, Cookie, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local application imports
from imports import get_db, limiter, validate_token


liked_router = APIRouter()


class Item(BaseModel):
    name_ids: Annotated[
        List[int],
        field(description="user liked names by the id of the name", min_items=1)] # type: ignore


@liked_router.post("/liked",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example":
                        {"success": "all liked names added"}
        }}},
        400:
            {"description": "bad request - unsuccessful response",
            "content": {
                "application/json": {
                    "example": {"error: couldnt find user"}
}}}})
@limiter.limit("10/minute")
async def user_liked(
    item: Item,
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None)
):

    """DEPRECATED: Both like and dislike can now go through "preferences".
    POST request to store the names a user has liked.
    Can handle batches of names."""

    if not session_token:
        raise HTTPException(status_code=401, detail="error: not logged in")

    # Reads the cookie.
    user_info = loads(session_token)
    user_id = user_info["id"]
    token = user_info["session_token"]
    await validate_token(token, user_id, db)

    if user_id:
        # First, get the list of name_ids the user has already liked
        placeholders = ",".join("?" for _ in item.name_ids)
        async with db.execute(
            f"SELECT name_id FROM user_disliked WHERE user_id = ? AND name_id IN ({placeholders})",
            (user_id, *item.name_ids)
        ) as cursor:
            liked_ids = {row[0] for row in await cursor.fetchall()}

        # Filter out liked name_ids from the ones the user is trying to dislike
        names_to_dislike = [name_id for name_id in item.name_ids if name_id not in liked_ids]

        if not names_to_dislike:
            return JSONResponse(content={"success":
                "No new liked names added (all already disliked)"},
                                status_code=200)

        names_to_insert = [(name_id, user_id) for name_id in names_to_dislike]

        query = "INSERT OR IGNORE INTO user_liked (name_id, user_id) VALUES (?, ?);"

        try:
            await db.executemany(query, names_to_insert)
            await db.commit()
            return JSONResponse(content={"success": "all liked names added"}, status_code=200)
        except Error as e:
            raise HTTPException(status_code=400, detail="error: database error") from e
