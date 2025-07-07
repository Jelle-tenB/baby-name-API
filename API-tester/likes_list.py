"""
Returns a list of all the names the user has liked.
Based on the user_id stored in the cookie.
"""

# Standard Library Imports
from json import loads

# Third-Party Libraries
from fastapi import HTTPException, APIRouter, Depends, Cookie, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, SuccessResponse, ErrorResponse, limiter


like_list_router = APIRouter()

@like_list_router.get("/like_list",
    response_model=SuccessResponse,
    responses={
        400: {
            "description": "bad request - unsuccessful response",
            "model": ErrorResponse
}})
@limiter.limit("10/minute")
async def like_list(
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None)
    ):

    """GET request which returns a list of all the names the user has liked"""

    if not session_token:
        raise HTTPException(status_code=401, detail="not logged in")

    # Query to find ALL the names the given user has liked.
    query = """
    SELECT
        names.id,
        names.name,
        names.gender,
        countries.country,
        population.pop
    FROM user_liked
    JOIN names ON user_liked.name_id = names.id
    JOIN population ON names.id = population.name_id
    JOIN countries ON population.country_id = countries.id
    WHERE user_liked.user_id = ?;
    """

    # Reads the cookie.
    data = loads(session_token)
    user_id = data["id"]

    try:
        async with db.execute(query, (user_id,)) as cursor:
            rows = await cursor.fetchall()

        # Formats the search results into a list of dictonaries / JSON.
        grouped_data = {}

        for row in rows:
            name_id = row[0]
            if name_id not in grouped_data:
                grouped_data[name_id] = {"name": row[1],
                                        "gender": row[2],
                                        "country": [],
                                        "population": []}

            grouped_data[name_id]["country"].append(row[3])
            grouped_data[name_id]["population"].append(row[4])

        results = [{"id": id, **data} for id, data in grouped_data.items()]

        return JSONResponse(content=results, status_code=200)
    except Error as e:
        raise HTTPException(status_code=400, detail="error: database error") from e
    