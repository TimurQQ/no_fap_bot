from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from database import database
from src.handlers.daily_actions import checkRating
from src.handlers.daily_actions import sendCheckMessageToWinners
from src.handlers.daily_actions import clear_problematic_users_cache
from src.utils.s3_backup import backup_database_to_s3
from logger import noFapLogger

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

logging_trigger = CronTrigger(hour='21',minute='00')
winners_trigger = CronTrigger(hour='20',minute='00')
check_rating_trigger = IntervalTrigger(seconds = 60)
cache_clear_trigger = CronTrigger(hour='3',minute='00')  # Очистка кэша каждый день в 3:00
s3_backup_trigger = CronTrigger(hour='22',minute='00')  # Бэкап базы данных в S3 каждый день в 22:00

scheduler.add_job(noFapLogger.logDatabase, trigger=logging_trigger, args=(database.data,))
scheduler.add_job(sendCheckMessageToWinners, trigger=winners_trigger)
scheduler.add_job(checkRating, trigger=check_rating_trigger)
scheduler.add_job(clear_problematic_users_cache, trigger=cache_clear_trigger)
scheduler.add_job(backup_database_to_s3, trigger=s3_backup_trigger)
