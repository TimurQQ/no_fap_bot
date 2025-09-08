import os
from argparse import ArgumentParser
from datetime import datetime

from aiogram import types
from aiogram.utils import executor

from commands import commands
from config.config import ADMINS
from database import database
from dispatcher import bot, dp
from logger import noFapLogger
from sheduler import scheduler
from src import handlers as handlers
from src.keyboard import start_kb


@dp.message_handler(commands=[commands.HelpCommand])
async def show_help(message: types.Message):
    await message.reply(
        f"Hi!\nI am No Fap Bot [created by @timtim2379]!\nOptions:{commands.getAllCommands()}"
    )


@dp.message_handler(commands=[commands.StartCommand])
async def send_welcome(message: types.Message):
    chatId = message.chat.id
    if chatId not in database:
        chat = await bot.get_chat(chatId)
        username = chat.username
        database.addNewUser(chatId, username, datetime.now())

    await message.reply(
        f"Hi!\nI am No Fap Bot [created by @timtim2379]!\nOptions:{commands.getAllCommands()}"
    )

    await message.reply("Choose your last fap day:", reply_markup=start_kb)


async def send_logs(logsFilePath):
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


def parse_args():
    parser = ArgumentParser(prog=f"{__file__}")
    parser.add_argument("-l", "--logs_output", type=str)
    args = parser.parse_args()
    loggingParam = args.logs_output
    if loggingParam and loggingParam.lower() == "true":
        noFapLogger.set_console_logging(True)
    else:
        noFapLogger.set_console_logging(False)


async def on_startup(dp):
    """Callback функция, вызываемая при запуске бота."""
    scheduler.start()
    noFapLogger.info("Scheduler started")


def main():
    """Main entry point for the bot."""
    noFapLogger.info("🚀 Инициализация бота")
    noFapLogger.setLoggerSender(send_logs)
    noFapLogger.info("✅ logsSender установлен успешно")
    noFapLogger.info("🤖 Запуск бота")
    parse_args()
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


if __name__ == "__main__":
    main()
