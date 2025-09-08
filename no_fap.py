from argparse import ArgumentParser
from datetime import datetime

from aiogram import types
from aiogram.utils import executor

from commands import commands
from database import database
from dispatcher import bot, dp
from logger import noFapLogger
from sheduler import scheduler
from src import handlers as handlers
from src.keyboard import start_kb
from src.utils.log_sender import send_logs


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
