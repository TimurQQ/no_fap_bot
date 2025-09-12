import os

from aiogram import types

from commands import commands
from database import database
from dispatcher import dp
from logger import noFapLogger
from sheduler import update_logging_schedule
from src.constants import LOGS_FOLDER
from src.utils.log_sender import send_logs


@dp.message_handler(is_admin=True, commands=["ban"])
async def ban_user(message: types.Message):
    args = message.get_args()
    if len(args) == 0:
        await message.answer(f"Command args passes incorrectly")
        return
    whom = args.split()[0].split("@")[-1]
    uid = database.getUserIDFromNick(whom)
    if uid is None:
        await message.answer(f"User with provided nickname doesn't exist")
        return
    database.update(uid, bannedFlag=True)
    await message.answer(f"User with nick @{whom} was banned by you :)")


@dp.message_handler(is_admin=True, commands=["unban"])
async def unban_user(message: types.Message):
    args = message.get_args()
    if len(args) == 0:
        await message.answer(f"Command args passes incorrectly")
        return
    whom = args.split()[0].split("@")[-1]
    uid = database.getUserIDFromNick(whom)
    if uid is None:
        await message.answer(f"User with provided nickname doesn't exist")
        return
    database.update(uid, bannedFlag=False)
    await message.answer(f"User with nick @{whom} was unbanned by you :)")


@dp.message_handler(is_admin=False, commands=["ban", "unban"])
async def no_admin_rights_handler(message: types.Message):
    await message.answer(f"You don't have admin rights to do /{message.get_command()}")


@dp.message_handler(commands=[commands.BlacklistCommand])
async def get_black_list(message: types.Message):
    blacklisted_users = database.getBlackList()

    if not blacklisted_users:
        await message.answer("BlackList is empty ✅")
        return

    # Формируем список без API вызовов - используем сохраненные usernames
    blacklist_lines = []
    for user in blacklisted_users:
        username = user["username"]
        uid = user["uid"]
        blacklist_lines.append(f"@{username} (ID: {uid}) is blocked")

    # Простое разбиение на части по 4000 символов
    full_text = f"BlackList ({len(blacklisted_users)} users):\n\n" + "\n".join(
        blacklist_lines
    )

    # Разбиваем текст на куски по 4000 символов
    chunk_size = 4000
    for i in range(0, len(full_text), chunk_size):
        chunk = full_text[i : i + chunk_size]
        if i == 0:
            await message.answer(chunk)
        else:
            await message.answer(f"BlackList (continued):\n{chunk}")


@dp.message_handler(is_admin=True, commands=["get_logs"])
async def send_logs_manually(message: types.Message):
    """Ручная отправка логов админам"""
    try:
        # Найдем последний файл логов
        log_files = [
            f
            for f in os.listdir(LOGS_FOLDER)
            if f.startswith("log.") and os.path.isfile(os.path.join(LOGS_FOLDER, f))
        ]

        if not log_files:
            await message.answer("❌ Нет файлов логов для отправки")
            return

        # Берем последний файл
        latest_log = sorted(log_files)[-1]
        log_path = os.path.join(LOGS_FOLDER, latest_log)

        await message.answer(f"📤 Отправляю лог файл: {latest_log}")

        # Отправляем лог
        await send_logs(log_path)

        await message.answer(
            f"✅ Лог файл {latest_log} успешно отправлен всем админам!"
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке логов: {e}")


@dp.message_handler(is_admin=False, commands=["get_logs"])
async def send_logs_no_admin(message: types.Message):
    await message.answer("❌ У вас нет прав администратора для выполнения /get_logs")


@dp.message_handler(is_admin=True, commands=["set_log_time"])
async def set_log_rotation_time(message: types.Message):
    """Устанавливает время ежедневной ротации и отправки логов"""
    args = message.get_args()

    if not args:
        current_time = noFapLogger.get_current_rotation_time()
        await message.answer(
            f"⏰ Текущее время ротации логов: {current_time} (МСК)\n\n"
            f"Использование: /set_log_time ЧЧ:ММ\n"
            f"Пример: /set_log_time 22:30\n\n"
            f"📋 Допустимые значения:\n"
            f"• Час: 00-23\n"
            f"• Минута: 00-59\n"
            f"🌍 Время указывается по московскому часовому поясу (МСК)"
        )
        return

    # Парсим время из аргументов (формат HH:MM)
    try:
        time_parts = args.strip().split(":")
        if len(time_parts) != 2:
            raise ValueError("Неверный формат")

        hour = int(time_parts[0])
        minute = int(time_parts[1])

        # Валидация
        if not (0 <= hour <= 23):
            await message.answer(f"❌ Час должен быть от 00 до 23, получен: {hour:02d}")
            return

        if not (0 <= minute <= 59):
            await message.answer(
                f"❌ Минута должна быть от 00 до 59, получена: {minute:02d}"
            )
            return

        # Обновляем время в конфигурации и планировщике
        logger_updated = noFapLogger.update_rotation_time(hour, minute)
        scheduler_updated = update_logging_schedule(hour, minute)

        if logger_updated and scheduler_updated:
            await message.answer(
                f"✅ Время ротации логов обновлено!\n\n"
                f"🕐 Новое время: {hour:02d}:{minute:02d} (МСК)\n"
                f"📤 Логи будут отправляться ежедневно в это время\n"
                f"⚡ Изменения применены немедленно (без перезапуска)"
            )
        elif logger_updated:
            await message.answer(
                f"⚠️ Время ротации частично обновлено\n\n"
                f"✅ Конфигурация обновлена: {hour:02d}:{minute:02d} (МСК)\n"
                f"❌ Ошибка обновления планировщика\n"
                f"🔄 Для полного применения требуется перезапуск бота"
            )
        else:
            await message.answer("❌ Ошибка при обновлении времени ротации логов")

    except ValueError:
        await message.answer(
            f"❌ Неверный формат времени!\n\n"
            f"Используйте формат: ЧЧ:ММ\n"
            f"Пример: /set_log_time 22:30\n"
            f"⏰ Время указывается по московскому часовому поясу (МСК)"
        )
    except Exception as e:
        await message.answer(f"❌ Неожиданная ошибка: {e}")


@dp.message_handler(is_admin=True, commands=["get_log_time"])
async def get_log_rotation_time(message: types.Message):
    """Показывает текущее время ротации логов"""
    try:
        current_time = noFapLogger.get_current_rotation_time()
        await message.answer(
            f"⏰ Текущее время ротации логов: {current_time} (МСК)\n\n"
            f"📤 Логи отправляются администраторам ежедневно в это время\n"
            f"🔧 Для изменения используйте: /set_log_time ЧЧ:ММ\n"
            f"🌍 Время указывается по московскому часовому поясу"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении времени ротации: {e}")


@dp.message_handler(is_admin=True, commands=["admin_help"])
async def admin_help(message: types.Message):
    """Показывает список всех админских команд"""
    help_text = (
        "🔧 **АДМИНСКИЕ КОМАНДЫ**\n\n"
        "👥 **Управление пользователями:**\n"
        "• `/ban @username` - заблокировать пользователя\n"
        "• `/unban @username` - разблокировать пользователя\n\n"
        "📋 **Логи и мониторинг:**\n"
        "• `/get_logs` - получить текущий файл логов\n"
        "• `/set_log_time ЧЧ:ММ` - установить время ежедневной отправки логов (МСК)\n"
        "• `/get_log_time` - показать текущее время отправки логов\n\n"
        "ℹ️ **Справка:**\n"
        "• `/admin_help` - показать эту справку\n\n"
        "🌍 Время указывается по московскому часовому поясу (МСК)\n"
        "⚠️ Эти команды доступны только администраторам"
    )

    await message.answer(help_text, parse_mode="Markdown")


@dp.message_handler(
    is_admin=False, commands=["set_log_time", "get_log_time", "admin_help"]
)
async def log_time_no_admin(message: types.Message):
    """Запрет доступа к командам управления временем ротации для не-админов"""
    command = message.get_command()
    await message.answer(f"❌ У вас нет прав администратора для выполнения /{command}")
