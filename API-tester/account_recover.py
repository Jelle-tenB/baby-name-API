"""
Account recovery endpoint for the API.
Which allows a user to reset their password using a recovery token.
"""

# Standard Library
from typing import Annotated
from os import getenv

# Third-Party Libraries
from fastapi import HTTPException, APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field as field
from aiosqlite import Connection, Error

# Local Application Imports
from imports import get_db, limiter, load_project_dotenv
from password import hash_pwd


account_recover_router = APIRouter()
load_project_dotenv()


class Item(BaseModel):
    username: Annotated[
        str, field(description="provide username")]
    recovery_token: Annotated[
        str, field(description="16 character recovery code")]
    new_password: Annotated[
        str, field(description="new password to replace the old one.")]


@account_recover_router.post("/account_recovery",)
@limiter.limit("10/minute")
async def recovery(
    item: Item,
    # Request might seem unused, but it is used by the limiter
    request: Request, # pylint: disable=unused-argument
    db: Connection = Depends(get_db)
):

    """POST request to reset a user's password, using a recovery token that the user has."""

    recovery_code = item.recovery_token.lower()
    username = item.username.lower()

    hashed_password = hash_pwd(item.new_password)

    find_code = getenv("FIND_CODE")

    try:
        async with db.execute(find_code, (username,)) as cursor:
            row = await cursor.fetchone()
            stored_token = row[0] if row else None
    except Error as e:
        raise HTTPException(status_code=500, detail="error: database error") from e


    if stored_token is None:
        raise HTTPException(status_code=404, detail="error: username not found")

    if stored_token == recovery_code:
        query = getenv("SET_CODE")

        try:
            await db.execute(query, (hashed_password, username))
            await db.commit()
        except Error as e:
            raise HTTPException(status_code=500, detail="error: failed to update password") from e

        return JSONResponse(status_code=200, content="success: password has been updated.")

    raise HTTPException(status_code=401, detail="error: recovery code does not match")
