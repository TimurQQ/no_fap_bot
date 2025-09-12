from apscheduler.triggers.cron import CronTrigger

from logger import noFapLogger


def update_logging_schedule(hour: int, minute: int) -> bool:
    try:
        from sheduler import scheduler

        # Проверяем текущее состояние задачи
        job = scheduler.get_job("logging_job")
        if job:
            noFapLogger.info(f"📋 Текущий триггер задачи: {job.trigger}")
            noFapLogger.info(f"📋 Следующий запуск: {job.next_run_time}")

        new_trigger = CronTrigger(hour=hour, minute=minute)
        scheduler.modify_job("logging_job", trigger=new_trigger)

        # Проверяем обновленное состояние
        updated_job = scheduler.get_job("logging_job")
        if updated_job:
            noFapLogger.info(f"✅ Новый триггер: {updated_job.trigger}")
            noFapLogger.info(f"✅ Новый следующий запуск: {updated_job.next_run_time}")

        noFapLogger.info(
            f"⏰ Планировщик: время logDatabase обновлено на {hour:02d}:{minute:02d} (МСК)"
        )
        return True
    except Exception as e:
        noFapLogger.error(f"❌ Ошибка при обновлении времени планировщика: {e}")
        return False
