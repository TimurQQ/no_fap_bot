from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from database import database
from datetime import datetime

class BlackListMiddleware(BaseMiddleware):
    def __init__(self):
        super(BlackListMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if message.chat.id in database.getBlackList():
            userStat = database.getStatById(message.chat.id)
            await message.answer(
                "Your statistics: \n" +
                f"@{userStat.username} Stat: {datetime.now() - userStat.lastTimeFap}"
                , reply_markup=types.ReplyKeyboardRemove()
            )
            raise CancelHandler()
