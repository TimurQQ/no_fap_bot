from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types

from src.logger import noFapLogger

class LoggingMiddleware(BaseMiddleware):
    def __init__(self):
        super(LoggingMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        noFapLogger.info_message(message)
