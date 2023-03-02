from aiogram import types
from aiogram.utils import executor
from datetime import datetime
from dispatcher import dp, bot
from database import database
from commands import commands
from src.keyboard import start_kb
from sheduler import scheduler

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

if __name__ == '__main__':
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
