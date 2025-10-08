"""
Returns a list of similar names based on the given name_id.
"""

# Standard Library
from json import loads
from os import getenv

# Third-Party Libraries
from fastapi import HTTPException, APIRouter, Depends, Query, Request, Cookie
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, SuccessResponse, ErrorResponse, limiter, load_project_dotenv


similar_router = APIRouter()
load_project_dotenv()

@similar_router.get("/similar",
    response_model=SuccessResponse,
    responses={
        400:
            {"description": "bad request - unsuccessful response",
            "model": ErrorResponse,},
        401:
            {"description": "validation Error",
            "content": {
                "application/json": {
                    "example":
                        {"error: not a valid name_id"}
}}}})
@limiter.limit("10/minute")
async def similar(
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    name_id: int = Query(..., description="The ID of the name", examples=[1234]),
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None)
):

    """GET request to find similar names based on the given name_id"""


    if name_id is not None:
        try:
            # Query to find similar names of the given name id.
            # Returns all similar names excluding the given name.
            if not session_token:
                query = getenv("FIND_SIMILAR_NAMES")

                async with db.execute(query, (name_id, name_id,)) as cursor:
                    rows = await cursor.fetchall()

            # If the user is logged in, exclude names that the user has liked or disliked.
            else:
                query = getenv("LOGIN_FIND_SIMILAR_NAMES")

                # Reads the cookie.
                data = loads(session_token)
                user_id = data["id"]

                async with db.execute(query, (name_id, name_id, user_id, user_id,)) as cursor:
                    rows = await cursor.fetchall()


            # Formats the search result into a List of Dictionaries / JSON
            grouped_data = {}

            for row in rows:
                name_id = row[0]
                if name_id not in grouped_data:
                    grouped_data[name_id] = {"name": row[1],
                                             "gender": row[2],
                                             "country": [],
                                             "population": []}

                grouped_data[name_id]["country"] = row[3].split(', ')
                grouped_data[name_id]["population"] = [int(pop) for pop in row[4].split(', ')]


            results = [{"id": id, **data} for id, data in grouped_data.items()]

            return results
        except Error as e:
            raise HTTPException(status_code=400, detail="error: database error") from e
    else:
        raise HTTPException(status_code=400, detail="error: not a valid name_id")
