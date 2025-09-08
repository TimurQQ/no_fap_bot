from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from config.config import ADMINS

class IsAdminFilter(BoundFilter):
    key = "is_admin"

    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

    async def check(self, message: types.Message):
        # Если список админов пустой, никто не является админом
        if not ADMINS:
            return False
        return message.chat.id in ADMINS
