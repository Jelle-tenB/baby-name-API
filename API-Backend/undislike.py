"""
Let the user remove a name from the disliked list.
The user must be logged in to remove a name from the disliked list.
The user must provide a list of name ID(s) to remove from the disliked list.
"""

# Standard library imports
from typing import List
from json import loads

# Third-party library imports
from fastapi import HTTPException, APIRouter, Depends, Cookie, Query, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local application imports
from imports import get_db, limiter, validate_token


undislike_router = APIRouter()


@undislike_router.delete("/undislike",
    responses={
        200:
            {"description": "successful response",
            "content": {
                "application/json": {
                    "example":
                        {"success": "deleted 5 items"}
        }}},
        400: {
            "description": "bad request - unsuccessful response",
            "content": {
                "application/json": {
                    "example":
                        {"error: database error"}
}}}})
@limiter.limit("10/minute")
async def undislike(
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    name_ids: List[int] = Query(..., examples={"name_ids": {"value": [1001, 1002]}}), # type: ignore
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None)
):

    """DELETE, request to remove a name from the disliked list."""

    if not session_token:
        raise HTTPException(status_code=401, detail="error: not logged in")

    # Reads the cookie.
    user_info = loads(session_token)
    user_id = user_info["id"]
    token = user_info["session_token"]
    await validate_token(token, user_id, db)

    try:
        placeholders = ', '.join(['?'] * len(name_ids))
        params = [user_id] + name_ids

        query = f"""
        DELETE FROM user_disliked
        WHERE user_id = ?
            AND name_id IN ({placeholders});
        """

        await db.execute(query, params)
        await db.commit()

        return JSONResponse(status_code=200, content={"success": f"deleted {len(name_ids)} items"})

    except Error as e:
        raise HTTPException(status_code=400, detail="error: database error") from e
