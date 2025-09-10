import os
from datetime import datetime

from config.config import ADMINS
from dispatcher import bot
from logger import noFapLogger


async def send_logs(logsFilePath: str):
    noFapLogger.info(f"📤 Начинается отправка лога {logsFilePath} админам")

    # Проверяем, есть ли админы
    if not ADMINS:
        noFapLogger.error("❌ Список админов пустой! Лог не будет отправлен.")
        noFapLogger.error("❌ Проверьте переменную ADMINS в .env файле")
        return

    # Проверяем существование файла
    if not os.path.exists(logsFilePath):
        noFapLogger.error(f"❌ Файл лога не существует: {logsFilePath}")
        return

    # Проверяем размер файла
    try:
        file_size = os.path.getsize(logsFilePath)
        noFapLogger.info(f"📊 Размер файла лога: {file_size} байт")
    except Exception as e:
        noFapLogger.error(f"❌ Ошибка при получении размера файла: {e}")
        return

    noFapLogger.info(f"👥 Список админов: {list(ADMINS)}")

    success_count = 0
    total_admins = len(ADMINS)

    for admin in ADMINS:
        try:
            noFapLogger.info(f"📤 Отправка лога админу {admin}")
            await bot.send_document(
                admin,
                (
                    f"{logsFilePath}-{datetime.now().timestamp()}",
                    open(logsFilePath, "rb"),
                ),
            )
            noFapLogger.info(f"✅ Лог успешно отправлен админу {admin}")
            success_count += 1
        except Exception as e:
            noFapLogger.error(f"❌ Ошибка при отправке лога админу {admin}: {e}")
            noFapLogger.error(f"❌ Детали ошибки: {type(e).__name__}: {str(e)}")

    noFapLogger.info(
        f"📊 Результат отправки: {success_count}/{total_admins} админов получили лог"
    )
