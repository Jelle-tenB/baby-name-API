"""
Running this file will start the FastAPI server.
The server will be available at http://127.0.0.1:5000
and the API documentation will be available at http://127.0.0.1:5000/docs
The server will automatically reload when changes are made to the code.

The Search Function takes the following optional parameters but at least 1 must be given:
- letter: The starting letter(s) of the name to search for
- gender: The given sex of the name to search for
- country: The country a name is used in to search for
- start: Optional parameter to search for names with given letter(s) SOMEWHERE in the name.
    If not given it defualts to the starting letter.

If a user is logged in, the search will filter out names already liked/disliked by the user.
"""

# Standard Library
from json import loads
from typing import Optional, List

# Third-Party Libraries
from fastapi import Depends, Query, HTTPException, Request, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from uvicorn import run
from aiosqlite import Connection, Error # pylint: disable=unused-argument

# Local Application Imports
from imports import (
    app, static_path, limiter,
    get_db, check_letter,  validate_token,
    SuccessResponse, ErrorResponse)
from login import login_router
from new_user import new_user_router
from user_liked import liked_router
from user_disliked import disliked_router
from protected_route import cookie_router
from likes_list import like_list_router
from dislike_list import dislike_list_router
from new_group import new_group_router
from group_liked import group_liked_router
from delete_group import delete_group_router
from similar import similar_router
from unlike import unlike_router
from undislike import undislike_router
from add_to_group import add_to_group_router
from account_recover import account_recover_router
from delete_user import delete_user_router
from compare_likes import compare_likes_router
from user_preferences import user_preferences_router
from logout import logout_router


# Router to add the API methods to /docs.
app.include_router(cookie_router)
app.include_router(like_list_router)
app.include_router(dislike_list_router)
app.include_router(group_liked_router)
app.include_router(similar_router)
app.include_router(compare_likes_router)
app.include_router(logout_router)
app.include_router(login_router)
app.include_router(new_user_router)
app.include_router(user_preferences_router)
app.include_router(liked_router)
app.include_router(disliked_router)
app.include_router(new_group_router)
app.include_router(add_to_group_router)
app.include_router(account_recover_router)
app.include_router(delete_group_router)
app.include_router(unlike_router)
app.include_router(undislike_router)
app.include_router(delete_user_router)

# Displays my own HTML file.
app.mount("/static", StaticFiles(directory=static_path), name='static')

@app.get("/")
async def read_index():
    """Currently empty page for possible API documentation"""

    return FileResponse(f"{static_path}/index.html")


@app.get("/search",
    response_model=SuccessResponse,
    responses={
        400:
            {"description": "bad request - unsuccessful response",
            "model": ErrorResponse},
        422:
            {"description": "validation error",
            "content": {
                "application/json": {
                    "example": {"error: 'character' in parameter 'X' is not a letter, please enter only letters"}
}}}})
@limiter.limit("10/minute")
async def search_first_letter(
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    letter: Optional[str] = Query(None, max_length=10, examples=["ab"]),
    gender: Optional[str] = Query(None, max_length=2, examples=["f"]),
    country: Optional[List[str]] = Query(None, examples=["Netherlands"]),
    start: Optional[int] = Query(None,
                                examples=["1 (default) for starting letter, 0 for anywhere"]),
    db: Connection = Depends(get_db),
    session_token: str = Cookie(None)
):

    """GET request to search for names with a given starting letter, given gender
    and/or given countries.
    All parameters are optional but atleast 1 MUST be given.
    Use start=0 if you want the given letter to be anywhere in the name.
    If not given it defualts to the starting letter."""

    # Changes the letter param to the correct format.
    query_letter = letter.title() if letter else None

    # Empty list to allow multiple countries to be given.
    query_country = []

    if country:  # Check if country is provided.
        for c in country:
            if c.lower() in ['usa', 'us']:
                query_country.append('USA')
            else:
                query_country.append(c.title())

    # Changes gender param to the correct format.
    query_gender = gender[:-1] + gender[-1].upper() if gender else None

    # Prevents users from giving no parameters.
    if not (query_letter or query_gender or query_country):
        raise HTTPException(status_code=400,
                            detail="error: at least one search parameter must be provided.")

    checklist = {}

    # Starting query to which more params are given.
    query = '''
        SELECT names.*, countries.country, population.pop
        FROM population
        JOIN names ON population.name_id = names.id
        JOIN countries ON population.country_id = countries.id
        WHERE 1=1
    '''

    # Empty parameters Tuple to add more params to.
    params = ()

    if start == 0: # Optional param to search for names with given letter(s) SOMEWHERE in the name.
        if query_letter:
            query += " AND names.name LIKE ?"
            params += ('%' + query_letter + '%',)
            checklist.update({"letter": query_letter})
    else: # Starting letter only.
        if query_letter:
            query += " AND names.name LIKE ?"
            params += (query_letter + '%',)
            checklist.update({"letter": query_letter})

    if query_gender:
        if '?' in query_gender:
            if query_gender == '?': # If asked for neutral gender it adds mostly female/male too.
                query += " AND (names.gender = '?' OR names.gender = '?M' OR names.gender = '?F')"
            else:
                query += " AND names.gender = ?"
                params += (query_gender,)
        else:
            query += " AND (names.gender = ? OR names.gender = ?)"
            params += (query_gender, '?' + query_gender)
        checklist.update({"gender": query_gender.strip('?')})

    if query_country:  # Check if the list is not empty
        if len(query_country) == 1:
            query += " AND countries.country = ?"
            params += (query_country[0],)  # Use the first element
            checklist.update({"country": query_country})
        else: # Allows multiple countries
            placeholders = ",".join("?" for _ in query_country)
            query += f" AND countries.country IN ({placeholders})"
            params += tuple(query_country)
            checklist.update({"country": query_country})

    # Check for letter and character validity
    check_letter(checklist)

    # Filter out names already liked/disliked by the user.
    if session_token:
        user_info = loads(session_token)
        user_id = user_info["id"]
        token = user_info["session_token"]

        await validate_token(token, user_id, db)

        query += '''
            AND names.id NOT IN (SELECT name_id FROM user_liked WHERE user_id = ?)
            AND names.id NOT IN (SELECT name_id FROM user_disliked WHERE user_id = ?)
            '''
        params += (user_id, user_id)

    try:
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

    except Error as exc:
        raise HTTPException(status_code=400, detail="error: database error") from exc

    grouped_data = {}

    for row in rows:
        name_id = row[0]
        if name_id not in grouped_data:
            grouped_data[name_id] = {
                "name": row[1], "gender": row[2], "country": [], "population": []}

        grouped_data[name_id]["country"].append(row[3])
        grouped_data[name_id]["population"].append(row[4])

    results = [{"id": id, **data} for id, data in grouped_data.items()]

    return JSONResponse(content=results, status_code=200)

if __name__ == "__main__":
    run("main:app", host="127.0.0.1", port=5000, reload=True)
