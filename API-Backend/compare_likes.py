"""
Returns a list of names that your partner has liked, but you haven't seen yet.
Based on the user_id stored in the cookie,
And given group_code.
"""

# Standard Library Imports
from json import loads
from os import getenv

# Third-Party Libraries
from fastapi import HTTPException, APIRouter, Depends, Cookie, Request, Query
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, SuccessResponse, ErrorResponse, limiter, validate_token, load_project_dotenv


compare_likes_router = APIRouter()
load_project_dotenv()

@compare_likes_router.get("/compare_likes",
    response_model=SuccessResponse,
    responses={
        400: {
            "description": "bad request - unsuccessful response",
            "model": ErrorResponse
}})
@limiter.limit("10/minute")
async def compare_likes(
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None),
    group_code: str = Query(None, max_length=6, min_length=6, examples=["abc123"])
    ):

    """GET request which returns a list of names that your partner has liked,
    but you haven't seen yet"""

    if not session_token:
        raise HTTPException(status_code=401, detail="not logged in")

    # Reads the cookie.
    data = loads(session_token)
    user_id = data["id"]
    token = data["session_token"]

    await validate_token(token, user_id, db)

    # Query to find the names your partner has liked, but you haven't seen yet.
    query = getenv("MATCHED_NAMES_QUERY")

    # Check if the group code is valid.
    async with db.execute("SELECT 1 FROM groups WHERE group_code = ?;", (group_code,)) as cursor:
        if not await cursor.fetchone():
            raise HTTPException(status_code=400, detail="error: invalid group code")

    try:
        async with db.execute(query, (user_id, group_code, user_id, user_id, user_id)) as cursor:
            rows = await cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=400, detail=f"error: database error {e}") from e

    # Formats the search results into a list of dictionaries / JSON.
    grouped_data = {}

    for row in rows:
        name_id = row[0]
        if name_id not in grouped_data:
            grouped_data[name_id] = {
                "name": row[1],
                "gender": row[2],
                "countries": row[3].split(",") if row[3] else [],
                "populations": [int(pop) for pop in row[4].split(",")] if row[4] else []
            }

    results = [{"id": id, **data} for id, data in grouped_data.items()]
    return JSONResponse(content=results, status_code=200)
