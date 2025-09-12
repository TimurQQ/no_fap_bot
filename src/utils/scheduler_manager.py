from apscheduler.triggers.cron import CronTrigger

from logger import noFapLogger


def update_logging_schedule(hour: int, minute: int) -> bool:
    try:
        from sheduler import scheduler

        new_trigger = CronTrigger(hour=hour, minute=minute)
        scheduler.modify_job("logging_job", trigger=new_trigger)
        noFapLogger.info(
            f"⏰ Планировщик: время logDatabase обновлено на {hour:02d}:{minute:02d} (МСК)"
        )
        return True
    except Exception as e:
        noFapLogger.error(f"❌ Ошибка при обновлении времени планировщика: {e}")
        return False
