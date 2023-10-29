from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import database
from src.handlers.daily_actions import checkRating
from logger import noFapLogger

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
scheduler.add_job(noFapLogger.logDatabase, "cron", args=(database.data,), day_of_week='mon-sun', hour=21, minute = 00)
scheduler.add_job(checkRating, "interval", seconds = 60)
