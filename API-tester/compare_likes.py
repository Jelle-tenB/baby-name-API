"""
Returns a list of names that your partner has liked, but you haven't seen yet.
Based on the user_id stored in the cookie,
And given group_code.
"""

# Standard Library Imports
from json import loads

# Third-Party Libraries
from fastapi import HTTPException, APIRouter, Depends, Cookie, Request, Query
from fastapi.responses import JSONResponse
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, SuccessResponse, ErrorResponse, limiter, validate_token


compare_likes_router = APIRouter()

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
    query = """
        WITH user_group AS (
            SELECT g.group_id
            FROM groups g
            JOIN link_users lu ON g.group_id = lu.group_id
            WHERE lu.user_id = ?
            AND g.group_code = ?
        ),
        partner_ids AS (
            SELECT user_id
            FROM link_users
            WHERE group_id = (SELECT group_id FROM user_group)
            AND user_id != ?
        ),
        partner_liked_names AS (
            SELECT DISTINCT ul.name_id
            FROM user_liked ul
            JOIN partner_ids p ON ul.user_id = p.user_id
        ),
        user_own_names AS (
            SELECT name_id FROM user_liked WHERE user_id = ?
            UNION
            SELECT name_id FROM user_disliked WHERE user_id = ?
        )
        SELECT 
            n.id,
            n.name,
            n.gender,
            GROUP_CONCAT(DISTINCT c.country) AS countries,
            GROUP_CONCAT(DISTINCT p.pop) AS populations
        FROM names n
        JOIN partner_liked_names pl ON n.id = pl.name_id
        LEFT JOIN population p ON n.id = p.name_id
        LEFT JOIN countries c ON p.country_id = c.id
        WHERE n.id NOT IN (SELECT name_id FROM user_own_names)
        GROUP BY n.id, n.name, n.gender;
    """

    # Check if the group code is valid.
    async with db.execute("SELECT 1 FROM groups WHERE group_code = ?;", (group_code,)) as cursor:
        if not await cursor.fetchone():
            raise HTTPException(status_code=400, detail="error: invalid group code")

    try:
        async with db.execute(query, (user_id, group_code, user_id, user_id, user_id)) as cursor:
            rows = await cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=400, detail=f"error: database error {e}") from e

    # Formats the search results into a list of dictonaries / JSON.
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
