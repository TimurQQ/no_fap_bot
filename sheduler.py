from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from database import database
from src.handlers.daily_actions import checkRating
from src.handlers.daily_actions import sendCheckMessageToWinners
from logger import noFapLogger

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

logging_trigger = CronTrigger(hour='21',minute='00')
winners_trigger = CronTrigger(hour='20',minute='00')
check_rating_trigger = IntervalTrigger(seconds = 60)

scheduler.add_job(noFapLogger.logDatabase, trigger=logging_trigger)
scheduler.add_job(sendCheckMessageToWinners, trigger=winners_trigger)
scheduler.add_job(checkRating, trigger=check_rating_trigger)
