import os
from datetime import datetime

from config.config import ADMINS
from dispatcher import bot
from logger import noFapLogger


async def send_logs(logsFilePath: str):
    """Отправляет лог файл всем админам"""
    if not ADMINS:
        noFapLogger.error(
            "❌ Список админов пустой! Проверьте переменную ADMINS в .env файле"
        )
        return

    if not os.path.exists(logsFilePath):
        noFapLogger.error(f"❌ Файл лога не существует: {logsFilePath}")
        return

    success_count = 0
    filename = f"{os.path.basename(logsFilePath)}-{datetime.now().timestamp()}"

    for admin in ADMINS:
        try:
            with open(logsFilePath, "rb") as log_file:
                await bot.send_document(admin, (filename, log_file))
            success_count += 1
        except Exception as e:
            noFapLogger.error(f"❌ Ошибка отправки лога админу {admin}: {e}")

    noFapLogger.info(f"📊 Лог отправлен {success_count}/{len(ADMINS)} админам")
