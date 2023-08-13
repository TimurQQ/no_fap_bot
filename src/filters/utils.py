# from aiogram import Bot
from dispatcher import bot
from database import database

async def check_username(chat_id):
    chat = await bot.get_chat(chat_id)
    old_nick = database.get
    new_nick = chat.username
    if chat.username is not None:
        database.update(newNickName=chat.username)
        return True
    return False