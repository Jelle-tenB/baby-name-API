"""
Scheduler for periodic database cleanup tasks.
"""

# Standard Library
from datetime import datetime

# Third-Party Libraries
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiosqlite import connect
from pytz import timezone


scheduler = AsyncIOScheduler()

token_query = """
    UPDATE users
    SET session_token = NULL,
        session_expiration = NULL
    WHERE session_expiration IS NOT NULL
    AND session_expiration < CURRENT_TIMESTAMP;
    """

failed_login_query = """
    DELETE FROM failed_logins
    WHERE last_attempt < datetime('now', '-7 days');
    """

group_links_query = """
    DELETE FROM link_users
    WHERE user_id NOT IN (SELECT user_id FROM users)
        OR group_id NOT IN (SELECT group_id FROM groups);
    """

likes_query = """
    DELETE FROM user_liked
    WHERE user_id NOT IN (SELECT user_id FROM users)
        OR name_id NOT IN (SELECT id FROM names);
    """

dislikes_query = """
    DELETE FROM user_disliked
    WHERE user_id NOT IN (SELECT user_id FROM users)
        OR name_id NOT IN (SELECT id FROM names);
    """

unused_linked_user_query = """
    DELETE FROM users
    WHERE user_id NOT IN (SELECT user_id FROM link_users)
        AND last_login < datetime('now', '-3 months');
    """

unused_user_query = """
    DELETE FROM users
    WHERE last_login < datetime('now', '-1 year');
    """


def start_scheduler(db_path: str):
    """Starts the scheduler to run periodic cleanup tasks."""
    async def cleanup_database():
        print(f"[{datetime.now()}] running cleanup...")

        async with connect(db_path) as db:
            async with db.execute(token_query):
                await db.commit()
                print("✅ session tokens cleaned up.")

            async with db.execute(failed_login_query):
                await db.commit()
                print("✅ failed login attempts cleaned up.")

            async with db.execute(group_links_query):
                await db.commit()
                print("✅ group links cleaned up.")

            async with db.execute(likes_query):
                await db.commit()
                print("✅ user likes cleaned up.")

            async with db.execute(dislikes_query):
                await db.commit()
                print("✅ user dislikes cleaned up.")

            async with db.execute(unused_linked_user_query):
                await db.commit()
                print("✅ unused linked users cleaned up.")

            async with db.execute(unused_user_query):
                await db.commit()
                print("✅ unused users cleaned up.")

        print("✅ cleanup complete.")

    scheduler.add_job(
        cleanup_database,
        trigger=CronTrigger(day_of_week="wed", hour=12, minute=0, timezone=timezone("Europe/Amsterdam")),
    )
    scheduler.start()
