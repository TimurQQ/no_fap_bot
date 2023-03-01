from aiogram import types
from aiogram.dispatcher.filters import Filter

admins = {464237994,}

class IsAdminFilter(Filter):
    key = "is_admin"

    async def check(self, message: types.Message):
        return message.from_user.id in admins

