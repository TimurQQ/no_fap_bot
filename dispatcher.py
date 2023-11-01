import logging
from aiogram import Bot, Dispatcher
from aiogram.bot.api import TelegramAPIServer
from config.config import BOT_TOKEN
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.filters.admin import IsAdminFilter
from src.middlewares.logging import LoggingMiddleware
from src.middlewares.black_list import BlackListMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)

local_server = TelegramAPIServer.from_base("http://localhost:8081")

bot = Bot(token=BOT_TOKEN, server=local_server)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.filters_factory.bind(IsAdminFilter)
dp.middleware.setup(LoggingMiddleware())
dp.middleware.setup(BlackListMiddleware())
