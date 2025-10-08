"""
File of functions used in (multiple) API endpoints.
To prevent circular imports.
"""

# Standard Library
from threading import local
from os import path, getenv
from datetime import datetime, timedelta
from typing import List
from secrets import token_hex
from contextlib import asynccontextmanager

# Third-Party Libraries
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, RootModel
from slowapi import Limiter, _rate_limit_exceeded_handler as rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from aiosqlite import connect, Connection, IntegrityError
from dotenv import load_dotenv

# Local Application Imports
from scheduler import start_scheduler


# Get the base directory of the current file (your app's directory)
basedir = path.abspath(path.dirname(__file__))
# Construct the full database path
db_path = path.join(basedir, 'static', 'names.db')
static_path = path.join(basedir, 'static')

# Load environment variables from the .env file
def load_project_dotenv():
    """Load environment variables secrets."""
    dotenv_path = path.join(path.dirname(__file__), '..', 'secrets.env')
    load_dotenv(dotenv_path=dotenv_path)

load_project_dotenv()


def load_main_dotenv():
    """Load environment variables secrets."""
    dotenv_path = path.join(path.dirname(__file__), '..', 'main_secrets.env')
    load_dotenv(dotenv_path=dotenv_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to start the scheduler when the app starts."""
    start_scheduler(db_path)  # Start scheduler when app starts
    yield


# Slowapi rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=lifespan, title="Pick-A-Name API",
                description="API for the Pick-A-Name application")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler) # type: ignore

maxage = int(timedelta(hours=24).total_seconds())

# Allows acces from other programs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://babynamegenerator.roads-technology.nl",
                   "https://apibabynamegenerator.roads-technology.nl",
                   "https://babynamegenerator.roads-technology.nl/pages/test.html",
                   "http://127.0.0.1:5501",
                   "https://babynamegenerator.roads-technology.nl/pages/index.html",
                   "http://127.0.0.1:5000",
                   "http://127.0.0.1:5500",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=maxage)

thread_local_storage = local()


class NameData(BaseModel):
    id: int = Field(..., example=18) # type: ignore
    name: str = Field(..., example="Aaliyah") # type: ignore
    gender: str = Field(..., example="?F") # type: ignore
    country: List[str] = Field(..., examples=["USA"])
    population: List[int] = Field(..., examples=[-8])


class SuccessResponse(RootModel):
    root: List[NameData]


class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["error: database error"])


# @asynccontextmanager
async def get_db():
    """Asynchronous context manager to get a database connection."""
    db = await connect(db_path)
    try:
        yield db
    finally:
        await db.close()


def check_letter(check):
    """Character checks to ensure only letters."""

    for item_key, item_value in check.items():
        if item_key == "country":
            for item in item_value:
                for character in item:
                    if character == "_":
                        pass
                    elif not character.isalpha():
                        raise HTTPException(status_code=422,
                            detail=f"""error: '{character}' in parameter '{item_key}' is not a letter,
                            please enter only letters""")
        else:
            for character in item_value:
                if item_key == 'gender' and character not in ["F", "?F", "M", "?M", "?"]:
                    raise HTTPException(status_code=422,
                            detail=f"'{item_key}' needs to be F, ?F, M, ?M or ?")
                if not character.isalpha():
                    raise HTTPException(status_code=422,
                        detail=f"""error: '{character}' in parameter '{item_key}' is not a letter,
                        please enter only letters""")


def timelater():
    """24 hours later, for automatic session expiration."""

    time = datetime.now() + timedelta(hours=24)
    time_later = time.strftime("%Y-%m-%d %H:%M:%S")
    return time_later


async def save_session_token(user_id: int, db: Connection = Depends(get_db)):
    """Save new session token in the DB"""

    # Check if the cookie is older than 1 hour, if so generate a new one.
    find_token_query = getenv("FIND_SESSION_TOKEN")
    try:
        async with db.execute(find_token_query, (user_id,)) as cursor:
            token_row = await cursor.fetchone()
            if token_row is None:
                raise HTTPException(status_code=401, detail="error: invalid session")
    except IntegrityError as e:
        raise HTTPException(status_code=401, detail="error: invalid session") from e

    # If there is a token, check if it's still valid for more than 23 hours
    if token_row[0] is not None:
        expiration_date = datetime.strptime(str(token_row[0]), "%Y-%m-%d %H:%M:%S")

        if expiration_date > datetime.now() + timedelta(hours=23):
            return token_row[2]

    # Otherwise, create a new token
    query = getenv("SAVE_SESSION_TOKEN")

    session_token = token_hex(20)
    session_expiration = timelater()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        async with db.execute(query, (session_token, session_expiration, now, user_id)):
            await db.commit()
        return session_token
    except IntegrityError as e:
        raise HTTPException(status_code=500, detail="error: database error") from e


async def set_recovery_token():
    """Generates an 8 character recovery token."""
    recovery_token = token_hex(8)
    return recovery_token

async def validate_token(session_token, user_id, db: Connection):
    """Checks the session token in the cookie against the token in the database"""

    # Query to find the user's current session token.
    query = getenv("FIND_SESSION_TOKEN")

    try:
        async with db.execute(query, (user_id,)) as cursor:
            row =  await cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=401, detail="error: invalid session")

            expiration_date = datetime.strptime(str(row[0]), "%Y-%m-%d %H:%M:%S")

            if expiration_date > datetime.now() and row[2] == session_token:
                return {"username": row[1], "user_id": user_id}

            raise HTTPException(status_code=401, detail="error: expired session")
    except IntegrityError as e:
        raise HTTPException(status_code=401, detail="error: invalid session") from e
