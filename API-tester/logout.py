"""
Route to handle logout by clearing the session token cookie.
Requires a valid session token to be passed in the cookie.
"""

# Standard library imports
from json import loads

# Third-party library imports
from fastapi import HTTPException, Depends, Cookie, APIRouter, Request
from fastapi.responses import JSONResponse
from aiosqlite import Connection

# Local application imports
from imports import get_db, limiter, validate_token

logout_router = APIRouter()

@logout_router.get("/logout",
    responses={
        200: {
            "description": "successful response",
            "content": {
                "application/json": {
                    "example": {"success": "You have been logged out successfully."}
                }
            }
        },
        401: {
            "description": "bad request - unsuccessful response",
            "content": {
                "application/json": {
                    "example": {"error not logged in"}
}}}})
@limiter.limit("10/minute")
async def logout(
    request: Request,  # pylint: disable=unused-argument
    session_token: str = Cookie(None),
    db: Connection = Depends(get_db)
):
    """GET request to logout by clearing the session token cookie."""

    if not session_token:
        raise HTTPException(status_code=401, detail="error: not logged in")
    else:
        # Reads the cookie.
        user_info = loads(session_token)
        user_id = user_info["id"]
        token = user_info["session_token"]
        await validate_token(token, user_id, db)
    
    # Invalidate the session token in the database
    try:
        query = """
        UPDATE users
        SET session_token = NULL,
            session_expiration = NULL
        WHERE user_id = ?;
        """
        async with db.execute(query, (user_id,)):
            await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail="error: invalidating session token") from e

    # Clear the session token cookie
    response = JSONResponse(content={"success": "you have been logged out successfully."})
    response.set_cookie(key="session_token", value="", max_age=0, httponly=True, samesite="lax")

    return response

