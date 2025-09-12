from apscheduler.triggers.cron import CronTrigger

from logger import noFapLogger


def update_logging_schedule(hour: int, minute: int) -> bool:
    try:
        from database import database
        from logger import noFapLogger as logger
        from sheduler import scheduler

        if not scheduler.get_job("logging_job"):
            noFapLogger.error("❌ Задача logging_job не найдена!")
            return False

        scheduler.remove_job("logging_job")

        new_trigger = CronTrigger(hour=hour, minute=minute)
        scheduler.add_job(
            logger.logDatabase,
            trigger=new_trigger,
            args=(database.data,),
            id="logging_job",
        )

        noFapLogger.info(
            f"⏰ Планировщик: время logDatabase обновлено на {hour:02d}:{minute:02d} (МСК)"
        )
        return True
    except Exception as e:
        noFapLogger.error(f"❌ Ошибка при обновлении времени планировщика: {e}")
        return False
