from aiogram import types
from aiogram.utils import executor
from datetime import datetime
from dispatcher import dp, bot
from src import handlers as handlers
from database import database
from commands import commands
from src.keyboard import start_kb
from sheduler import scheduler

from logger import noFapLogger

from argparse import ArgumentParser

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
    parser = ArgumentParser(prog='f"{__file__}"')
    parser.add_argument('-l', '--logs_output', type=str)
    args = parser.parse_args()
    loggingParam = args.logs_output
    if loggingParam:
        if loggingParam.lower() == "true":
            noFapLogger.set_console_logging(True)
        else:
            noFapLogger.set_console_logging(False)
    else:
        noFapLogger.set_console_logging(True)

if __name__ == '__main__':
    noFapLogger.info("start bot")
    parse_args()
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
