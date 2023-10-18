from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.handlers.daily_actions import sendCheckMessageBroadcast
from src.handlers.daily_actions import checkRating
from src.handlers.daily_actions import makeBackup

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
scheduler.add_job(sendCheckMessageBroadcast, "cron", day_of_week='mon-sun', hour=21, minute = 00)
scheduler.add_job(makeBackup, "cron", day_of_week='mon-sun', hour=22, minute = 00)
scheduler.add_job(checkRating, "interval", seconds = 60)
