"""
Scheduler for periodic database cleanup tasks.
"""

# Standard Library
from datetime import datetime
from os import path, getenv

# Third-Party Libraries
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiosqlite import connect
from pytz import timezone
from dotenv import load_dotenv


scheduler = AsyncIOScheduler()
load_dotenv(dotenv_path=path.join(path.dirname(__file__), '..', 'scheduler_secrets.env'))

TOKEN_QUERY = getenv("TOKEN_QUERY")

FAILED_LOGIN_QUERY = getenv("FAILED_LOGIN_QUERY")

GROUP_LINKS_QUERY = getenv("GROUP_LINKS_QUERY")

LIKES_QUERY = getenv("LIKES_QUERY")

DISLIKES_QUERY = getenv("DISLIKES_QUERY")

UNUSED_LINKED_USER_QUERY = getenv("UNUSED_LINKED_USER_QUERY")

UNUSED_USER_QUERY = getenv("UNUSED_USER_QUERY")


def start_scheduler(db_path: str):
    """Starts the scheduler to run periodic cleanup tasks."""
    async def cleanup_database():
        print(f"[{datetime.now()}] running cleanup...")

        async with connect(db_path) as db:
            async with db.execute(TOKEN_QUERY):
                await db.commit()
                print("✅ session tokens cleaned up.")

            async with db.execute(FAILED_LOGIN_QUERY):
                await db.commit()
                print("✅ failed login attempts cleaned up.")

            async with db.execute(GROUP_LINKS_QUERY):
                await db.commit()
                print("✅ group links cleaned up.")

            async with db.execute(LIKES_QUERY):
                await db.commit()
                print("✅ user likes cleaned up.")

            async with db.execute(DISLIKES_QUERY):
                await db.commit()
                print("✅ user dislikes cleaned up.")

            async with db.execute(UNUSED_LINKED_USER_QUERY):
                await db.commit()
                print("✅ unused linked users cleaned up.")

            async with db.execute(UNUSED_USER_QUERY):
                await db.commit()
                print("✅ unused users cleaned up.")

        print("✅ cleanup complete.")

    scheduler.add_job(
        cleanup_database,
        trigger=CronTrigger(day_of_week="wed", hour=12, minute=0, timezone=timezone("Europe/Amsterdam")),
    )
    scheduler.start()
